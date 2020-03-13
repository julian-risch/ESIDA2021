from abc import ABC, abstractmethod
from collections import defaultdict

from bs4 import BeautifulSoup
import requests
from datetime import datetime
from requests.exceptions import HTTPError

import logging

logger = logging.getLogger('scraper')


class Scraper(ABC):
    INTERRUPTION_MODE = True
    logged_urls = {"refused": defaultdict(list), "accepted": defaultdict(list)}

    @classmethod
    def wrapped_scrape(cls, url):
        data = cls._scrape(url)
        data['comments'] = list(sorted(data['comments'], key=lambda c: c['timestamp']))
        cls.print_info(data)
        return data

    @classmethod
    def get_urls_and_flush(cls):
        temp = dict(cls.logged_urls)
        cls.logged_urls = {"refused": defaultdict(list), "accepted": defaultdict(list)}
        return temp

    @classmethod
    def scrape(cls, url):
        if cls.INTERRUPTION_MODE:
            data = cls.wrapped_scrape(url)
        else:
            try:
                data = cls.wrapped_scrape(url)
                cls.logged_urls["accepted"][cls.__name__].append(url)
            except UserWarning:
                data = None
                cls.logged_urls["refused"][cls.__name__].append(url)

        return data

    @classmethod
    def make_comment(cls, cid, user, published, text, reply_to, **kwargs):
        data = {
            'user': user,
            'id': cid,
            'timestamp': cls.dt2str(published),
            'text': text,
            'reply_to': reply_to
        }
        if kwargs:
            for k, v in kwargs.items():
                data[k] = v
        return data

    @classmethod
    def make_article(cls, url, title, summary, author, text, published, **kwargs):
        data = {
            'url': url,
            'title': title,
            'summary': summary,
            'author': author,
            'text': text,
            'published_time': cls.dt2str(published),
            'scrape_time': cls.get_now(),
            'scraper': str(cls),
            'comments': []
        }
        if kwargs:
            for k, v in kwargs.items():
                data[k] = v
        return data

    @staticmethod
    def dt2str(dt):
        return dt.strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def get_now():
        return Scraper.dt2str(datetime.now())

    @classmethod
    def get_html(cls, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            logger.debug('     - Successfully loaded: ' + url)
            return BeautifulSoup(response.text, 'lxml')
        except HTTPError as http_err:
            logger.debug(f'  !!! HTTP error occurred: {http_err}')
        except Exception as err:
            logger.debug(f'  !!! Other error occurred: {err}')
        return None

    @classmethod
    def get_json(cls, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            logger.debug('     - Successfully loaded: ' + url)
            return response.json()
        except HTTPError as http_err:
            logger.debug(f'  !!! HTTP error occurred: {http_err}')
        except Exception as err:
            logger.debug(f'  !!! Other error occurred: {err}')
        return None

    @classmethod
    def post_json(cls, url, data, headers):
        try:
            response = requests.post(url, data=data, headers=headers)
            response.raise_for_status()
            logger.debug('     - Successfully loaded: ' + url)
            return response.json()
        except HTTPError as http_err:
            logger.debug(f'  !!! HTTP error occurred: {http_err}')
        except Exception as err:
            logger.debug(f'  !!! Other error occurred: {err}')
        return None

    @classmethod
    def print_info(cls, article_data):
        logger.debug(f'\n'
                     f'    Title: {article_data["title"]}\n'
                     f'    - Author: {article_data["author"]}\n'
                     f'    - Date: {article_data["published_time"]}\n'
                     f'    - Length: {len(article_data["text"])}\n'
                     f'    - Number of comments: {len(article_data["comments"])}')

    @classmethod
    def test_scraper(cls, test_urls):
        for test_url in test_urls:
            logger.debug(f' TESTING: {test_url}')
            cls.scrape(test_url)

    @staticmethod
    @abstractmethod
    def assert_url(url):
        """
        This function will return true if this scraper can deal with a given URL.
        Recommended implementation will use a regular expression to match appropiate URLs.
        :param url:
        :return: bool
        """
        raise NotImplementedError

    @classmethod
    def _scrape(cls, url):
        """
        This function will return an object in the form of

        ```
        {
           "url": "...",
           "title": "...",
           "published_time": "...",
           "scrape_time": "...",
           "author": "...",
           "text": "...",
           "comments": [ {
              "id": "...",
              "user": "...",
              "timestamp": "...",
              "text": "...",
              "reply_to": "..."       // id of another comment or null
              },              // end comment
              ... ]           // end comments
           }
        ```

        :param url: url to article to scrape
        :return: see above
        """
        raise NotImplementedError


from data.platforms.sz import SueddeutscheScraper
from data.platforms.zon import ZONScraper
from data.platforms.spon import SPONScraper
from data.platforms.welt import WeltScraper
from data.platforms.tagesschau import TagesschauScraper
from data.platforms.faz import FAZScraper
from data.platforms.taz import TAZScraper

__all__ = ['Scraper',
           'SueddeutscheScraper', 'ZONScraper', 'SPONScraper',
           'WeltScraper', 'TagesschauScraper', 'FAZScraper',
           'TAZScraper']
