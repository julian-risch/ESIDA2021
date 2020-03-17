from fastapi.testclient import TestClient
from server.main import run
from urllib.parse import quote
import data.models as models
import pytest

server = run(['--config', 'configs/testing.ini'])

client = TestClient(server.app)


def _test_platform(urls):
    for url in urls:
        response = client.get(f'/api/platforms/scrape?url={quote(url)}')
        assert response.status_code == 200
        assert response.json()['details']['status'] == models.ScrapeResultStatus.OK


def test_faz():
    _test_platform([
        'https://www.faz.net/aktuell/wirtschaft/mittelstand/bonpflicht-duerfte-thema-im-koalitionsausschuss-werden-16603306.html'
    ])


def test_spon():
    _test_platform([
        'https://www.spiegel.de/panorama/schleswig-holstein-untersagt-touristen-zutritt-a-3ed8bc38-f81d-42fa-8b19-4ce585e9fae9#kommentare'
    ])


def test_sz():
    _test_platform([
        'https://www.sueddeutsche.de/bayern/kommunalwahl-bayern-diskussion-leserdiskussion-meinung-1.4845541',
        'https://www.spiegel.de/wirtschaft/unternehmen/corona-krise-daimler-setzt-produktion-in-europaeischen-werken-aus-a-29204fd5-0424-4a22-a06d-e351fc407d8c',
        'https://www.spiegel.de/wissenschaft/medizin/coronavirus-warum-landen-noch-flugzeuge-aus-iran-in-deutschland-a-cc762322-1533-4bdb-9bfe-f4a9e59dd7ac'
    ])


def test_tagesschau():
    _test_platform([

    ])


def test_taz():
    _test_platform([

    ])


def test_welt():
    _test_platform([

    ])


def test_zon():
    _test_platform([

    ])
