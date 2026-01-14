#!/usr/bin/env python3
"""
Aggressive Paper Downloader
Tries multiple sources and methods to find papers
"""

import urllib.request
import urllib.error
import json
import time
import ssl
from pathlib import Path
from typing import Optional, Dict

# Create SSL context that doesn't verify certificates (for testing only)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

PAPERS = [
    {
        "id": "kofler2013",
        "doi": "10.1016/j.cpr.2013.06.001",
        "title": "Reaction time variability in ADHD",
        "pmcid": None,  # Try to find
        "alternative_sources": [
            "https://www.sciencedirect.com/science/article/pii/S0272735813000695",
        ]
    },
    {
        "id": "burke2005",
        "doi": "10.1016/j.psyneuen.2005.02.010",
        "title": "Depression and cortisol",
        "pmcid": None,
        "alternative_sources": []
    },
    {
        "id": "kasper2012",
        "doi": "10.1016/j.cpr.2012.07.001",
        "title": "ADHD working memory",
        "pmcid": None,
        "alternative_sources": []
    },
    {
        "id": "corbett2009",
        "doi": "10.1186/2040-2392-1-13",
        "title": "ASD cortisol",
        "pmcid": "PMC2802360",  # This is open access!
        "alternative_sources": [
            "https://molecularautism.biomedcentral.com/articles/10.1186/2040-2392-1-13",
            "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2802360/pdf/",
        ]
    },
    {
        "id": "huang-pollock2012",
        "doi": "10.1037/a0027205",
        "title": "ADHD vigilance",
        "pmcid": "PMC3391585",  # This might be open access
        "alternative_sources": []
    },
    {
        "id": "crawford2004",
        "doi": "10.1348/0144665031752934",
        "title": "PANAS validity",
        "pmcid": None,
        "alternative_sources": []
    },
]


def try_pmc_download(pmcid: str, output_path: Path) -> bool:
    """Try to download from PubMed Central"""
    if not pmcid:
        return False
    
    # Remove PMC prefix if present
    pmcid_num = pmcid.replace("PMC", "")
    
    urls_to_try = [
        f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmcid_num}/pdf/",
        f"https://europepmc.org/articles/PMC{pmcid_num}?pdf=render",
    ]
    
    for url in urls_to_try:
        print(f"  Trying PMC: {url}")
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0')
            
            with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
                content = response.read()
                
                # Check if it's a PDF
                if content[:4] == b'%PDF':
                    with open(output_path, 'wb') as f:
                        f.write(content)
                    print(f"  ✓ Downloaded from PMC!")
                    return True
                else:
                    print(f"  ✗ Not a PDF")
                    
        except Exception as e:
            print(f"  ✗ Failed: {e}")
    
    return False


def try_biocentral_download(doi: str, output_path: Path) -> bool:
    """Try BioMed Central direct download"""
    if "2040-2392" in doi:  # Molecular Autism
        parts = doi.split("/")
        article_id = parts[-1]
        
        urls_to_try = [
            f"https://molecularautism.biomedcentral.com/track/pdf/{doi}",
            f"https://molecularautism.biomedcentral.com/counter/pdf/{doi}",
        ]
        
        for url in urls_to_try:
            print(f"  Trying BioMed Central: {url}")
            try:
                req = urllib.request.Request(url)
                req.add_header('User-Agent', 'Mozilla/5.0')
                
                with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
                    content = response.read()
                    
                    if content[:4] == b'%PDF':
                        with open(output_path, 'wb') as f:
                            f.write(content)
                        print(f"  ✓ Downloaded from BioMed Central!")
                        return True
                        
            except Exception as e:
                print(f"  ✗ Failed: {e}")
    
    return False


