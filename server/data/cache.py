from common import config
import data.database as db
import data.models as models
from fastapi import Depends
from typing import Union, Optional, Tuple, List
from data.scrapers import get_matching_scraper, NoScraperException, ScraperWarning, NoCommentsWarning
import logging

logger = logging.getLogger('data.cache')


def create_comment(_db: db.Session):
    pass


async def get_article(url: str, override_cache=False, ignore_cache=False):
    # try cache if not ignored or overridden
    try:
        if not override_cache and not ignore_cache:
            article = await db.get_article_with_comments(url=url)
            logger.debug(f'Found cache entry id:{article.id} for {url}')
            return article
    except AssertionError:
        # nothing cached for given URL
        logger.debug(f'No cache entry for {url}')

    scraper = get_matching_scraper(url)
    article, comments = scraper.scrape(url)

    # check if scraping was successful
    assert article and comments

    article_id = await db.insert_article(article)
    await db.insert_comments(comments, article_id)

    return await db.get_article_with_comments(url=url)
