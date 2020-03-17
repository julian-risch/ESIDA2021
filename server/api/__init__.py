from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from common import config, get_logger_config
from api.routes import ping, platforms
import uvicorn
import json
import resource
import time
import logging

logger = logging.getLogger('comex.api.server')


class APISubRouter:
    def __init__(self):
        self.router = APIRouter()
        self.paths = {
            '/ping': ping,
            '/platforms': platforms
        }
        for path, router in self.paths.items():
            self.router.include_router(router.router, prefix=path)


class Server:
    def __init__(self):
        self.app = FastAPI()

        logger.debug('Setup Middlewares')
        trusted_hosts = json.loads(config.get('server', 'hosts'))
        if config.getboolean('server', 'header_trusted_host'):
            self.app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)
        if config.getboolean('server', 'header_cors'):
            self.app.add_middleware(CORSMiddleware, allow_origins=trusted_hosts,
                                    allow_methods=['GET', 'POST', 'DELETE'])
        self.app.add_middleware(GZipMiddleware, minimum_size=1000)
        self.app.add_middleware(TimingMiddleware)

        logger.debug('Setup routers')
        self.api_router = APISubRouter()
        self.app.include_router(self.api_router.router, prefix='/api')

        self.app.mount('/', StaticFiles(directory='../frontend', html=True), name='static')

        uvicorn.run(self.app, host=config.get('server', 'host'), port=config.getint('server', 'port'),
                    log_config=get_logger_config())


class TimingMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.time()
        start_cpu_time = self._get_cpu_time()

        response = await call_next(request)

        used_cpu_time = self._get_cpu_time() - start_cpu_time
        used_time = time.time() - start_time

        response.headers['X-CPU-Time'] = f'{used_cpu_time:.8f}s'
        response.headers['X-WallTime'] = f'{used_time:.8f}s'

        request.scope['timing_stats'] = {
            'cpu_time': f'{used_cpu_time:.8f}s',
            'wall_time': f'{used_time:.8f}s'
        }

        return response

    @staticmethod
    def _get_cpu_time():
        resources = resource.getrusage(resource.RUSAGE_SELF)
        # add up user time (ru_utime) and system time (ru_stime)
        return resources[0] + resources[1]
