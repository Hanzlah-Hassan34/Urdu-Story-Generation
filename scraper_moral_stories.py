import argparse
import csv
import time
from pathlib import Path

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


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
    return "\n".join(cleaned)


def get_category_url(page_num):
    if page_num == 1:
        return "https://www.urdupoint.com/kids/category/moral-stories.html"
    return f"https://www.urdupoint.com/kids/category/moral-stories-page{page_num}.html"


def build_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--log-level=3")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")

    # Selenium Manager is built into Selenium 4.6+, so this path avoids extra deps.
    try:
        return webdriver.Chrome(options=options)
    except WebDriverException:
        # Fallback to webdriver-manager if explicit setup is needed.
        try:
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager

            return webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=options,
            )
        except Exception as err:
            raise RuntimeError(
                "Unable to start Chrome WebDriver. Install Google Chrome and ensure "
                "Selenium can access/download a matching ChromeDriver."
            ) from err


def safe_get(driver, url, retries=3, retry_sleep=2):
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            driver.get(url)
            return True
        except TimeoutException as err:
            last_error = err
            log(f"Timeout loading URL (attempt {attempt}/{retries}): {url}")
        except WebDriverException as err:
            last_error = err
            log(f"WebDriver error loading URL (attempt {attempt}/{retries}): {url}")
        if attempt < retries:
            time.sleep(retry_sleep * attempt)

    log(f"Skipping URL after retries: {url}. Last error: {last_error}")
    return False


def scrape_urdu_stories(
    start_page=1,
    max_pages=None,
    max_stories_per_page=None,
    output_file="urdu_moral_stories.csv",
):
    log("Starting scraper")
    log("Launching Chrome driver...")
    driver = build_driver()
    driver.set_page_load_timeout(30)

    seen_links = set()
    page_num = start_page
    pages_processed = 0
    stories_written = 0
    stories_failed = 0
    output_path = Path(output_file).resolve()

    try:
        with output_path.open("w", newline="", encoding="utf-8-sig") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["title", "content"])
            csv_file.flush()

            while True:
                if max_pages is not None and pages_processed >= max_pages:
                    log(f"Reached max pages limit ({max_pages}), stopping.")
                    break

                url = get_category_url(page_num)
                log(f"Opening category page {page_num}: {url}")
                if not safe_get(driver, url):
                    stories_failed += 1
                    log("Restarting driver and retrying category page...")
                    driver.quit()
                    driver = build_driver()
                    driver.set_page_load_timeout(30)
                    if not safe_get(driver, url):
                        log("Unable to load category page after restart; stopping.")
                        break
                time.sleep(2)

                soup = BeautifulSoup(driver.page_source, "html.parser")
                links = soup.select("a.sharp_box")
                story_links = [
                    a["href"] if a["href"].startswith("http") else "https://www.urdupoint.com" + a["href"]
                    for a in links
                ]
                story_links = [l for l in story_links if l not in seen_links]

                if not story_links:
                    log("No new stories found, stopping pagination.")
                    break

                if max_stories_per_page is not None:
                    story_links = story_links[:max_stories_per_page]

                log(f"Found {len(story_links)} stories on this page")

                for i, link in enumerate(story_links, 1):
                    log(f"Scraping story {i}/{len(story_links)}: {link}")
                    seen_links.add(link)
                    story_done = False
                    for attempt in range(1, 3):
                        try:
                            if not safe_get(driver, link):
                                raise WebDriverException("Navigation failed for story URL.")

                            try:
                                title = driver.find_element(
                                    By.XPATH,
                                    '//h2[contains(@class,"txt_blue")]',
                                ).text
                            except Exception:
                                title = "No title"

                            content = WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located(
                                    (
                                        By.XPATH,
                                        '//div[contains(@class,"txt_detail") and contains(@class,"urdu")]',
                                    )
                                )
                            )

                            html = content.get_attribute("innerHTML")
                            soup_chunk = BeautifulSoup(html, "html.parser")
                            for tag in soup_chunk(["script", "style", "iframe", "noscript"]):
                                tag.decompose()

                            text = clean_text(soup_chunk.get_text(separator="\n", strip=True))
                            if not text.strip():
                                stories_failed += 1
                                log("Empty content extracted, skipping story.")
                                story_done = True
                                break

                            writer.writerow([title, text])
                            csv_file.flush()
                            stories_written += 1
                            story_done = True
                            log("Written story to CSV")
                            break
                        except WebDriverException as err:
                            log(f"WebDriver error on story (attempt {attempt}/2): {err}")
                            if attempt < 2:
                                log("Restarting driver and retrying story...")
                                try:
                                    driver.quit()
                                except Exception:
                                    pass
                                driver = build_driver()
                                driver.set_page_load_timeout(30)
                            else:
                                stories_failed += 1
                                story_done = True
                                log("Failed story after driver restart retry.")
                        except Exception as err:
                            stories_failed += 1
                            log(f"Failed story: {err}")
                            story_done = True
                            break

                    if not story_done:
                        stories_failed += 1

                page_num += 1
                pages_processed += 1
    except KeyboardInterrupt:
        log("Stopped by user interrupt.")
    finally:
        log("Closing driver...")
        driver.quit()

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
    parser.add_argument("--output", default="urdu_stories.csv")
    args = parser.parse_args()

    log("Program started")
    scrape_urdu_stories(
        start_page=args.start_page,
        max_pages=args.max_pages,
        max_stories_per_page=args.max_stories_per_page,
        output_file=args.output,
    )
    log("Program complete")
