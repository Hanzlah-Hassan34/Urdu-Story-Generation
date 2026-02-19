import argparse
import csv
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


BASE_URL = "https://www.urdupoint.com"
CATEGORY_FIRST = "https://www.urdupoint.com/kids/category/true-stories.html"
CATEGORY_PAGED = "https://www.urdupoint.com/kids/category/true-stories-page{page_num}.html"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"


def log(msg):
    print(f"[LOG] {msg}", flush=True)


def clean_text(text):
    bad_lines = [
        "LIVE",
        "Advertisement",
        "Tap to unmute",
        "Learn more",
        "An error occurred",
    ]
    lines = text.split("\n")
    cleaned = [line for line in lines if not any(bad in line for bad in bad_lines)]
    return "\n".join(cleaned).strip()


def build_session():
    session = requests.Session()
    retry = Retry(
        total=5,
        connect=5,
        read=5,
        backoff_factor=1.0,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def get_category_url(page_num):
    if page_num == 1:
        return CATEGORY_FIRST
    return CATEGORY_PAGED.format(page_num=page_num)


def fetch_html(session, url, timeout=30):
    try:
        response = session.get(url, timeout=timeout)
        response.raise_for_status()
        return response.text
    except Exception as err:
        log(f"Failed to fetch URL: {url} | {err}")
        return None


def extract_story_links(category_html):
    soup = BeautifulSoup(category_html, "html.parser")
    links = []
    for a_tag in soup.select("a.sharp_box[href]"):
        href = a_tag.get("href", "").strip()
        if not href:
            continue
        links.append(urljoin(BASE_URL, href))
    return links


def extract_story_data(story_html):
    soup = BeautifulSoup(story_html, "html.parser")

    title_tag = soup.select_one("h2.txt_blue")
    title = title_tag.get_text(strip=True) if title_tag else "No title"

    content_tag = soup.select_one("div.txt_detail.urdu")
    if not content_tag:
        return title, ""

    for tag in content_tag(["script", "style", "iframe", "noscript"]):
        tag.decompose()

    text = clean_text(content_tag.get_text(separator="\n", strip=True))
    return title, text


def scrape_urdu_stories(
    start_page=1,
    max_pages=None,
    max_stories_per_page=None,
    output_file="urdu_tru_stories.csv",
):
    log("Starting scraper")
    session = build_session()
    output_path = Path(output_file).resolve()

    seen_links = set()
    page_num = start_page
    pages_processed = 0
    stories_written = 0
    stories_failed = 0

    with output_path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["title", "content"])
        csv_file.flush()

        while True:
            if max_pages is not None and pages_processed >= max_pages:
                log(f"Reached max pages limit ({max_pages}), stopping.")
                break

            category_url = get_category_url(page_num)
            log(f"Opening category page {page_num}: {category_url}")
            category_html = fetch_html(session, category_url)
            if not category_html:
                stories_failed += 1
                page_num += 1
                pages_processed += 1
                continue

            story_links = [link for link in extract_story_links(category_html) if link not in seen_links]
            if not story_links:
                log("No new stories found, stopping pagination.")
                break

            if max_stories_per_page is not None:
                story_links = story_links[:max_stories_per_page]

            log(f"Found {len(story_links)} stories on this page")

            for i, link in enumerate(story_links, 1):
                log(f"Scraping story {i}/{len(story_links)}: {link}")
                seen_links.add(link)

                story_html = fetch_html(session, link)
                if not story_html:
                    stories_failed += 1
                    continue

                title, text = extract_story_data(story_html)
                if not text:
                    stories_failed += 1
                    log("Empty content extracted, skipping story.")
                    continue

                writer.writerow([title, text])
                csv_file.flush()
                stories_written += 1
                log("Written story to CSV")
                time.sleep(0.2)

            page_num += 1
            pages_processed += 1
            time.sleep(0.5)

    log(
        f"Scraping finished. Output: {output_path}. "
        f"Written: {stories_written}, Failed: {stories_failed}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-page", type=int, default=1)
    parser.add_argument("--max-pages", type=int, default=None, help="Stop after N category pages.")
    parser.add_argument(
        "--max-stories-per-page",
        type=int,
        default=None,
        help="Limit stories processed per category page.",
    )
    parser.add_argument("--output", default="urdu_tru_stories.csv")
    args = parser.parse_args()

    log("Program started")
    scrape_urdu_stories(
        start_page=args.start_page,
        max_pages=args.max_pages,
        max_stories_per_page=args.max_stories_per_page,
        output_file=args.output,
    )
    log("Program complete")
