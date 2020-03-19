import argparse
import json
import os
import hashlib
import time
from collections import defaultdict
from typing import Dict, Any
from fastapi.testclient import TestClient
from server.main import run
from urllib.parse import quote
import data.models as models
import pytest
import requests

# server = run(['--config', 'configs/testing.ini'])
# client = TestClient(server.app)

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('-f', type=str, dest='collection_folder', default=None,
                    help='Folder of files with lists of URLs to scrape')
parser.add_argument('-c', type=str, dest='collection', default=None,
                    help='File with list of all URLs to scrape')
parser.add_argument('-u', type=str, dest='base_url', default='http://0.0.0.0:9080',
                    help='File with list of all URLs to scrape')
args = parser.parse_args()


def process_collections_file(file):
    with open(file, 'r') as f:
        for line in f:
            line = line.strip()
            if line[0] == '-':
                yield line[1:].strip()


def process_collections_folder(folder):
    for f in os.listdir(folder):
        yield from process_collections_file(os.path.join(folder, f))


if __name__ == '__main__':
    urls = []
    if args.collection:
        urls = process_collections_file(args.collection)
    elif args.collection_folder:
        urls = process_collections_folder(args.collection_folder)
    else:
        print('No collection source given!')
        exit(1)

    for url in urls:
        # response = client.get(f'/api/platforms/article?url={quote(url)}')
        response = requests.get(f'{args.base_url}/api/platforms/article?url={quote(url)}')

        try:
            print(f"{response.status_code} {response.json()['detail']['status']} for {url}")
        except Exception as e:
            print(f'ERROR: {e} for {url}')
