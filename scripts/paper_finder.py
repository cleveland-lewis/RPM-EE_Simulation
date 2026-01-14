#!/usr/bin/env python3
"""
Simple Paper Finder - No external dependencies
Uses DOI.org and Unpaywall to find open access papers
"""

import json
import os
import urllib.request
import urllib.error
import time
from pathlib import Path
from typing import Dict, List, Optional

# Priority papers to download
PRIORITY_PAPERS = [
    {
        "id": "kofler2013",
        "title": "Reaction time variability in ADHD: A meta-analytic review of 319 studies",
        "authors": ["Kofler M.J.", "Rapport M.D."],
        "year": 2013,
        "journal": "Clinical Psychology Review",
        "doi": "10.1016/j.cpr.2013.06.001",
        "priority": "HIGH",
        "parameter": "adhd_rt_variability"
    },
    {
        "id": "burke2005",
        "title": "Depression and cortisol responses to psychological stress: A meta-analysis",
        "authors": ["Burke H.M.", "Davis M.C."],
        "year": 2005,
        "journal": "Psychoneuroendocrinology",
        "doi": "10.1016/j.psyneuen.2005.02.010",
        "priority": "HIGH",
        "parameter": "mdd_stress_baseline"
    },
    {
        "id": "kasper2012",
        "title": "Moderators of working memory deficits in children with ADHD",
        "authors": ["Kasper L.J.", "Alderson R.M.", "Hudec K.L."],
        "year": 2012,
        "journal": "Clinical Psychology Review",
        "doi": "10.1016/j.cpr.2012.07.001",
        "priority": "HIGH",
        "parameter": "adhd_wm_capacity"
    },
    {
        "id": "corbett2009",
        "title": "Elevated cortisol during play in children with autism",
        "authors": ["Corbett B.A.", "Mendoza S."],
        "year": 2009,
        "journal": "Molecular Autism",
        "doi": "10.1186/2040-2392-1-13",
        "priority": "HIGH",
        "parameter": "asd_stress_baseline"
    },
    {
        "id": "huang-pollock2012",
        "title": "Evaluating vigilance deficits in ADHD",
        "authors": ["Huang-Pollock C.L.", "Karalunas S.L."],
        "year": 2012,
        "journal": "Journal of Abnormal Psychology",
        "doi": "10.1037/a0027205",
        "priority": "HIGH",
        "parameter": "adhd_attention_stability"
    },
    {
        "id": "crawford2004",
        "title": "The PANAS: Construct validity",
        "authors": ["Crawford J.R.", "Henry J.D."],
        "year": 2004,
        "journal": "British Journal of Clinical Psychology",
        "doi": "10.1348/0144665031752934",
        "priority": "MEDIUM",
        "parameter": "affect_parameters"
    },
]


def check_unpaywall(doi: str, email: str = "research@example.com") -> Optional[Dict]:
    """
    Check Unpaywall API for open access version
    Unpaywall is legal and free - it aggregates OA sources
    """
    url = f"https://api.unpaywall.org/v2/{doi}?email={email}"
    
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'RPM-EE-Paper-Downloader/1.0')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            
            if data.get('is_oa'):
                best_oa = data.get('best_oa_location', {})
                return {
                    'is_oa': True,
                    'pdf_url': best_oa.get('url_for_pdf'),
                    'landing_page': best_oa.get('url'),
                    'version': best_oa.get('version'),
                    'host_type': best_oa.get('host_type'),
                    'license': best_oa.get('license')
                }
            else:
                return {'is_oa': False}
                
    except urllib.error.URLError as e:
        print(f"  Error checking Unpaywall: {e}")
        return None
    except Exception as e:
        print(f"  Unexpected error: {e}")
        return None


def download_pdf(url: str, output_path: Path) -> bool:
    """Download PDF from URL"""
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (compatible; RPM-EE-Downloader/1.0)')
        
        print(f"  Downloading from: {url}")
        
        with urllib.request.urlopen(req, timeout=30) as response:
            with open(output_path, 'wb') as f:
                f.write(response.read())
        
        # Verify it's a PDF
        if output_path.stat().st_size < 1000:
            print(f"  ⚠ Downloaded file is suspiciously small ({output_path.stat().st_size} bytes)")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ✗ Download failed: {e}")
        return False


