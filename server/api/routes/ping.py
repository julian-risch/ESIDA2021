from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from common import init_logging

logger = init_logging('comex.api.route.ping')
router = APIRouter()

logger.debug('Setup comex.api.route.ping router')


@router.get('/', response_class=PlainTextResponse)
async def _pong():
    logger.debug('ping test DEBUG log')
    logger.info('ping test INFO log')
    logger.warning('ping test WARNING log')
    logger.error('ping test ERROR log')
    logger.fatal('ping test FATAL log')
    return 'pong'


@router.post('/{name}', response_class=PlainTextResponse)
async def _ping(name: str) -> str:
    return f'Hello {name}'
