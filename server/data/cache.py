from common import config
import data.database as db
import data.models as models
from fastapi import Depends
from typing import Union, Optional, Tuple, List

from data.scrapers import scrape, prepare_url, get_matching_scraper, \
    NoScraperException, ScraperWarning, NoCommentsWarning
from data.processors.graph import GraphRepresentation
# from data.processors.graph_testing import GraphRepresentation
import logging

logger = logging.getLogger('data.cache')


async def get_graph(urls: List[str] = None, article_ids: List[int] = None, conf: dict = None,
                    override_cache: bool = False, ignore_cache: bool = False) -> models.Graph:
    if urls:
        article_ids = [await db.get_article_id(url) for url in urls]

    if not ignore_cache and not override_cache:
        graph = await db.get_graph(article_ids)
        if graph:
            logger.debug(f'Found graph cache entry with {len(graph.edges)} edges '
                         f'for article_ids: {article_ids} | urls: {urls}')
            return graph
        else:
            logger.debug(f'No cached graph found for article_ids: {article_ids} | urls: {urls}')
    else:
        logger.debug('Ignoring cache for graph request.')

    comments = await db.get_comments(article_ids)
    graph_rep = GraphRepresentation(comments, conf=conf)
    graph = models.Graph(**graph_rep.__dict__())

    logger.debug(f'Constructed graph with {len(graph.edges)} edges '
                 f'for article_ids: {article_ids} | urls: {urls}')

    if not ignore_cache:
        graph_id = await db.store_graph(article_ids, graph)
        graph.graph_id = graph_id
        graph.article_ids = article_ids

    return graph


async def get_stored_article(article_id: int):
    return await db.get_article_with_comments(article_id=article_id)


async def get_article(url: str, override_cache=False, ignore_cache=False):
    url = prepare_url(url)
    try:
        # try cache if not ignored or overridden
        if not override_cache and not ignore_cache:
            article = await db.get_article_with_comments(url=url)
            logger.debug(f'Found cache entry id: {article.id} for {url}')
            return article
    except AssertionError:
        # nothing cached for given URL
        logger.debug(f'No cache entry for {url}')

    article, comments = scrape(url)

    # check if scraping was successful
    assert article and comments

    # FIXME ignore_cache not implemented

    if override_cache:
        await db.delete_article(url=url, recursive=True)

    article_id = await db.insert_article(article)
    await db.insert_comments(comments, article_id)

    return await db.get_article_with_comments(url=url)
