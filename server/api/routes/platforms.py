from fastapi import APIRouter, HTTPException, status
from common import init_logging, except2str
from pydantic import HttpUrl
from data.models import CommentedArticle, ScrapeResultStatus, ScrapeResult, ScrapeResultDetails, CacheResult
from data.scrapers import scrape, NoScraperException, ScraperWarning, NoCommentsWarning
import data.cache as cache
from requests.exceptions import RequestException
import functools

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
                                                           error=except2str(e, logger)).__dict__)
        except NoCommentsWarning as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail=ScrapeResultDetails(status=ScrapeResultStatus.NO_COMMENTS,
                                                           error=except2str(e, logger)).__dict__)
        except (RequestException, ScraperWarning) as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail=ScrapeResultDetails(status=ScrapeResultStatus.SCRAPER_ERROR,
                                                           error=except2str(e, logger)).__dict__)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail=ScrapeResultDetails(status=ScrapeResultStatus.ERROR,
                                                           error=except2str(e, logger)).__dict__)

    return wrapper


@router.get('/scrape', response_model=ScrapeResult)
@catch_scrape_errors
async def direct_scrape(url: HttpUrl):
    article, comments = scrape(url)
    article = CommentedArticle(**article.dict(), comments=comments)
    return ScrapeResult(payload=article)


@router.get('/article', response_model=CacheResult,
            description='Try to get the article from the cache, '
                        'otherwise scrape, cache, and return article including comments.')
@catch_scrape_errors
# FIXME cache override and ignoring shouldn't be exposed!
async def get_article(url: HttpUrl, override_cache: bool = False, ignore_cache: bool = False):
    article = await cache.get_article(url, override_cache, ignore_cache)
    result = CacheResult(payload=article)
    return result
