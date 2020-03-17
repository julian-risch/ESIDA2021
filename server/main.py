#!/usr/bin/env python3

from common import init_logging, init_config


def run(args=None):
    init_config(args)

    from data.database import init_db
    from api import Server

    init_logging()
    server = Server()
    init_db(server.app)

    return server


if __name__ == '__main__':
    run()
