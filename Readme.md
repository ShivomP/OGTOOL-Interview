# Save Aline Assignment

This pipeline ingests content from URLs, blog index pages, Google Drive PDFs, or local PDF files, and adds to it with structured metadata using OpenAI and Jina APIs.

It supports:
- Blog and article scraping
- RSS feed parsing
- Google Drive PDF extraction
- AI-based metadata generation
- Token-based chunking for LLM training

---

## Instructions
- Clone the repo
- Install the dependencies:
    - I recommend setting up a virtual environment python3 -m venv venv
    - source venv/bin/activate # or `venv\Scripts\activate` on Windows
    - pip install -r requirements.txt
    - I apologize in advance if I missed any packages
- Add the .env file into the root directory
    - OPEN_AI_KEY=your_key
    - JINA_API_KEY=your_key
    - as for the keys, you can email me at shivompaudel@icloud.com and I don't mind sharing my openai key with you even though I know that is a terrible practice, I have roughly $95 in credits I am willing to let you test this with, or you can use your own. For the jina key you can also email me or go to https://jina.ai/reader/#faq and copy a key, it is free.

## Example use cases
1. Article URL
    - python main.py --urls https://interviewing.io/blog/stop-trying-to-make-recruiters-think-or-why-your-resume-is-bad-and-how-to-fix-it --team_id test_team --user_id test_user --out test_output.json
    - for multiple urls just space separate them
2. Google Drive PDF
    - python main.py --gdrive_links https://drive.google.com/file/d/1Udr6zhDxF-LEqxti15UAfe-_vriggdRO/view?usp=drive_link --team_id test_team --user_id test_user --out test_output.json
    - same deal just space separate the gdrive links here is the other link you provided: https://drive.google.com/file/d/10W-Wl8DMISmLe6z1GnTu09sEyuX9dnm6/view?usp=drive_link
3. Local PDF
    - python main.py --pdfs ./test1.pdf ./test2.pdf --team_id test_team --user_id test_user --out test_output.json
4. Blog Index URL
    - python main.py --blog_indexes https://interviewing.io/blog https://interviewing.io/topics#companies https://quill.co/blog https://shreycation.substack.com https://interviewing.io/learn#interview-guides https://nilmamano.com/blog/category/dsa --team_id test_team --user_id test_user --out test_output.json
    - can do single or multiple
5. All Together
    - python main.py --team_id test_team --user_id test_user --out test_output.json --blog_indexes https://interviewing.io/blog https://quill.co/blog https://shreycation.substack.com --gdrive_links https://drive.google.com/file/d/1Udr6zhDxF-LEqxti15UAfe-_vriggdRO/view?usp=drive_link --pdfs ./test2.pdf --urls http://interviewing.io/guides/hiring-process/meta-facebook https://interviewing.io/guides/hiring-process/amazon
- Run the above in your terminal, make sure you are in the root directory of the project