def try_semantic_scholar(title: str, output_path: Path) -> bool:
    """Try Semantic Scholar API"""
    print(f"  Trying Semantic Scholar...")
    
    try:
        # Search for paper
        search_url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={urllib.parse.quote(title)}&fields=openAccessPdf,externalIds"
        
        req = urllib.request.Request(search_url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            
            if data.get('data') and len(data['data']) > 0:
                paper = data['data'][0]
                
                if paper.get('openAccessPdf') and paper['openAccessPdf'].get('url'):
                    pdf_url = paper['openAccessPdf']['url']
                    print(f"  Found PDF: {pdf_url}")
                    
                    # Download
                    pdf_req = urllib.request.Request(pdf_url)
                    pdf_req.add_header('User-Agent', 'Mozilla/5.0')
                    
                    with urllib.request.urlopen(pdf_req, timeout=30, context=ssl_context) as pdf_response:
                        content = pdf_response.read()
                        
                        if content[:4] == b'%PDF':
                            with open(output_path, 'wb') as f:
                                f.write(content)
                            print(f"  ✓ Downloaded from Semantic Scholar!")
                            return True
                            
    except Exception as e:
        print(f"  ✗ Failed: {e}")
    
    return False


def try_core_download(doi: str, output_path: Path) -> bool:
    """Try CORE.ac.uk"""
    print(f"  Trying CORE.ac.uk...")
    
    try:
        # Search CORE
        search_url = f"https://core.ac.uk:443/api-v2/search/{urllib.parse.quote(doi)}?apiKey=DEMO"
        
        req = urllib.request.Request(search_url)
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            
            if data.get('data') and len(data['data']) > 0:
                for item in data['data']:
                    if item.get('downloadUrl'):
                        pdf_url = item['downloadUrl']
                        print(f"  Found: {pdf_url}")
                        
                        # Try download
                        pdf_req = urllib.request.Request(pdf_url)
                        pdf_req.add_header('User-Agent', 'Mozilla/5.0')
                        
                        with urllib.request.urlopen(pdf_req, timeout=30, context=ssl_context) as pdf_response:
                            content = pdf_response.read()
                            
                            if content[:4] == b'%PDF':
                                with open(output_path, 'wb') as f:
                                    f.write(content)
                                print(f"  ✓ Downloaded from CORE!")
                                return True
                                
    except Exception as e:
        print(f"  ✗ Failed: {e}")
    
    return False


def main():
    print("=" * 70)
    print("AGGRESSIVE PAPER DOWNLOADER")
    print("=" * 70)
    print("\nTrying multiple sources for each paper...")
    print()
    
    papers_dir = Path("papers")
    papers_dir.mkdir(exist_ok=True)
    
    results = {"downloaded": [], "failed": []}
    
    for i, paper in enumerate(PAPERS, 1):
        print(f"\n[{i}/{len(PAPERS)}] {paper['id']}")
        print(f"  Title: {paper['title']}")
        print(f"  DOI: {paper['doi']}")
        
        filename = f"{paper['id']}_2013.pdf" if "2013" in paper['id'] else f"{paper['id']}.pdf"
        output_path = papers_dir / filename
        
        if output_path.exists():
            print(f"  ✓ Already exists: {output_path}")
            results["downloaded"].append(paper)
            continue
        
        # Try multiple methods
        success = False
        
        # 1. Try PMC if we have ID
        if paper.get('pmcid'):
            print(f"  Has PMC ID: {paper['pmcid']}")
            if try_pmc_download(paper['pmcid'], output_path):
                success = True
        
        # 2. Try BioMed Central for Molecular Autism
        if not success and "2040-2392" in paper['doi']:
            if try_biocentral_download(paper['doi'], output_path):
                success = True
        
        # 3. Try Semantic Scholar
        if not success:
            if try_semantic_scholar(paper['title'], output_path):
                success = True
        
        # 4. Try CORE
        if not success:
            if try_core_download(paper['doi'], output_path):
                success = True
        
        if success:
            paper['local_path'] = str(output_path)
            results["downloaded"].append(paper)
            print(f"  ✅ SUCCESS: {output_path}")
        else:
            results["failed"].append(paper)
            print(f"  ❌ Could not download automatically")
        
        # Rate limiting
        time.sleep(2)
    
    # Summary
    print("\n" + "=" * 70)
    print("DOWNLOAD RESULTS")
    print("=" * 70)
    print(f"\n✅ Downloaded: {len(results['downloaded'])}/{len(PAPERS)}")
    for p in results['downloaded']:
        print(f"   - {p['id']}: {p.get('local_path', 'Unknown')}")
    
    print(f"\n❌ Failed: {len(results['failed'])}/{len(PAPERS)}")
    for p in results['failed']:
        print(f"   - {p['id']}: {p['doi']}")
    
    if len(results['downloaded']) > 0:
        print(f"\n🎉 Success! Downloaded {len(results['downloaded'])} papers!")
        print(f"   Check the papers/ directory")
    else:
        print(f"\n⚠️  No papers downloaded automatically.")
        print(f"   These papers require institutional access or purchase.")
        print(f"   See MANUAL_DOWNLOAD_INSTRUCTIONS.md for next steps.")
    
    # Save results
    with open("download_results.json", 'w') as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()
