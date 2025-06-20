import requests
from bs4 import BeautifulSoup
from metadata_generator import guess_clickable_texts
from urllib.parse import urljoin, urlparse
import feedparser
import os
from dotenv import load_dotenv
from markdownify import markdownify as md
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Load API key for Jina Reader
load_dotenv()
JINA_API_KEY = os.getenv("JINA_API_KEY")


def fetch_content_from_url(url: str) -> dict:
    """
    Fetches structured content using the Jina Reader API for a given article URL.

    Returns:
        dict with keys: title, content (in markdown), published_time, source_url
    """
    try:
        response = requests.get(
            f"https://r.jina.ai/{url}",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {JINA_API_KEY}"
            },
            timeout=30
        )
        response.raise_for_status()
        data = response.json().get("data", {})

        return {
            "title": data.get("title", "Untitled"),
            "content": data.get("content", ""),
            "published_time": data.get("publishedTime", ""),
            "source_url": data.get("url", url)
        }

    except Exception as e:
        raise Exception(f"Failed to fetch JSON content from {url}: {e}")


def get_rss_feed_url(html: str, base_url: str) -> str | None:
    """
    Parses HTML to find an RSS feed link if available.

    Returns:
        Full RSS feed URL or None if not found.
    """
    soup = BeautifulSoup(html, "html.parser")
    link = soup.find("link", type="application/rss+xml")
    if link and link.get("href"):
        return urljoin(base_url, link["href"])
    return None


def extract_links_from_rss(rss_url: str) -> list:
    """
    Extracts article links from an RSS feed.

    Returns:
        A list of URLs found in the feed.
    """
    feed = feedparser.parse(rss_url)
    links = []
    for entry in feed.entries:
        if hasattr(entry, "link"):
            links.append(entry.link)
    return links


def extract_links_from_index_page(index_url: str) -> list:
    """
    Attempts to heuristically extract article/blog links from a static HTML index page.

    Returns:
        A list of inferred article URLs.
    """
    try:
        response = requests.get(index_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        base = "{uri.scheme}://{uri.netloc}".format(uri=urlparse(index_url))

        links = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            full_url = urljoin(base, href)
            parsed = urlparse(full_url)

            # Heuristics: Check for common blog/article paths
            if parsed.netloc == urlparse(index_url).netloc and any(x in parsed.path for x in [
                "blog", "post", "article", "/p/", "/news/", "/story/", "/entry/", "/read/"
            ]):
                links.add(full_url)

        return list(links)
    except Exception as e:
        print(f"Failed to extract links from index page {index_url}: {e}")
        return []


def try_click_text(driver, index_url, original_url, text) -> str | None:
    """
    Tries to simulate a click on a text element and captures the resulting URL.

    Args:
        driver: Selenium WebDriver instance
        index_url: URL to load
        original_url: Original URL to compare against
        text: Text to search and click

    Returns:
        URL navigated to after click, or None if no change occurred.
    """
    try:
        driver.get(index_url)
        elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{text}')]")
        for el in elements:
            try:
                # Attempt to click and extract resulting URL
                ActionChains(driver).move_to_element(el).click().perform()
                time.sleep(1.5)
                current_url = driver.current_url.rstrip("/")
                if current_url != original_url:
                    print(f"[+] Discovered from '{text}': {current_url}")
                    return current_url
            except Exception as click_error:
                print(f"[!] Click failed on '{text}': {click_error}")
    except Exception as e:
        print(f"[!] Element not found for '{text}': {e}")
    return None


def follow_clickable_texts(index_url: str, texts: list[str], max_workers=4) -> list:
    """
    Uses Selenium to parallelize clicking on guessed article titles and collecting resulting links.

    Returns:
        A list of discovered article URLs.
    """
    print(f"[Selenium Fallback] Parallel click attempts on: {index_url}")
    original_url = index_url.rstrip("/")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    results = set()

    def worker(text):
        # Isolate each worker in its own WebDriver instance
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        result = try_click_text(driver, index_url, original_url, text)
        driver.quit()
        return result

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(worker, text) for text in texts]
        for future in as_completed(futures):
            url = future.result()
            if url:
                results.add(url)

    return list(results)


def extract_article_links(index_url: str) -> list:
    """
    Main method to extract likely article/blog links from an index page.

    Uses RSS (if available), static HTML heuristics, or falls back to OpenAI + Selenium click simulation.

    Returns:
        List of unique article links.
    """
    try:
        print(f"Trying to extract article links from: {index_url}")
        html = requests.get(index_url, timeout=10).text
        rss_url = get_rss_feed_url(html, base_url=index_url)

        rss_links = set()
        if rss_url:
            print(f"RSS feed found: {rss_url}")
            rss_links.update(extract_links_from_rss(rss_url))
        else:
            print("No RSS feed found.")

        html_links = set(extract_links_from_index_page(index_url))

        # Combine both link sources
        all_links = list(rss_links.union(html_links))

        # Filter out index page itself
        all_links = [link for link in all_links if link.rstrip("/") != index_url.rstrip("/")]

        # If no links found, fallback to AI + Selenium clicking
        if not all_links:
            print("No static links found. Trying OpenAI-assisted HTML extraction...")
            markdown = md(html)
            guessed_texts = guess_clickable_texts(markdown)

            if guessed_texts:
                selenium_links = follow_clickable_texts(index_url, guessed_texts)
                all_links = list(set(selenium_links))

        print(f"Total unique links extracted: {len(all_links)}")
        return all_links

    except Exception as e:
        print(f"Error while extracting article links from {index_url}: {e}")
        return []
