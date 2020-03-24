from fastapi import APIRouter, HTTPException, status
from common import init_logging, except2str
from pydantic import HttpUrl
from data.models import Graph, ComparatorConfig
import data.models as m
from typing import List, Optional
import data.cache as cache
import functools

logger = init_logging('comex.api.route.graph')
logger.debug('Setup comex.api.route.graph router')

router = APIRouter()


def catch_errors(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail=except2str(e, logger))

    return wrapper


@router.post('/', response_model=Graph)
@catch_errors
async def get_graph(article_ids: List[int] = None,
                    urls: List[HttpUrl] = None,
                    override_cache: bool = False, ignore_cache: bool = False,
                    conf: ComparatorConfig = None):
    if conf is not None:
        conf = conf.dict(exclude_unset=True)
        logger.debug(f'Graph request included config: {conf}')
    graph = await cache.get_graph(urls=urls, article_ids=article_ids, conf=conf,
                                  override_cache=override_cache, ignore_cache=ignore_cache)
    return graph
