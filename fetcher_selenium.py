import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support import expected_conditions as EC
import time # occasionally needed
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re

class Fetcher:

    def __init__(self):
        pass

    def refine(self, text):
        text= text.replace('\xa0','') # remove useless unicode characters

        for _ in range(10):
            text=text.replace('\n\n','\n').replace('  ',' ') # remove multiple \n
        return text
    
    #Collects all text from children p tags of the given parent_tag
    # the following function works in the context of beautifulsoup
    def collect_content(self, parent_tag):
        content = ''
        for tag in parent_tag:
            p_tags = tag.find_all('p')
            for tag in p_tags:
                content += tag.text + '\n'
        return content
    
    def collect_text(self, parent_tag):
        content = ''
        content = parent_tag.get_text(strip=True)
        return content

    def process_with_soup(self, url, html):
        soup = BeautifulSoup(html, 'html.parser')

        domain_str = urlparse(url).netloc

        # patterns obtined from frequently appeared sources
        # RegExes below are supposed to be obtained from the 'class=...' property
        domain_class_mapping = {
            "apnews.com": [re.compile(r'^RichTextStoryBody')],
            "axios.com": [re.compile(r'^DraftjsBlocks')],
            "bbc.com": ['article'],
            "blog.checkpoint.com": ['div.container'],
            "darkreading.com": [re.compile(r'^ContentText'), 'span.ContentText', 'div.ContentModule-Wrapper'],
            "edition.cnn.com": ['div.video-resource__description'],
            "enisa.europa.eu": ['div.content-body'],
            "federalnewsnetwork.com": [re.compile(r'^Entry-content')],
            "findbiometrics.com": ['div.entry-content'],
            "foxnews.com": ['div.paywall'],
            "forbes.com": [re.compile(r'^article-body')],
            "iapp.org": [re.compile(r'^Article-Body')],
            "infosecurity-magazine.com": ['div.content-module'],
            "justice.gov": [re.compile(r'field-formatter--text-default'), 'div.node-body'],
            "ncsc.gov.uk": ['div.pcf-articleWrapper', 'div.pcf-BodyText'],
            "niccs.cisa.gov": [re.compile(r'field--name-body')], 
            "nist.gov": ['div.text-with-summary'],
            "nsa.gov": ['div.body'], 
            "nytimes.com": ['div.css-53u6y8'],
            "reuters.com": ['div.text__text', re.compile(r'^text__text')],
            "rstreet.org": [re.compile(r'^post-')],
            "scmagazine.com": ['div.GuttenbergBlockFactory_wrapper__AcvAp'],
            "securityintelligence.com": ['div.grid__content.post', re.compile(r'post__content')],
            "spiceworks.com": ['div.gp-entry-text'],
            "state.gov": ['div.wp-block-paragraph'],
            "techtarget.com": ['div.content-center', 'section#content-body', re.compile(r'^content-body')],
            "thehackernews.com": [re.compile(r'^articlebody'), 'div.articlebody'],
            "thehill.com": [re.compile(r'^article__text')],
            "theguardian.com": ['div.dcr-ch7w1w'],
            "therecord.media": ['div.article__content', 'span.wysiwyg-parsed-content', re.compile(r'wysiwyg-parsed-content')],
            "theregister.com": ['div#body'],
            "thomsonreuters.com": ['div.article-body', re.compile(r'^article-content')],
            "tripwire.com": [re.compile(r'^field')],
            "wiley.law": ['div#itemContent'],
            "washingtontechnology.com": [re.compile(r'^content-body')],
        } 

        # customized processing for the above sources
        for domain, selectors in domain_class_mapping.items():
            if domain in domain_str:
                for selector in selectors:
                    if isinstance(selector, re.Pattern):
                        elems = soup.find_all(class_=selector)
                    else:
                        elems = soup.select(selector)
                    cont = []
                    for elem in elems:
                        cont.append(elem.get_text(strip=True))
                        return cont

        # is still no content obtained
        div_tags = soup.find_all('div', id='articleContentBody')
        div_tags_2 = soup.find_all('div', class_='ArticleText')
        div_tags_3 = soup.find_all('div', id='ArticleText')
        div_tags_4 = soup.find_all('div', id='article')
        div3 = soup.find_all('div', id='article_content')
        div4 = soup.find_all('div', class_='articleBodyText')
        div5 = soup.find_all('div', class_='story-container')
        div_tags_l = soup.find_all('div', id=re.compile('article'))
        div7 = soup.find_all('div', class_='main-text')
        div8 = soup.find_all('div', id='content')
        rest = soup.find_all(id='articleText')

        if div_tags:
            return self.collect_content(div_tags)
        elif div_tags_2:
            return self.collect_content(div_tags_2)
        elif div_tags_3:
            return self.collect_content(div_tags_3)
        elif div_tags_4:
            return self.collect_content(div_tags_4)
        elif div3:
            return self.collect_content(div3)
        elif div4:
            return self.collect_content(div4)
        elif div5:
            return self.collect_content(div5)
        elif div_tags_l and len(self.collect_content(div_tags_l)) > 0:
            return self.collect_content(div_tags_l)
        elif div7:
            return self.collect_content(div7)
        elif div8:
            return self.collect_content(div8)
        elif rest:
            return self.collect_content(rest)
        else:
            # contingency
            c_list = [v.text for v in soup.find_all('p') if len(v.text) > 0]
            words_to_bans = ['<', 'javascript']
            for word_to_ban in words_to_bans:
                c_list = list(filter(lambda x: word_to_ban not in x.lower(), c_list))
            clean_html_ratio_letters_length = 0.33
            c_list = [t for t in c_list if
                    len(re.findall('[a-z]', t.lower())) / (
                            len(t) + 1) < clean_html_ratio_letters_length]
            content = ' '.join(c_list)
            content = content.replace('\n', ' ')
            content = re.sub('\s\s+', ' ', content)  # remove multiple spaces.
        return content

    def getContents(self, url):
        option = ChromeOptions()
        option.add_argument('--user-data-dir=temp_chrome_data')
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=option)
        driver.get(url)
        #driver.save_screenshot('screen_now.png')

        ##NOTE: when stucked by the CloudFlare anti-bot, 
        ##      (1) uncomment the following sleep statement
        ##      (2) when selenium opens Chrome, you manually open another tab and then manually access troublesome URLS (ex, darkreading.com)
        ## The above assumes that (A) "--user-data-dir" is set for storing cookies 
        ##
        #time.sleep(20)

        content = []

        # finding elements examples
        #     #p_elems = driver.find_elements(By.TAG_NAME, 'p')
        #     #d_elems = driver.find_elements(By.CSS_SELECTOR, "[data-testid='content-text']")
        #     #d_elems = driver.find_element(By.CSS_SELECTOR, ".ContentParagraph")
        #     #h_elems = driver.find_element(By.CSS_SELECTOR, "div[class^='articlebody']")
        #     #d_elems = driver.find_element(By.XPATH, "//*[starts-with(@class='ContentText')]")
        #     #p_elems = driver.find_elements(By.XPATH, "//span[starts-with(@class='ContentText')]")

        # error page handling examples 
        #     # if EC.title_contains("Just a moment"):
        #     #     print("Filtered by the CloudFlare Anti-bot...")
        #     pass

        html = driver.page_source
        content = self.process_with_soup(url, html)

        return content

# main ================================

test_urls = [
    "https://www.darkreading.com/cloud-security/critical-bugs-hugging-face-ai-platform-pickle",
    "https://thehackernews.com/2024/05/experts-find-flaw-in-replicate-ai.html"
]

if __name__ == "__main__":

    fetcher = Fetcher()

    if len(sys.argv) != 2:
        for url in test_urls:
            print("======== Visiting:", url)
            print(fetcher.getContents(url))
            print("========")
    else:
        print(fetcher.getContents(sys.argv[1]))





















