#!/usr/bin/env python3
"""
ICL Website Crawler

Crawls the Innovation & Creativity Lab website to extract:
1. Page content (tools, equipment, guides)
2. PDF links (manuals, SOPs, hardware/software guides)
3. Downloads PDFs for text extraction

Usage:
    python scripts/crawl_icl.py
"""

import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# Configuration
BASE_URL = "https://icl.sites.gettysburg.edu"
OUTPUT_DIR = Path(__file__).parent.parent / "knowledge_base"
RAW_DIR = OUTPUT_DIR / "raw"
PDF_DIR = OUTPUT_DIR / "pdfs"

# Pages to crawl
PAGES_TO_CRAWL = [
    "/",
    "/tools/",
    "/tools/3d-printing/",
    "/tools/laser-cutting/",
    "/tools/cnc-machining/",
    "/tools/sewing-machines/",
    "/tools/virtual-reality/",
    "/tools/vinyl-cutting/",
    "/hours/",
    "/contact/",
]

# Request settings
HEADERS = {
    "User-Agent": "ICL Voice Assistant KB Builder/1.0 (Educational Project)"
}
REQUEST_DELAY = 1  # seconds between requests


def clean_text(text: str) -> str:
    """Clean extracted text by removing extra whitespace."""
    # Replace multiple newlines with double newline
    text = re.sub(r'\n\s*\n', '\n\n', text)
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)
    # Strip leading/trailing whitespace from lines
    lines = [line.strip() for line in text.split('\n')]
    return '\n'.join(lines).strip()


def extract_page_content(soup: BeautifulSoup, url: str) -> dict:
    """Extract structured content from a page."""
    # Remove navigation, footer, social links
    for element in soup.find_all(['nav', 'footer', 'header']):
        element.decompose()
    
    # Remove social media links sections
    for element in soup.find_all(class_=re.compile(r'social|twitter|instagram|tiktok', re.I)):
        element.decompose()
    
    # Find main content area
    main_content = soup.find('main') or soup.find(id='site-content') or soup.find('article') or soup.body
    
    if not main_content:
        return {"url": url, "title": "", "content": "", "pdf_links": []}
    
    # Extract title
    title_elem = soup.find('h1')
    title = title_elem.get_text(strip=True) if title_elem else ""
    
    # Extract PDF links
    pdf_links = []
    for link in main_content.find_all('a', href=True):
        href = link.get('href', '')
        if href.endswith('.pdf'):
            pdf_url = urljoin(url, href)
            link_text = link.get_text(strip=True) or Path(urlparse(href).path).stem
            pdf_links.append({
                "url": pdf_url,
                "name": link_text
            })
    
    # Extract text content with structure
    content_parts = []
    
    for element in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'ul']):
        text = element.get_text(strip=True)
        if not text:
            continue
        
        # Skip navigation/social media text
        skip_patterns = [
            r'^(Home|Tools and Resources|Projects|Hours and Events|Contact|Impact Report)$',
            r'^(Twitter|Instagram|TikTok)$',
            r'^Skip to the content$',
            r'^To the top',
            r'^Up ↑$',
            r'^Powered by WordPress$',
            r'^© \d{4}',
            r'^Find Us$',
            r'^Address:',
            r'^Hours: The lab is open',
        ]
        
        if any(re.match(pattern, text, re.I) for pattern in skip_patterns):
            continue
        
        tag = element.name
        if tag == 'h1':
            content_parts.append(f"\n# {text}\n")
        elif tag == 'h2':
            content_parts.append(f"\n## {text}\n")
        elif tag == 'h3':
            content_parts.append(f"\n### {text}\n")
        elif tag == 'h4':
            content_parts.append(f"\n#### {text}\n")
        elif tag == 'h5':
            content_parts.append(f"\n##### {text}\n")
        elif tag == 'h6':
            content_parts.append(f"\n###### {text}\n")
        elif tag == 'li':
            # Check if it's not a nav link
            parent = element.find_parent('ul')
            if parent and not parent.find_parent('nav'):
                content_parts.append(f"- {text}")
        elif tag == 'p':
            content_parts.append(text)
    
    content = clean_text('\n'.join(content_parts))
    
    return {
        "url": url,
        "title": title,
        "content": content,
        "pdf_links": pdf_links
    }


