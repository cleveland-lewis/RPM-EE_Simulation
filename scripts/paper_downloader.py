#!/usr/bin/env python3
"""
Paper Download Automation Tool
Searches for and downloads papers from open access sources
"""

import json
import os
import time
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import re

# Try to import optional dependencies
try:
    from scholarly import scholarly
    HAS_SCHOLARLY = True
except ImportError:
    HAS_SCHOLARLY = False
    print("Warning: scholarly not installed. Install with: pip install scholarly")

try:
    from Bio import Entrez
    HAS_BIOPYTHON = True
except ImportError:
    HAS_BIOPYTHON = False
    print("Warning: biopython not installed. Install with: pip install biopython")


@dataclass
class Paper:
    """Paper metadata"""
    title: str
    authors: List[str]
    year: int
    journal: str
    doi: Optional[str] = None
    pmid: Optional[str] = None
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    status: str = "pending"  # pending, downloaded, failed, not_found
    local_path: Optional[str] = None
    notes: str = ""
    priority: str = "medium"  # high, medium, low


class PaperDownloader:
    """Automated paper downloader using multiple sources"""
    
    def __init__(self, output_dir: str = "papers", cache_file: str = "paper_cache.json"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.cache_file = Path(cache_file)
        self.cache: Dict[str, Paper] = {}
        self.load_cache()
        
        # Email for Entrez (required by NCBI)
        self.email = "your.email@example.com"  # UPDATE THIS
        if HAS_BIOPYTHON:
            Entrez.email = self.email
    
    def load_cache(self):
        """Load cached paper metadata"""
        if self.cache_file.exists():
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
                self.cache = {k: Paper(**v) for k, v in data.items()}
            print(f"Loaded {len(self.cache)} papers from cache")
    
    def save_cache(self):
        """Save paper metadata to cache"""
        data = {k: asdict(v) for k, v in self.cache.items()}
        with open(self.cache_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Saved {len(self.cache)} papers to cache")
    
    def add_paper(self, paper: Paper) -> str:
        """Add paper to cache and return key"""
        key = self._generate_key(paper)
        self.cache[key] = paper
        return key
    
    def _generate_key(self, paper: Paper) -> str:
        """Generate unique key for paper"""
        if paper.doi:
            return f"doi:{paper.doi}"
        elif paper.pmid:
            return f"pmid:{paper.pmid}"
        else:
            # Use first author + year + title prefix
            author = paper.authors[0].split()[-1] if paper.authors else "Unknown"
            title_prefix = paper.title[:30].replace(" ", "_")
            return f"{author}_{paper.year}_{title_prefix}"
    
    def search_pubmed_central(self, query: str, max_results: int = 10) -> List[Paper]:
        """Search PubMed Central for open access papers"""
        if not HAS_BIOPYTHON:
            print("Biopython not available. Skipping PubMed search.")
            return []
        
        papers = []
        try:
            print(f"Searching PubMed Central: {query}")
            handle = Entrez.esearch(db="pmc", term=query, retmax=max_results)
            record = Entrez.read(handle)
            handle.close()
            
            id_list = record["IdList"]
            print(f"Found {len(id_list)} results")
            
            if id_list:
                handle = Entrez.efetch(db="pmc", id=id_list, rettype="xml")
                records = Entrez.read(handle)
                handle.close()
                
                for rec in records:
                    paper = self._parse_pmc_record(rec)
                    if paper:
                        papers.append(paper)
                        
        except Exception as e:
            print(f"PubMed Central search error: {e}")
        
        return papers
    
    def _parse_pmc_record(self, record) -> Optional[Paper]:
        """Parse PubMed Central record"""
        try:
            # This is simplified - actual PMC XML parsing is complex
            title = record.get('MedlineCitation', {}).get('Article', {}).get('ArticleTitle', 'Unknown')
            year = record.get('MedlineCitation', {}).get('Article', {}).get('Journal', {}).get('JournalIssue', {}).get('PubDate', {}).get('Year', '0')
            
            authors = []
            author_list = record.get('MedlineCitation', {}).get('Article', {}).get('AuthorList', [])
            for author in author_list:
                if 'LastName' in author:
                    authors.append(f"{author.get('ForeName', '')} {author['LastName']}")
            
            journal = record.get('MedlineCitation', {}).get('Article', {}).get('Journal', {}).get('Title', 'Unknown')
            
            pmid = record.get('MedlineCitation', {}).get('PMID', {}).get('PMID', None)
            
            return Paper(
                title=title,
                authors=authors,
                year=int(year) if year.isdigit() else 0,
                journal=journal,
                pmid=str(pmid) if pmid else None
            )
        except Exception as e:
            print(f"Error parsing PMC record: {e}")
            return None
    
    def search_by_doi(self, doi: str) -> Optional[Paper]:
        """Search for paper by DOI"""
        print(f"Searching by DOI: {doi}")
        
        # Try Unpaywall API (free, legal access to open access papers)
        try:
            url = f"https://api.unpaywall.org/v2/{doi}?email={self.email}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                paper = Paper(
                    title=data.get('title', 'Unknown'),
                    authors=[a.get('family', '') for a in data.get('z_authors', [])],
                    year=data.get('year', 0),
                    journal=data.get('journal_name', 'Unknown'),
                    doi=doi,
                    url=data.get('doi_url'),
                )
                
                # Check for open access PDF
                if data.get('is_oa'):
                    best_oa = data.get('best_oa_location', {})
                    paper.pdf_url = best_oa.get('url_for_pdf')
                    paper.status = "found"
                    print(f"✓ Found open access PDF")
                else:
                    paper.status = "not_open_access"
                    print(f"⚠ Paper found but not open access")
                
                return paper
                
        except requests.exceptions.RequestException as e:
            print(f"Error searching Unpaywall: {e}")
        
        return None
    
    def download_pdf(self, paper: Paper, filename: Optional[str] = None) -> bool:
        """Download PDF for paper"""
        if not paper.pdf_url:
            print(f"No PDF URL available for: {paper.title}")
            return False
        
        if not filename:
            # Generate safe filename
            safe_title = re.sub(r'[^\w\s-]', '', paper.title[:50])
            safe_title = re.sub(r'[-\s]+', '_', safe_title)
            author = paper.authors[0].split()[-1] if paper.authors else "Unknown"
            filename = f"{author}_{paper.year}_{safe_title}.pdf"
        
        output_path = self.output_dir / filename
        
        try:
            print(f"Downloading: {paper.title}")
            response = requests.get(paper.pdf_url, timeout=30, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            paper.local_path = str(output_path)
            paper.status = "downloaded"
            print(f"✓ Downloaded to: {output_path}")
            return True
            
        except Exception as e:
            print(f"✗ Download failed: {e}")
            paper.status = "download_failed"
            return False
    
    def generate_author_request_email(self, paper: Paper) -> str:
        """Generate email template for requesting paper from authors"""
        if not paper.authors:
            return "No authors available"
        
        first_author = paper.authors[0]
        
        email_template = f"""
Subject: Request for Full Text: {paper.title}

Dear Dr. {first_author.split()[-1]},

I am a researcher working on computational models of clinical populations, 
and I am conducting a systematic review of parameters for simulation models.

I would like to request access to the full text of your paper:

{paper.title}
{paper.journal}, {paper.year}
{f"DOI: {paper.doi}" if paper.doi else ""}

Your work is cited in our parameter validation documentation, and I need to 
extract specific quantitative values for our evidence table.

Would you be able to share a PDF copy of this paper?

Thank you for your time and consideration.

Best regards,
[Your name]
[Your affiliation]
[Your email]
"""
        return email_template
    
    def batch_download(self, papers: List[Paper], delay: float = 2.0) -> Dict[str, int]:
        """Download multiple papers with rate limiting"""
        stats = {"downloaded": 0, "failed": 0, "skipped": 0}
        
        for i, paper in enumerate(papers, 1):
            print(f"\n[{i}/{len(papers)}] Processing: {paper.title[:60]}...")
            
            # Skip if already downloaded
            if paper.status == "downloaded" and paper.local_path:
                if Path(paper.local_path).exists():
                    print("Already downloaded, skipping")
                    stats["skipped"] += 1
                    continue
            
            # Try to download
            if self.download_pdf(paper):
                stats["downloaded"] += 1
            else:
                stats["failed"] += 1
            
            # Rate limiting
            if i < len(papers):
                time.sleep(delay)
        
        return stats
    
    def report_status(self):
        """Print download status report"""
        print("\n" + "=" * 70)
        print("DOWNLOAD STATUS REPORT")
        print("=" * 70)
        
        by_status = {}
        by_priority = {}
        
        for paper in self.cache.values():
            by_status[paper.status] = by_status.get(paper.status, 0) + 1
            by_priority[paper.priority] = by_priority.get(paper.priority, 0) + 1
        
        print("\nBy Status:")
        for status, count in sorted(by_status.items()):
            print(f"  {status:20s}: {count}")
        
        print("\nBy Priority:")
        for priority, count in sorted(by_priority.items()):
            print(f"  {priority:20s}: {count}")
        
        print(f"\nTotal papers: {len(self.cache)}")
        print("=" * 70)


def load_papers_from_references(ref_file: str = "docs/references.txt") -> List[Paper]:
    """Load papers from reference file"""
    papers = []
    
    # This is a template - you'll need to parse your specific reference format
    # For now, creating the priority papers manually
    
    priority_papers = [
        {
            "title": "Reaction time variability in ADHD: A meta-analytic review of 319 studies",
            "authors": ["Kofler, M. J.", "Rapport, M. D.", "et al."],
            "year": 2013,
            "journal": "Clinical Psychology Review",
            "doi": "10.1016/j.cpr.2013.06.001",
            "priority": "high",
            "notes": "ADHD RT variability meta-analysis - 319 studies"
        },
        {
            "title": "Depression and cortisol responses to psychological stress: A meta-analysis",
            "authors": ["Burke, H. M.", "Davis, M. C.", "et al."],
            "year": 2005,
            "journal": "Psychoneuroendocrinology",
            "doi": "10.1016/j.psyneuen.2005.02.010",
            "priority": "high",
            "notes": "MDD cortisol meta-analysis - 361 studies"
        },
        {
            "title": "Moderators of working memory deficits in children with ADHD",
            "authors": ["Kasper, L. J.", "Alderson, R. M.", "Hudec, K. L."],
            "year": 2012,
            "journal": "Clinical Psychology Review",
            "doi": "10.1016/j.cpr.2012.07.001",
            "priority": "high",
            "notes": "ADHD WM meta-analysis"
        },
        {
            "title": "Elevated cortisol during play is associated with age and social engagement in children with autism",
            "authors": ["Corbett, B. A.", "Mendoza, S.", "et al."],
            "year": 2009,
            "journal": "Molecular Autism",
            "doi": "10.1186/2040-2392-1-13",
            "priority": "high",
            "notes": "ASD cortisol measurements"
        },
        {
            "title": "Evaluating vigilance deficits in ADHD: A meta-analysis of CPT performance",
            "authors": ["Huang-Pollock, C. L.", "Karalunas, S. L.", "et al."],
            "year": 2012,
            "journal": "Journal of Abnormal Psychology",
            "doi": "10.1037/a0027205",
            "priority": "high",
            "notes": "ADHD vigilance meta-analysis"
        },
        {
            "title": "The Positive and Negative Affect Schedule (PANAS): Construct validity",
            "authors": ["Crawford, J. R.", "Henry, J. D."],
            "year": 2004,
            "journal": "British Journal of Clinical Psychology",
            "doi": "10.1348/0144665031752934",
            "priority": "medium",
            "notes": "PANAS norms for affect parameters"
        },
        {
            "title": "Is low positive emotionality a specific risk factor for depression",
            "authors": ["Khazanov, G. K.", "Ruscio, A. M."],
            "year": 2016,
            "journal": "Psychological Bulletin",
            "doi": "10.1037/bul0000059",
            "priority": "high",
            "notes": "Anhedonia meta-analysis for MDD"
        },
    ]
    
    for p in priority_papers:
        papers.append(Paper(**p))
    
    return papers


def main():
    """Main download script"""
    print("Paper Download Automation Tool")
    print("=" * 70)
    
    # Initialize downloader
    downloader = PaperDownloader(
        output_dir="papers",
        cache_file="paper_cache.json"
    )
    
    # Load priority papers
    print("\nLoading priority papers...")
    papers = load_papers_from_references()
    print(f"Loaded {len(papers)} papers")
    
    # Add to cache
    for paper in papers:
        downloader.add_paper(paper)
    
    # Search and download
    print("\n" + "=" * 70)
    print("SEARCHING FOR PAPERS")
    print("=" * 70)
    
    for paper in papers:
        if paper.doi and paper.status == "pending":
            found = downloader.search_by_doi(paper.doi)
            if found:
                # Update paper with found info
                paper.pdf_url = found.pdf_url
                paper.url = found.url
                paper.status = found.status
                
                # Try to download if open access
                if paper.pdf_url:
                    downloader.download_pdf(paper)
            
            time.sleep(1)  # Rate limiting
    
    # Save cache
    downloader.save_cache()
    
    # Report
    downloader.report_status()
    
    # Generate author request emails for non-OA papers
    print("\n" + "=" * 70)
    print("AUTHOR REQUEST EMAILS")
    print("=" * 70)
    
    need_request = [p for p in downloader.cache.values() 
                    if p.status in ["not_open_access", "failed", "not_found"]]
    
    if need_request:
        print(f"\nFound {len(need_request)} papers that need author requests")
        print("\nSaving email templates to: author_requests/")
        
        request_dir = Path("author_requests")
        request_dir.mkdir(exist_ok=True)
        
        for i, paper in enumerate(need_request, 1):
            email_text = downloader.generate_author_request_email(paper)
            
            # Safe filename
            author = paper.authors[0].split()[-1] if paper.authors else f"paper{i}"
            filename = f"{i:02d}_{author}_{paper.year}.txt"
            
            with open(request_dir / filename, 'w') as f:
                f.write(email_text)
        
        print(f"✓ Saved {len(need_request)} email templates")
    
    print("\n" + "=" * 70)
    print("DOWNLOAD COMPLETE")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Check papers/ directory for downloaded PDFs")
    print("2. Review author_requests/ for papers to request")
    print("3. Run extraction script on downloaded papers")


if __name__ == "__main__":
    main()
