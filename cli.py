import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Import technical knowledge into knowledgebase format.")

    parser.add_argument("--urls", nargs="*", help="List of blog/article URLs to ingest.")
    parser.add_argument("--pdfs", nargs="*", help="List of PDF file paths to process.")
    parser.add_argument("--gdrive_links", nargs="*", help="List of Google Drive links to PDFs.")
    parser.add_argument("--team_id", required=True, help="Team ID to associate with the content.")
    parser.add_argument("--user_id", required=True, help="User ID for comment personalization.")
    parser.add_argument("--out", default="output.json", help="Path to save the output JSON file.")
    parser.add_argument("--blog_indexes", nargs="*", help="List of blog/article indexes")

    return parser.parse_args()