def crawl_page(url: str) -> dict:
    """Crawl a single page and extract content."""
    print(f"  Crawling: {url}")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"    ERROR: {e}")
        return {"url": url, "error": str(e)}
    
    soup = BeautifulSoup(response.text, 'html.parser')
    return extract_page_content(soup, url)


def download_pdf(url: str, save_path: Path) -> bool:
    """Download a PDF file."""
    print(f"  Downloading: {url}")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=60, stream=True)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"    Saved: {save_path.name}")
        return True
    except requests.RequestException as e:
        print(f"    ERROR: {e}")
        return False


def sanitize_filename(name: str) -> str:
    """Create a safe filename from a string."""
    # Remove or replace invalid characters
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = re.sub(r'\s+', '_', name)
    name = name.strip('._')
    return name[:100]  # Limit length


def main():
    """Main crawler function."""
    print("=" * 60)
    print("ICL Website Crawler")
    print("=" * 60)
    
    # Ensure output directories exist
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    
    # Storage for all extracted data
    all_pages = []
    all_pdf_links = []
    
    # Step 1: Crawl all pages
    print("\n[Step 1] Crawling pages...")
    for path in PAGES_TO_CRAWL:
        url = urljoin(BASE_URL, path)
        page_data = crawl_page(url)
        all_pages.append(page_data)
        
        # Collect PDF links
        if 'pdf_links' in page_data:
            for pdf in page_data['pdf_links']:
                if pdf not in all_pdf_links:
                    all_pdf_links.append(pdf)
        
        time.sleep(REQUEST_DELAY)
    
    # Save raw page data
    raw_pages_file = RAW_DIR / "pages.json"
    with open(raw_pages_file, 'w', encoding='utf-8') as f:
        json.dump(all_pages, f, indent=2, ensure_ascii=False)
    print(f"\n  Saved {len(all_pages)} pages to {raw_pages_file}")
    
    # Step 2: Download PDFs
    print(f"\n[Step 2] Downloading {len(all_pdf_links)} PDFs...")
    pdf_manifest = []
    
    for pdf_info in all_pdf_links:
        pdf_url = pdf_info['url']
        pdf_name = pdf_info['name']
        
        # Create filename from URL
        url_path = urlparse(pdf_url).path
        original_name = Path(url_path).name
        safe_name = sanitize_filename(original_name)
        
        if not safe_name.endswith('.pdf'):
            safe_name += '.pdf'
        
        save_path = PDF_DIR / safe_name
        
        # Skip if already downloaded
        if save_path.exists():
            print(f"  Skipping (exists): {safe_name}")
            pdf_manifest.append({
                "url": pdf_url,
                "name": pdf_name,
                "local_file": safe_name,
                "downloaded": True
            })
            continue
        
        success = download_pdf(pdf_url, save_path)
        pdf_manifest.append({
            "url": pdf_url,
            "name": pdf_name,
            "local_file": safe_name,
            "downloaded": success
        })
        
        time.sleep(REQUEST_DELAY)
    
    # Save PDF manifest
    pdf_manifest_file = RAW_DIR / "pdf_manifest.json"
    with open(pdf_manifest_file, 'w', encoding='utf-8') as f:
        json.dump(pdf_manifest, f, indent=2, ensure_ascii=False)
    print(f"\n  PDF manifest saved to {pdf_manifest_file}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("CRAWL COMPLETE")
    print("=" * 60)
    print(f"Pages crawled: {len(all_pages)}")
    print(f"PDFs found: {len(all_pdf_links)}")
    print(f"PDFs downloaded: {sum(1 for p in pdf_manifest if p['downloaded'])}")
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print(f"  - Raw data: {RAW_DIR}")
    print(f"  - PDFs: {PDF_DIR}")
    
    return all_pages, pdf_manifest


if __name__ == "__main__":
    main()
