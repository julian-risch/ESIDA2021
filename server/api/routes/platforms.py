from fastapi import APIRouter, HTTPException, status
from fastapi.responses import PlainTextResponse
from common import init_logging
from pydantic import HttpUrl
from data.models import Article, Comment, ScrapeResultStatus, ScrapeResult
from data.platforms import SueddeutscheScraper, ZONScraper, SPONScraper, \
    WeltScraper, TagesschauScraper, FAZScraper, TAZScraper
from fastapi.responses import JSONResponse
from typing import Union

logger = init_logging('comex.api.route.platforms')
logger.debug('Setup comex.api.route.platforms router')
router = APIRouter()

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
            return scraper


@router.post('/')
async def scrape(url: HttpUrl) -> ScrapeResult:
    scraper = get_matching_scraper(url)
    try:
        article_data = scraper.scrape(url)
        return ScrapeResult(payload=article_data)
    except UserWarning:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=ScrapeResultStatus.NO_COMMENTS)
    ##except:  # TODO replace with something specific from requests lib
     #   raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=ScrapeResultStatus.ERROR)
