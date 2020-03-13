import re
from data.scrapers import Scraper
from datetime import datetime, timedelta
import logging
import data.models as models

logger = logging.getLogger('scraper')


class ZONScraper(Scraper):
    @staticmethod
    def assert_url(url):
        return re.match(r'(https?://)?(www\.)?zeit\.de/.*', url)

    @classmethod
    def _scrape(cls, url):
        bs = cls.get_html(url + '?sort=desc')
        article_data = cls.scrape_article(bs, url)
        article_data['comments'] = cls.scrape_comments(bs, url)
        if len(article_data['comments']) == 0:
            raise UserWarning('No Comments found!')
        return article_data

    @classmethod
    def scrape_article(cls, bs, url):
        article_parts = bs.select('article section h2, article section p')
        if not article_parts:
            article_parts = bs.select('article p.paragraph')

        return cls.make_article(
            url=url,
            title=bs.select('article header h1')[0].get_text().strip(),
            summary=bs.select('article header div.summary')[0].get_text().strip(),
            author=cls._scrape_author(bs),
            text='\n\n'.join([e.get_text().strip() for e in article_parts]),
            published=datetime.strptime(bs.select('article header time')[0]['datetime'], '%Y-%m-%dT%H:%M:%S%z')
        )

    @staticmethod
    def _scrape_author(bs):
        author = ', '.join([e.get_text().strip() for e in bs.select('article header div.byline [itemprop="name"]')])
        if not author:
            author = bs.select('a[rel="author"] span[itemprop="name"]')
        if not author:
            author = bs.select('span.metadata__source')
        if not author:
            return None
        if not isinstance(author, str):
            author = author[0].get_text().replace('Quelle: ', '').strip()

        return author

    @classmethod
    def scrape_comments(cls, bs, url):
        page_url_stack = set()
        resolved_urls = [url + '?sort=desc#comments']
        resolved_urls = set(resolved_urls)
        comments = []

        while True:
            # get direct comments
            for e in bs.select('#comments article'):
                comments.append(cls.parse_comment(e))

            # get async load comments
            for nested in bs.select('#comments div.comment-section__body > div.comment__container a'):
                bss = Scraper.get_html(nested['data-url'])
                for e in bss.select('article'):
                    comments.append(cls.parse_comment(e))

            # get pagination
            for e in bs.select('ul.pager__pages li a'):
                page_url_stack.add(e['href'])
            page_url_stack = page_url_stack.difference(resolved_urls)

            # am I done?
            if len(page_url_stack) == 0:
                break

            # load next comment page
            next_url = page_url_stack.pop()
            resolved_urls.add(next_url)
            bs = cls.get_html(next_url)

        return comments

    @classmethod
    def parse_comment(cls, e):
        user_name = None
        try:
            author = e.select('div.comment-meta__name a')[0]
            user_id = author['href']
        except IndexError:
            author = e.select('div.comment-meta__name')
            if author is None or len(author) == 0:
                user_name = ""
            else:
                author = author[0]
                user_name = author.get_text().strip()
            user_id = None

        reply_to = e.select('div.comment__reactions a.comment__origin')
        if reply_to:
            reply_to = reply_to[0]['href'].split('#')[-1]
        else:
            reply_to = None

        return cls.make_comment(
            cid=e['id'],
            user=user_name,
            published=cls.parse_date(e.select('.comment-meta__date')[0].get_text()),
            text='\n\n'.join([ei.get_text().strip() for ei in e.select('div.comment__body p')]),
            reply_to=reply_to,
            user_id=user_id,
            leseempfehlungen=int(e.select('.js-comment-recommendations')[0].get_text().strip())
        )

    @classmethod
    def parse_date(cls, s):
        try:
            # Example: "#1  —  20. November 2017, 9:51 Uhr"

            # maybe de_DE locale is not installed on system, replace month names
            for de, en in [('Januar', 'January'), ('Februar', 'February'), ('März', 'March'),  # ('April', 'April'),
                           ('Mai', 'May'), ('Juni', 'June'), ('Juli', 'July'),
                           # ('August', 'August'), ('September', 'September'),
                           ('Oktober', 'October'),  # ('November', 'November')
                           ('Dezember', 'December')]:
                s = s.replace(de, en)
            return datetime.strptime(s.split('—')[1].strip(), '%d. %B %Y, %H:%M Uhr')
        except ValueError or IndexError:
            # Example: "#17  —  vor 2 Wochen"
            parts = s.split('vor')[-1].strip().split()
            offset = int(parts[0])
            dimension = parts[1]

            if dimension == 'Stunden':
                delta = timedelta(hours=offset)
            elif dimension == 'Minuten':
                delta = timedelta(minutes=offset)
            elif dimension == 'Tage':
                delta = timedelta(days=offset)
            else:
                delta = timedelta()
            return datetime.now() - delta


if __name__ == '__main__':
    Scraper.LOG_REQUESTS = True
    Scraper.LOG_INFO = True
    ZONScraper.test_scraper([
        'https://www.zeit.de/wissen/2020-01/buschfeuer-australien-waldbraende-buschbraende-region-duerre-3',
        'https://www.zeit.de/wirtschaft/2017-11/weltklimakonferenz-bonn-naivitaet-politik-5vor8',
        'https://zeit.de/zeit-geschichte/2017/04/orientalismus-kino-hollywood-georg-seesslen',
        'https://www.zeit.de/kultur/film/2019-10/preis-der-freiheit-zdf-dreiteiler-ddr-rezension/komplettansicht',
        'https://www.zeit.de/politik/ausland/2019-11/brexit-grossbritannien-boris-johnson-deutsche-wirtschaft-jeremy-corbyn',
        'https://www.zeit.de/politik/deutschland/2019-11/annegret-kramp-karrenbauer-cdu-parteitag-gegner'
    ])
