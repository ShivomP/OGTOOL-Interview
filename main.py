import json
from cli import parse_args
from content_fetcher import fetch_content_from_url, extract_article_links
from metadata_generator import generate_metadata, infer_title_from_probe
from pdf_chunker import download_pdf_from_gdrive, extract_paragraphs_from_pdf, chunk_paragraphs_by_tokens
from concurrent.futures import ThreadPoolExecutor, as_completed

def handle_url_input(url: str, user_id: str) -> dict:
    """
    Processes a URL using the Jina Reader API and enriches it with metadata.

    Args:
        url (str): The URL to process.
        user_id (str): ID of the user initiating the request.

    Returns:
        dict: Enriched metadata dictionary with title, content, type, etc.
    """
    content_data = fetch_content_from_url(url)

    enriched = generate_metadata(
        markdown=content_data["content"],
        url=content_data["source_url"],
        title=content_data["title"],
        published_time=content_data.get("published_time", "")
    )
    enriched["user_id"] = user_id
    return enriched

def handle_pdf_input(pdf_path: str, user_id: str = "", max_pages_for_metadata: int = 6, source_url: str = "") -> list:
    """
    Handles parsing and enrichment of a local or downloaded PDF.

    - Extracts the first few pages for metadata.
    - Attempts title inference if title is unknown.
    - Extracts the full content and chunks it by token limit.

    Args:
        pdf_path (str): Path to the PDF file.
        user_id (str): Optional user ID.
        max_pages_for_metadata (int): Number of pages to extract for metadata inference.
        source_url (str): Source URL (for GDrive fallback traceability).

    Returns:
        list: List of enriched content chunks.
    """
    # Step 1: Extract paragraphs from initial pages to infer metadata
    probe_paragraphs = extract_paragraphs_from_pdf(pdf_path, max_pages=max_pages_for_metadata)
    probe_text = "\n\n".join(probe_paragraphs)
    metadata = generate_metadata(markdown=probe_text, title="", url="")

    # Safe fallback values in case of missing or unknown fields
    author = metadata.get("author", "")
    content_type = metadata.get("content_type", "other")
    title = metadata.get("title", "Untitled")

    # If GPT fails to infer a proper title, try again using dedicated title inference
    if not title or title.lower() in {"untitled", "unknown", ""}:
        try:
            title = infer_title_from_probe(probe_text)
        except Exception as e:
            print(f"Failed to infer title: {e}")
            title = "Untitled"

    # Step 2: Extract full content and chunk it based on token count
    all_paragraphs = extract_paragraphs_from_pdf(pdf_path)
    chunks = chunk_paragraphs_by_tokens(all_paragraphs)

    enriched_chunks = []
    for i, chunk in enumerate(chunks):
        enriched = {
            "title": f"{title}",
            "content": chunk,
            "content_type": content_type,
            "source_url": source_url,
            "author": author,
            "user_id": user_id
        }
        enriched_chunks.append(enriched)

    return enriched_chunks

def process_url(url, user_id):
    """
    Wrapper for processing URL input with exception handling.
    """
    try:
        print(f"Processing URL: {url}")
        return handle_url_input(url, user_id)
    except Exception as e:
        print(f"Failed to process URL {url}: {e}")
        return None

def process_local_pdf(pdf_path, user_id):
    """
    Wrapper for processing local PDF files.
    """
    try:
        print(f"Processing local PDF: {pdf_path}")
        return handle_pdf_input(pdf_path, user_id)
    except Exception as e:
        print(f"Failed to process PDF {pdf_path}: {e}")
        return None

def process_gdrive_pdf(gdrive_url, user_id):
    """
    Downloads a PDF from a Google Drive link and processes it.
    """
    try:
        print(f"Downloading and processing GDrive PDF: {gdrive_url}")
        pdf_path = download_pdf_from_gdrive(gdrive_url)
        return handle_pdf_input(pdf_path, user_id, source_url=gdrive_url)
    except Exception as e:
        print(f"Failed to process GDrive link {gdrive_url}: {e}")
        return None


def main():
    """
    CLI entry point:
    - Parses args (URLs, PDFs, GDrive links, blog index pages).
    - Extracts article links from blog indexes (RSS or HTML).
    - Processes each URL/PDF concurrently.
    - Saves enriched results to a specified output JSON file.
    """
    args = parse_args()
    all_items = []
    resolved_urls = list(args.urls or [])

    # Step 1: Extract links from blog index pages
    if args.blog_indexes:
        for index_url in args.blog_indexes:
            print(f"Extracting blog/article links from: {index_url}")
            extracted = extract_article_links(index_url)
            print(f"Found {len(extracted)} articles")
            resolved_urls.extend(extracted)

    # Step 2: Launch concurrent processing tasks
    with ThreadPoolExecutor() as executor:
        futures = []

        # Submit article URL processing jobs
        for url in resolved_urls:
            futures.append(executor.submit(process_url, url, args.user_id))

        # Submit local PDF processing jobs
        if args.pdfs:
            for pdf_path in args.pdfs:
                futures.append(executor.submit(process_local_pdf, pdf_path, args.user_id))

        # Submit Google Drive PDF processing jobs
        if args.gdrive_links:
            for link in args.gdrive_links:
                futures.append(executor.submit(process_gdrive_pdf, link, args.user_id))

        # Step 3: Collect results from all jobs
        for future in as_completed(futures):
            result = future.result()
            if isinstance(result, list):
                all_items.extend(result)
            elif isinstance(result, dict):
                all_items.append(result)

    # Step 4: Write output to file
    result = {
        "team_id": args.team_id,
        "items": all_items
    }

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f" Successfully saved {len(all_items)} items to {args.out}")


if __name__ == "__main__":
    main()
