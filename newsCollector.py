
# How to run
# - python3 sys.argv[0] ai cyber attack --days 15 > RESULT.txt
#   (=> then it may produce .debug, .error, and RESULT-government.txt)
# - python3 sys.argv[0] --days 30 maritime cybersecurity --file crawled_articles.csv

from dotenv import load_dotenv
import argparse
import sys
import logging
from google_news_crawler import NewsCrawler as GNewsCrawler
from fetcher_selenium import Fetcher as SeleniumFetcher
import csv
from langchain.prompts import PromptTemplate
from langchain.chains.summarize import load_summarize_chain
from langchain_openai import ChatOpenAI
from langchain_text_splitters import CharacterTextSplitter
from langchain_core.documents import Document

class MyTextLoader:
    def __init__(self, text, source="null"):
        self.text = text
        self.source = source

    def load(self):
        return [Document(page_content=self.text,metadata={'source': self.source})]
    
    def load_and_split(self, text_splitter):
        text = self.text
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + text_splitter.chunk_size, len(text))
            chunk = text[start:end]
            chunks.append(chunk)
            start += text_splitter.chunk_size - text_splitter.chunk_overlap
        return chunks

def summarize_partial_text(text, source="null"):
    openai_llm = ChatOpenAI(temperature=0, model_name='gpt-3.5-turbo-16k')
    
    prompt = PromptTemplate(
        template="Please summarize the following text:\n{text}",
        input_variables=["text"]
    )

    prompt_full = PromptTemplate(
        template= """
        Please summarize the following news article. Note that statements of the summary should be enlisted as the following [FORMAT]. 
        [FORMAT]
        \n
        - summary:
            - 
            -
        \n
        ---
        \n{text}
        """,
        input_variables=['text']
    )

    summarize_chain = load_summarize_chain(
        llm=openai_llm,
        map_prompt=prompt,
        combine_prompt=prompt_full,
        chain_type="map_reduce",
        verbose=False
    )
    
    loader = MyTextLoader(text, source)
    docs = loader.load()
    
    response = summarize_chain.invoke(docs)

    return response["output_text"]

def summarize_text(content_orig_json):
    text_splitter = CharacterTextSplitter(
        separator='',
        chunk_size=1000,  
        chunk_overlap=200 
    )

    chunks = text_splitter.split_text(content_orig_json['content'])
    partial_summaries = [summarize_partial_text(chunk, content_orig_json['link']) for chunk in chunks]
    combined_summary = " ".join(partial_summaries)
    final_summary = summarize_partial_text(combined_summary)

    return final_summary

def process_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('keywords', metavar='keywords', type=str, nargs='+', 
                        default=[], help='a list of search keywords (optional)') 
    parser.add_argument('--days', dest='days', type=str, nargs='?',
                        help='seach for articles published within given days (optional)')
    parser.add_argument('--file', dest='infile', type=str, nargs='?',
                        help='a CSV file that has fields of [date, publisher, title, link, content] (optional)')
    return parser.parse_args()

def get_news_summaries_from_csv(filename):
    with open(filename, 'r') as csvrfile:
        reader = csv.DictReader(csvrfile)
        for row in reader:
            if row['content'] : 
                print(f"\nDate: {row['date']}")
                print(f"Title: {row['title']}")
                print(f"Link: {row['link']}")
                print(f"Content: \n{summarize_text(row)}")

def get_news_summaries_from_crawling(search_url):
    # (1) Get Google news articles regarding the input keywords
    # -----------------
    crawler = GNewsCrawler()
    article_list = crawler.getNews(search_url) # an article has {date, publisher, title, link, content}

    # (2) Now feed up the "content" keys in the above JSON list
    # -----------------
    fetcher = SeleniumFetcher()
    for al in enumerate(article_list):
        content = fetcher.getContents(al['link'])
        if content:
            # at this point, content could be a string, or a list of strings. For latter, make the list to a simple string.
            if isinstance(content, list):
               content = '\n'.join(content)

            al['content'] = content
        else:
            pass
    
    # (3) Temporarily, save the intermediate results to a file
    # -----------------
    keywords_ = '_'.join(keyword_list)
    tempfilename = 'crawled_articles_' + keywords_ + '.csv'
    fields = ['date', 'publisher', 'title', 'link', 'content']
    with open(tempfilename, 'w', newline='') as csvwfile:
        writer = csv.DictWriter(csvwfile, fieldnames=fields)
        writer.writeheader()
        writer.writerows(article_list)

    # (4) News is ready, pass it to LLM
    # -----------------
    for al in article_list: 
        if al['content'] : 
            print(f"\nDate: {al['date']}")
            print(f"Title: {al['title']}")
            print(f"Link: {al['link']}")
            print(f"Content: \n{summarize_text(al)}")
        else:
            logging.debug(f"Content is null! while getting contents from {al['link']}")


# main ================================
if __name__ == "__main__":
    logging.basicConfig(filename=sys.argv[0]+".debug", level=logging.DEBUG)
    logging.basicConfig(filename=sys.argv[0]+".error", level=logging.ERROR)

    load_dotenv(dotenv_path="envar.env", override=True)

    args = process_arguments()

    keyword_list = args.keywords
    keywords = '%20'.join(keyword_list)

    days = args.days
    if not days: 
        logging.debug("No days provided. set as default(30 days)")
        days = "30"
    else:
        pass

    search_url = f"https://news.google.com/rss/search?hl=en-US&gl=US&ceid=US%3Aen&q=when%3A{days}d%20{keywords}"

    inputfilename = args.infile
    if inputfilename:
        get_news_summaries_from_csv(inputfilename)
    else:
        get_news_summaries_from_crawling(search_url)
