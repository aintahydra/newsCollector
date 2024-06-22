import sys
import requests
import feedparser
import re
import logging

class NewsCrawler:

    def __init__(self):
        pass

    def remove_tags(self, textwtags):
        tagpattern = re.compile('<.*?>|&nbsp')
        text = re.sub(tagpattern, '', textwtags)
        return text
    
    def getNews(self, url, num=100):
   
        news_list = []
        news_count = 0

        try: 
            res = requests.get(url)
            if res.status_code == 200:
                data_entries = feedparser.parse(res.text).entries
                for entry in data_entries:
                    pubdate = "%4d%02d%02d" % (entry.published_parsed.tm_year, entry.published_parsed.tm_mon, entry.published_parsed.tm_mday)
                    publisher = entry.source.title
                    title = entry.title.split('-')[0]
                    desc = self.remove_tags(entry.summary).split(';')[0]
                    newslink = (requests.get(entry.link)).url
                    content = ""

                    ### Filterout some news sources
                    banned_sources = ['businesswire.com', 'spiceworks.com'] 

                    if any(domain in newslink for domain in banned_sources):
                        logging.debug("Skipping a banned source: {}".format(newslink))
                        pass
                    
                    news_list.append({"date": pubdate, "publisher": publisher, "title": title, "link": newslink, "content": content})#, "content": newscontent)
                    
                    news_count = news_count + 1
                    if (news_count + 1 == num):
                        return news_list
            else:
                logging.debug("HTTP Error")
        except requests.exceptions.RequestException as err:
            logging.debug('Error Requests: {}'.format(err))

        return news_list


# main ================================
if __name__ == "__main__":

    test_keywords = "cybersecurity AI attack".replace(' ', '%20')
    gnews_url = "https://news.google.com/rss/search?hl=en-US&gl=US&ceid=US%3Aen&q=when%3A{days}d%20{keywords}"

    crawler = NewsCrawler()
    
    if len(sys.argv) != 2:
        crawler.getNews(gnews_url.format(keywords=test_keywords, days="30"))
    else:
        kwrds = sys.argv[1].replace(' ', '%20')
        crawler.getNews(gnews_url.format(keywords=kwrds, days="30"))