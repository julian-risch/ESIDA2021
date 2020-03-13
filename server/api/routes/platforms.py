from fastapi import APIRouter, HTTPException, status
from fastapi.responses import PlainTextResponse
from common import init_logging
from pydantic import HttpUrl
from data.models import Article, Comment, ScrapeResultStatus, ScrapeResult, ScrapeResultDetails
from data.scrapers import get_matching_scraper, NoScraperException, ScraperWarning, NoCommentsWarning
from fastapi.responses import JSONResponse
from typing import Union
import data.database as db
import data.models as models
import data.cache as cache
from fastapi import Depends
from requests.exceptions import RequestException
import functools
import json

logger = init_logging('comex.api.route.platforms')
logger.debug('Setup comex.api.route.platforms router')

router = APIRouter()


def catch_scrape_errors(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except NoScraperException as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail=ScrapeResultDetails(status=ScrapeResultStatus.NO_SCRAPER,
                                                           error=str(e)).__dict__)
        except NoCommentsWarning as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail=ScrapeResultDetails(status=ScrapeResultStatus.NO_COMMENTS,
                                                           error=str(e)).__dict__)
        except (RequestException, ScraperWarning) as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail=ScrapeResultDetails(status=ScrapeResultStatus.SCRAPER_ERROR,
                                                           error=str(e)).__dict__)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail=ScrapeResultDetails(status=ScrapeResultStatus.ERROR,
                                                           error=str(e)).__dict__)

    return wrapper


@router.get('/')
@catch_scrape_errors
async def scrape(url: HttpUrl) -> ScrapeResult:
    from_cache, article = cache.get_article(url)
    return ScrapeResult(payload=article)


@router.get('/article', response_class=ScrapeResult)
@catch_scrape_errors
async def get_article(url: HttpUrl):
    article = await cache.get_article(url)
    result = ScrapeResult(payload=article)
    print(1)
    return result