def generate_doi_url(doi: str) -> str:
    """Generate DOI resolver URL"""
    return f"https://doi.org/{doi}"


def main():
    print("=" * 70)
    print("PAPER FINDER - Phase 2 Literature Extraction")
    print("=" * 70)
    print("\nThis script will:")
    print("1. Check Unpaywall for open access versions")
    print("2. Download available PDFs")
    print("3. Generate links for manual download")
    print("4. Create author request templates")
    print("\n" + "=" * 70)
    
    # Setup directories
    papers_dir = Path("papers")
    papers_dir.mkdir(exist_ok=True)
    
    requests_dir = Path("author_requests")
    requests_dir.mkdir(exist_ok=True)
    
    # Results tracking
    results = {
        "downloaded": [],
        "open_access_found": [],
        "not_open_access": [],
        "failed": []
    }
    
    # Process each paper
    for i, paper in enumerate(PRIORITY_PAPERS, 1):
        print(f"\n[{i}/{len(PRIORITY_PAPERS)}] {paper['id']}")
        print(f"  Title: {paper['title'][:60]}...")
        print(f"  DOI: {paper['doi']}")
        print(f"  Priority: {paper['priority']}")
        
        # Check if already downloaded
        filename = f"{paper['id']}_{paper['year']}.pdf"
        output_path = papers_dir / filename
        
        if output_path.exists():
            print(f"  ✓ Already downloaded: {output_path}")
            results["downloaded"].append(paper)
            continue
        
        # Check Unpaywall
        print(f"  Checking Unpaywall...")
        oa_info = check_unpaywall(paper['doi'])
        
        if oa_info and oa_info.get('is_oa'):
            pdf_url = oa_info.get('pdf_url')
            
            print(f"  ✓ Open Access found!")
            print(f"    Version: {oa_info.get('version', 'unknown')}")
            print(f"    Host: {oa_info.get('host_type', 'unknown')}")
            print(f"    License: {oa_info.get('license', 'unknown')}")
            
            if pdf_url:
                print(f"  Attempting download...")
                if download_pdf(pdf_url, output_path):
                    print(f"  ✓ Downloaded to: {output_path}")
                    paper['local_path'] = str(output_path)
                    paper['pdf_url'] = pdf_url
                    results["downloaded"].append(paper)
                else:
                    print(f"  ✗ Download failed")
                    paper['pdf_url'] = pdf_url
                    paper['landing_page'] = oa_info.get('landing_page')
                    results["open_access_found"].append(paper)
            else:
                print(f"  ⚠ OA version found but no PDF URL")
                paper['landing_page'] = oa_info.get('landing_page')
                results["open_access_found"].append(paper)
        
        else:
            print(f"  ✗ Not open access")
            paper['doi_url'] = generate_doi_url(paper['doi'])
            results["not_open_access"].append(paper)
        
        # Rate limiting
        if i < len(PRIORITY_PAPERS):
            time.sleep(2)
    
    # Generate summary report
    print("\n" + "=" * 70)
    print("DOWNLOAD SUMMARY")
    print("=" * 70)
    
    print(f"\n✓ Downloaded: {len(results['downloaded'])}")
    for p in results['downloaded']:
        print(f"  - {p['id']}: {p.get('local_path', 'Unknown')}")
    
    print(f"\n⚠ Open Access (manual download needed): {len(results['open_access_found'])}")
    for p in results['open_access_found']:
        print(f"  - {p['id']}: {p.get('landing_page', p.get('pdf_url', 'No URL'))}")
    
    print(f"\n✗ Not Open Access: {len(results['not_open_access'])}")
    for p in results['not_open_access']:
        print(f"  - {p['id']}: {p.get('doi_url', 'No URL')}")
    
    # Save results to JSON
    results_file = Path("paper_download_results.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ Results saved to: {results_file}")
    
    # Generate manual download instructions
    if results['open_access_found'] or results['not_open_access']:
        print("\n" + "=" * 70)
        print("MANUAL DOWNLOAD INSTRUCTIONS")
        print("=" * 70)
        
        instructions_file = Path("MANUAL_DOWNLOAD_INSTRUCTIONS.md")
        with open(instructions_file, 'w') as f:
            f.write("# Manual Download Instructions\n\n")
            f.write("Papers that need manual download:\n\n")
            
            if results['open_access_found']:
                f.write("## Open Access (Should be free to download)\n\n")
                for p in results['open_access_found']:
                    f.write(f"### {p['id']} - {p['title']}\n")
                    f.write(f"- **Priority:** {p['priority']}\n")
                    f.write(f"- **Parameter:** {p['parameter']}\n")
                    if 'landing_page' in p:
                        f.write(f"- **Link:** {p['landing_page']}\n")
                    if 'pdf_url' in p:
                        f.write(f"- **PDF:** {p['pdf_url']}\n")
                    f.write(f"- **Save as:** papers/{p['id']}_{p['year']}.pdf\n\n")
            
            if results['not_open_access']:
                f.write("## Not Open Access (Requires institution/purchase/request)\n\n")
                for p in results['not_open_access']:
                    f.write(f"### {p['id']} - {p['title']}\n")
                    f.write(f"- **Priority:** {p['priority']}\n")
                    f.write(f"- **Parameter:** {p['parameter']}\n")
                    f.write(f"- **Authors:** {', '.join(p['authors'])}\n")
                    f.write(f"- **DOI:** {p['doi_url']}\n")
                    f.write(f"- **Options:**\n")
                    f.write(f"  1. Access through university library\n")
                    f.write(f"  2. Request via interlibrary loan\n")
                    f.write(f"  3. Email authors (see author_requests/ folder)\n")
                    f.write(f"  4. Purchase ($20-40)\n")
                    f.write(f"- **Save as:** papers/{p['id']}_{p['year']}.pdf\n\n")
        
        print(f"✓ Instructions saved to: {instructions_file}")
    
    # Generate author request emails
    if results['not_open_access']:
        print("\n" + "=" * 70)
        print("AUTHOR REQUEST EMAILS")
        print("=" * 70)
        
        for p in results['not_open_access']:
            author_lastname = p['authors'][0].split()[-1].replace('.', '')
            email_file = requests_dir / f"{p['id']}_request.txt"
            
            with open(email_file, 'w') as f:
                f.write(f"Subject: Request for Full Text: {p['title']}\n\n")
                f.write(f"Dear Dr. {author_lastname},\n\n")
                f.write(f"I am a researcher conducting a systematic validation of computational model parameters ")
                f.write(f"for clinical populations. I am extracting quantitative values from peer-reviewed ")
                f.write(f"literature to strengthen our evidence base.\n\n")
                f.write(f"I would like to request access to your paper:\n\n")
                f.write(f"  {p['title']}\n")
                f.write(f"  {p['journal']}, {p['year']}\n")
                f.write(f"  DOI: {p['doi']}\n\n")
                f.write(f"Your work is cited in our parameter validation for: {p['parameter']}\n\n")
                f.write(f"Specifically, I need to extract the following from your paper:\n")
                f.write(f"- [TODO: Fill in specific values needed]\n\n")
                f.write(f"Would you be able to share a PDF copy?\n\n")
                f.write(f"Thank you for your time and consideration.\n\n")
                f.write(f"Best regards,\n")
                f.write(f"[Your name]\n")
                f.write(f"[Your affiliation]\n")
                f.write(f"[Your email]\n")
        
        print(f"✓ Generated {len(results['not_open_access'])} email templates in: author_requests/")
    
    # Final summary
    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print(f"\n1. Review downloaded PDFs in: papers/")
    print(f"2. Manual download: See {instructions_file}")
    print(f"3. Author requests: See author_requests/ folder")
    print(f"4. Once complete, run extraction script")
    
    total = len(PRIORITY_PAPERS)
    got = len(results['downloaded'])
    print(f"\nProgress: {got}/{total} papers ({got/total*100:.0f}%)")
    
    if got == total:
        print("\n🎉 All papers downloaded! Ready for extraction.")
    elif got > 0:
        print(f"\n✓ Good start! {total - got} papers still needed.")
    else:
        print("\n⚠ No papers downloaded automatically. Manual steps needed.")


if __name__ == "__main__":
    main()
