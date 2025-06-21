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

## Functionality Demo
- https://www.loom.com/share/000e9111b0e44964b6464ea2bf14eff8

## Code Demo
### Part One
- https://www.loom.com/share/79509d4d971145dc9cd675567eebc3cd?sid=29e11bd7-f9d2-477c-90c0-90b6e73a725b
### Part Two
- https://www.loom.com/share/ad526524a9af488e96c4abf1b28de742

## Questions
1. What was your thinking process? Why did you build it the way you did?
    After reading the google doc my first impressions of the problem were that I needed to make the web scraper as scalable and reusable as possible. Once I looked at the json format and required fields to return I wasn't quite sure what you expected for the user_id and team_id fields. After some thinking I figured you planned to integrate this almost as a rag to your current pipeline for generating reddit comments where you would 
use this pipeline to query a specific article or group of articles for a team/company and then the user_id would represent the agent you were using to make the comment. As a result of those assumptions I decided to hard code those two inputs. To make this as scalable as possible I had the idea to parallel process urls to make this run quickly. As for reuseability, that was a bit of a struggle especially when it came to websites like quil. I did rely on
openai to fill some gaps but ultimately kept prices fairly cheap. When I started solving this I began with just a single blog post url and tried to generate a model json format for just one url, I started here because I find it easier to scale up and work from the inside out. One useful tool I found was jina ai, it was free and returned and page I sent to it in json format with a title and section labeled content already in markdown. This was very helpful 
and free which was nice. To fill the gaps of content-type and author I passed a chunk of the markdown to openai and prompted it correctly to give me the correct result. I did this knowing that the latest model is very inuitive as I have worked with it before. Next was parsing the pdfs, I did this by following the method you suggested and chunked the pdfs by tokens. I chose tokens because I planned on passing the first chunk to openai to infer the title, author, and content-type. 
This was a bit of a struggle when it came to title so I had to create a separate query for that. The process and logic was pretty similar for google drive links. Next I moved on to the main problem you wanted to solve and that was having the ability to take a blog index page, grab all the article urls and process the article contents into their own json objects under the same team. To start scraped for rss feed because it is very common amongst blog pages, if that didn't work I 
fell back to html parsing and searching for a tags which is probably the most standard approach since most links are embedded that way. Then as a final pitfall which brings me back to the quil page where the links get embedded into the JavaScript and are not easy to scrape. I was actually pretty proud of my solution to this road block. I started bye getting the page in markdown and sending it to gpt, then I devised a prompt that would return a list of potential clickable links.
With that list I used selenium and chrome to search for the text on the screen and see if it directed me to a new page once I clicked on it. If I was redircted, I filtered out false positived by comparing to the original index url. Other than that I would add the link to my result links that were parallel processed. I also ran thess potential text guesses in parallel since selenium takes awhile to run. I think that is as clear as I can get over text, I hope you enjoy testing this 
tool, I really enjoyed solving this problem and I hope to hear back from you.

 
