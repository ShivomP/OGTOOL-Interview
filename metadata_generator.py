import os
import openai
from dotenv import load_dotenv
import ast

# Load environment variables from a .env file
load_dotenv()

# Initialize OpenAI client using API key from environment
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Function to generate metadata from a markdown string using LLM
def generate_metadata(markdown: str, url: str = None, title: str = "Untitled", published_time: str = "") -> dict:
    """
    Uses GPT to extract metadata fields from a given markdown:
    - title (guessed if not explicitly present)
    - content_type (e.g., blog, book, linkedin_post, etc.)
    - author (organization or individual)
    
    Falls back to default values if LLM fails.
    """

    # Prompt includes first 4000 chars of markdown for token limit safety
    prompt = f"""
        You are a structured data generator for a content ingestion pipeline.

        Given the following markdown content, extract ONLY:
        - "title" → use your best guess if not explicitly stated
        - "content_type" → one of: blog, podcast_transcript, call_transcript, linkedin_post, reddit_comment, book, other
        - "author" → person or org name (leave empty if unknown)

        Respond ONLY with a JSON object that has these three fields.

        Markdown:
        ---
        {markdown[:4000]}
    """

    try:
        # Use OpenAI to get metadata from markdown
        response = client.chat.completions.create(
            model="chatgpt-4o-latest",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        raw = response.choices[0].message.content.strip()

        # Strip JSON formatting if wrapped in ```json or similar blocks
        if raw.startswith("```json"):
            raw = raw.split("```json")[-1].split("```")[0].strip()
        elif raw.startswith("```"):
            raw = raw.strip("```").strip()

        # Use eval to parse string into dictionary (assuming trusted source)
        metadata = eval(raw)

        return {
            "title": title,
            "content": markdown,
            "content_type": metadata.get("content_type", "other"),
            "source_url": url or "",
            "author": metadata.get("author", ""),
            "user_id": ""
        }

    except Exception as e:
        # Fallback metadata if LLM call fails
        print("LLM metadata enrichment failed:", e)
        return {
            "title": title,
            "content": markdown,
            "content_type": "blog",
            "source_url": url or "",
            "author": "",
            "user_id": ""
        }


# Function to infer a document title from the start of its content
def infer_title_from_probe(probe_text: str) -> str:
    """
    Given the opening text of a document, uses GPT to infer a title.
    Returns the predicted title as a simple string.
    """
    prompt = f"""
        Below is the beginning of a PDF. Infer the **title of the document** based on this content.

        Only return the **title** — no explanation, no quotes.

        PDF excerpt:
        \"\"\" 
        {probe_text}
        \"\"\" 
        Title:
    """

    response = client.chat.completions.create(
        model="chatgpt-4o-latest",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    return response.choices[0].message.content.strip()


# Function to extract probable clickable article titles from a markdown index page
def guess_clickable_texts(markdown: str) -> list:
    """
    Parses a markdown version of a webpage and returns a list of likely clickable article titles,
    such as blog post headlines from an index page.

    Returns a list of strings (titles).
    """
    prompt = f"""
        You are given a website page converted to Markdown.

        Identify all likely clickable article titles or links. These may include text like "developer 101: introduction to python" that would typically be linked on a blog index page.

        Respond ONLY with a **valid JSON list of strings**.

        Do NOT include any explanation, comments, or markdown formatting.

        Example output:
        [
        "Why SaaS Companies Offer Analytics",
        "Don’t build ChatGPT for X"
        ]

        Markdown content:
        -----
        {markdown}
    """

    try:
        response = client.chat.completions.create(
            model="chatgpt-4o-latest",
            messages=[
                {"role": "system", "content": "You are a semantic web parser."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        raw = response.choices[0].message.content.strip()

        # Remove code block wrappers if present
        if raw.startswith("```json"):
            raw = raw.split("```json")[-1].split("```")[0].strip()
        elif raw.startswith("```"):
            raw = raw.strip("```").strip()

        # Parse JSON list safely using ast
        if raw.startswith("["):
            return ast.literal_eval(raw)

        print("LLM response not in expected format.")
        return []

    except Exception as e:
        print(f"Failed to guess clickable texts: {e}")
        return []
