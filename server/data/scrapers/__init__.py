from abc import ABC, abstractmethod
from collections import defaultdict

from bs4 import BeautifulSoup
import requests
from datetime import datetime
from requests.exceptions import HTTPError
import data.models as models
from typing import Tuple, List

import logging

logger = logging.getLogger('scraper')


class NoScraperException(Exception):
    pass


class ScraperWarning(UserWarning):
    pass


class NoCommentsWarning(ScraperWarning):
    pass


class UnknownStructureWarning(ScraperWarning):
    pass


class Scraper(ABC):
    @classmethod
    def scrape(cls, url) -> Tuple[models.ArticleScraped, List[models.CommentScraped]]:
        article, comments = cls._scrape(url)
        comments = list(sorted(comments, key=lambda c: c.timestamp))

        logger.debug(f'Scraped: "{article.title}" using "{article.scraper}" for {article.url}')
        logger.debug(
            f'  - Length: {len(article.text)} | num comments: {len(comments)} | Date: {article.published_time} | Author: {article.author}\n')

        if len(comments) == 0:
            raise NoCommentsWarning(f'No Comments found at {url}!')

        return article, comments

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
    def get_json(cls, url, params=None):
        try:
            response = requests.get(url, params=params)
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
    def test_scraper(cls, test_urls):
        for test_url in test_urls:
            logger.debug(f' TESTING: {test_url}')
            cls.scrape(test_url)

    @staticmethod
    @abstractmethod
    def assert_url(url) -> bool:
        """
        This function will return true if this scraper can deal with a given URL.
        Recommended implementation will use a regular expression to match appropiate URLs.
        :param url:
        :return: bool
        """
        raise NotImplementedError

    @classmethod
    def _scrape(cls, url) -> Tuple[models.ArticleScraped, List[models.CommentScraped]]:
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


from data.scrapers.sz import SueddeutscheScraper
from data.scrapers.zon import ZONScraper
from data.scrapers.spon import SPONScraper
from data.scrapers.welt import WeltScraper
from data.scrapers.tagesschau import TagesschauScraper
from data.scrapers.faz import FAZScraper
from data.scrapers.taz import TAZScraper

SCRAPERS = [
    SueddeutscheScraper,
    ZONScraper,
    WeltScraper,
    TagesschauScraper,
    FAZScraper,
    SPONScraper,
    TAZScraper
]


def get_matching_scraper(url):
    for scraper in SCRAPERS:
        if scraper.assert_url(url):
            logger.debug(f'Using scraper {scraper} for {url}')
            return scraper
    raise NoScraperException(f'No matching scraper for: {url}')


def scrape(url: str) -> Tuple[models.ArticleScraped, List[models.CommentScraped]]:
    scraper = get_matching_scraper(url)
    article, comments = scraper.scrape(url)
    return article, comments


__all__ = ['Scraper', 'SCRAPERS', 'scrape', 'get_matching_scraper', 'NoScraperException',
           'ScraperWarning', 'NoCommentsWarning', 'UnknownStructureWarning']
