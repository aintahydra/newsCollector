# Requirements
# - !pip install beautifulsoup4 requests openai tiktoken --upgrade
#
# How to run
# $ python3 sys.argv[0] ai cyber attack --days 15 > output.txt

# search for 'null' in the .debug file for checking in there are sources being reported their contents 'null'

import openai
import os
import json
import argparse
import sys
import logging
from google_news_crawler import NewsCrawler as GNewsCrawler
from fetcher_selenium import Fetcher as SeleniumFetcher

def OpenAI_news_bot(messages, temperature=0.1, max_tokens=1024):
    client = openai.OpenAI()

    result = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    return result.choices[0].message

def process_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('keywords', metavar='keywords', type=str, nargs='+',
                        default=[], help='a list of search keywords (optional)') 
    parser.add_argument('--days', dest='days', type=str, nargs='?',
                        help='seach for articles published within given days (optional)')
    return parser.parse_args()


def start():
     
    os.environ['OPENAI_API_KEY']="..." #fill out the key

    args = process_arguments()

    keyword_list = args.keywords
    keywords = '%20'.join(keyword_list)

    days = args.days
    if not days: 
        logging.debug("No days provided. set as default(30 days)")
        days = "30"

    search_url = f"https://news.google.com/rss/search?hl=en-US&gl=US&ceid=US%3Aen&q=when%3A{days}d%20{keywords}"

    # Get Google news articles regarding the input keywords
    # -----------------
    crawler = GNewsCrawler()
    article_list = crawler.getNews(search_url)

    # Now feed up the "content" keys in the above JSON list
    # -----------------
    fetcher = SeleniumFetcher()

    for i, al in enumerate(article_list):
        #print(f"DEBUG>> article link {i}: {al['link']}")
        content = fetcher.getContents(al['link'])
        if content:
           al['content'] = content
        else:
            logging.debug("DEBUG>> no content obtained at {}".format(al['link']))

    # News is ready, Toss to OpenAI and get JSON output
    # -----------------

    # for JSON output 
    print("{")
    print(f"\'query\': {keywords}")
    print(f"\'days\': {days}")
    print(f"\'searchURL\': {search_url}")
    print(f"\'newsList\': [")

    num_news = len(article_list)
    ever_printed = 0
    for i, al in enumerate(article_list): 


        #print("\n===============================")

        if al['content'] : 
            
            result = OpenAI_news_bot([
            #print(json.dumps(n, indent=4))
            #result = OpenAI_news_bot_stream([
                {
                    "role": "user",
                    # ############################################## TXT output ################################################
                    # "content": "Summarize the following news articles about " + keywords + ". The summary should be a bulleted list of sentences. \
                    # Note that the output should be formatted as below, including Korean-traslated versions of the title and the summary. \
                    # --- \n \
                    # date: \n \
                    # publisher: \n \
                    # title: \n \
                    # link to the source article: \n \
                    # content Summary: \n \
                    #   - \
                    #   - \
                    #   - ...\
                    # - Title(in Korean): \n \
                    # - Content Summary(in Korean): \n \
                    #   - \
                    #   - \
                    #   - ...\
                    # \n --- \n"
                    # ############################################## JSON output ################################################
                    "content": "Summarize the following news articles about " + keywords + ". The summary should be a bulleted list of sentences. \
                    The output should be formatted as below. The \'link\' is the URL to the original news article, \'titleKor\' is the Korean-translated \
                    version of \'title\'. \'summaryStatementsKor\' is the Korean-translated version of \'summaryStatementsKor\' \
                    ---json \n \
                    {  \
                        \"date\":  \
                        \"link\":  \
                        \"publisher\": \
                        \"title\":  \
                        \"summaryStatements\": [ \
                            \"\", \
                            \"\", \
                            \"\", \
                            ...\
                        ], \
                        \"titleKor\":  \
                        \"summaryStatementsKor\": [ \
                            \"\", \
                            \"\", \
                            \"\", \
                            ... \
                        ], \
                    } \
                    \n --- \n"
                },
                {
                    "role": "user",
                    "content": json.dumps(al, indent=4)
                }
            ],
                max_tokens=2000)

            # No streaming
            # for JSON output -- part(2/3)
            #print(f"\"{keywords}{i}\":")
            # if (i+1 == num_news):
            #     print(f"{result.content}")
            # else:
            #     print(f"{result.content},")
            if ever_printed:
                print(f", {result.content}")
            else: 
                ever_printed = 1
                print(f"{result.content}")
        else:
            logging.debug(f"Content is null! while getting contents from {al['link']}")
    
    # for JSON output -- part(3/3)
    print("]}")

# main ================================
if __name__ == "__main__":
    logging.basicConfig(filename=sys.argv[0]+".debug", level=logging.DEBUG)
    logging.basicConfig(filename=sys.argv[0]+".error", level=logging.ERROR)
    #logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    start()


# Expected JSON ouptput format
# {
#     "query": "XXXX",
#     "days": "XX",
#     "searchURL": "",
#     "newsList": [
#         {
#             "date": "",
#             "publisher": "",
#             "title": "",
#             "link": "",
#             "summaryStatements": [
#                 "",
#                 "",
#                 "",
#                 "",
#             "titleKorean": ""
#             "summaryStatementsKorean": [
#                 "",
#                 "",
#                 "",
#                 "",
#             ]
#         }
#     ]
    
# }
