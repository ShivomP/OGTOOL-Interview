import re
import tempfile
import gdown
import tiktoken
import fitz  # PyMuPDF, used for extracting text from PDFs


def download_pdf_from_gdrive(gdrive_url: str) -> str:
    """
    Downloads a PDF file from a Google Drive shareable link.

    Args:
        gdrive_url (str): Google Drive shareable link in the form 'https://drive.google.com/file/d/FILE_ID/view?...'

    Returns:
        str: Local path to the downloaded PDF file.

    Raises:
        ValueError: If the Google Drive link is invalid or malformed.
    """
    # Extract the file ID from the Google Drive link using regex
    match = re.search(r'/d/([\w-]+)', gdrive_url)
    if not match:
        raise ValueError("Invalid Google Drive link")

    file_id = match.group(1)

    # Create a temporary file path for the downloaded PDF
    output = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

    # Download the file using gdown
    gdown.download(f"https://drive.google.com/uc?id={file_id}", output.name, quiet=False)

    return output.name


def extract_paragraphs_from_pdf(pdf_path: str, max_pages: int = None) -> list:
    """
    Extracts paragraphs from a PDF file, optionally limiting to the first `max_pages` pages.

    Args:
        pdf_path (str): Path to the PDF file.
        max_pages (int, optional): Maximum number of pages to parse. Defaults to None (parse all pages).

    Returns:
        list: A list of paragraph strings extracted from the PDF.
    """
    doc = fitz.open(pdf_path)
    paragraphs = []

    for i, page in enumerate(doc):
        # Stop processing if max_pages is specified and reached
        if max_pages and i >= max_pages:
            break

        # Extract plain text from page
        text = page.get_text("text")

        # Split text into paragraphs based on double newline
        for para in text.split("\n\n"):
            cleaned = para.strip()
            if cleaned:
                paragraphs.append(cleaned)

    return paragraphs


def chunk_paragraphs_by_tokens(paragraphs: list, chunk_size: int = 2000) -> list:
    """
    Groups a list of paragraphs into chunks, each with a maximum token count limit.

    Args:
        paragraphs (list): List of paragraph strings.
        chunk_size (int, optional): Max tokens per chunk. Defaults to 2000 tokens.

    Returns:
        list: List of text chunks, each under the specified token limit.
    """
    # Use OpenAI's tokenizer (same as for gpt-3.5/4's cl100k_base)
    enc = tiktoken.get_encoding("cl100k_base")

    chunks = []
    current_chunk = ""

    for para in paragraphs:
        para_tokens = len(enc.encode(para))
        current_tokens = len(enc.encode(current_chunk))

        # If current chunk can fit the new paragraph, add it
        if current_tokens + para_tokens < chunk_size:
            current_chunk += "\n\n" + para
        else:
            # Save the current chunk and start a new one
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para

    # Add the last remaining chunk
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks
