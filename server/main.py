#!/usr/bin/env python3

from api import Server
from common import init_logging
from data.database import init_db
import logging

logger = logging.getLogger('main')

if __name__ == '__main__':
    init_logging()
    server = Server()
    init_db(server.app)
