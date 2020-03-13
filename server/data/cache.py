import sqlite3 as sqlite
from common import config


def ensure_connection(f):
    def wrapper(self, *args, **kwargs):
        self.connection = sqlite.connect(self.DB_FILE)
        self.cursor = self.connection.cursor()
        f(self, *args, **kwargs)
        self.connection.commit()
        self.connection.close()

    return wrapper


class Cache:
    """
    # connector to a sqlite database used to cache already queried comments
    # also stores the generated model
    # must have capability to reset for a story
    """

    def __init__(self):
        self.connection = None
        self.cursor = None

    @property
    def DB_FILE(self):
        return config['cache']['db_file']

    def tmp(self):
        pass

    @ensure_connection
    def _ensure_db(self):
        try:
            # tables exists, nothing to do
            self.cursor.execute('SELECT * FROM articles')
        except sqlite.Error:
            # tables do not exist, create them
            self.cursor.execute('CREATE TABLE cars (\
                    id text,\
                    make text,\
                    model text,\
                    year text,\
                    trans text,\
                    color text)')


__all__ = ['Cache']
