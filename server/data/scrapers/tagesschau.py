import re
from data.scrapers import Scraper, NoCommentsWarning
from datetime import datetime
import logging
import data.models as models

logger = logging.getLogger('scraper')


class TagesschauScraper(Scraper):
    @staticmethod
    def assert_url(url):
        return re.match(r'(https?://)?(www\.)?tagesschau\.de/.*', url)

    @classmethod
    def _scrape(cls, url):
        bs = cls.get_html(url)
        article = cls._scrape_article(bs, url)

        try:
            meta_url = bs.select('div.modConComments h3.headline a')[0]['href']
            comments = cls._scrape_comments(meta_url)
        except IndexError:
            raise NoCommentsWarning('No Comments found!')

        return article, comments

    @classmethod
    def _scrape_author(cls, bs):
        author = bs.select('div.sectionZ div.modParagraph p.autorenzeile')
        if author:
            return author[0].get_text().replace('Von ', '').split(',')[0]
        logger.debug('WARN: no author found!')
        return None

    @classmethod
    def _scrape_article(cls, bs, url):
        texte = bs.select('div.sectionZ div.modParagraph>p, div.sectionZ div.modParagraph>h2')

        article = models.ArticleBase(
            url=url,
            title=bs.select('div.meldungHead h1 span.headline')[0].get_text().strip(),
            subtitle=bs.select('div.meldungHead h1 span.dachzeile')[0].get_text().strip(),
            summary=texte[0].get_text().strip(),
            author=cls._scrape_author(bs),
            text='\n\n'.join([e.get_text().strip() for e in texte[2:]]),
            published_time=datetime.strptime(bs.select('div.meldungHead span.stand')[0].get_text().strip(),
                                             'Stand: %d.%m.%Y %H:%M Uhr'),
            scraper=str(cls))

        return article

    @classmethod
    def _scrape_comments(cls, url):
        comments = []

        bs = cls.get_html(url)
        for e in bs.select('div#comments div.comment'):
            comments.append(cls._parse_comment(e))

        return comments

    @classmethod
    def _parse_comment(cls, e):
        author_time = e.select('div.commentheader div.submitted')[0]
        author_time = re.match(r'Am (.+) um (.+) von (.+)', author_time.get_text().strip())

        return models.CommentBase(username=author_time.group(3),
                                  comment_id=e.select('div.commentheader h3.title a')[0]['id'],
                                  timestamp=cls._parse_date(f'{author_time.group(1)} {author_time.group(2)}'),
                                  text=e.select('div.content')[0].get_text().strip(),
                                  title=e.select('div.commentheader h3.title')[0].get_text().strip())

    @staticmethod
    def _parse_date(s):
        for de, en in [('Januar', 'January'), ('Februar', 'February'), ('März', 'March'),  # ('April', 'April'),
                       ('Mai', 'May'), ('Juni', 'June'), ('Juli', 'July'),
                       # ('August', 'August'), ('September', 'September'),
                       ('Oktober', 'October'),  # ('November', 'November')
                       ('Dezember', 'December')]:
            s = s.replace(de, en)
        return datetime.strptime(s, '%d. %B %Y %H:%M')


# todo: run test cases and fix broken url
if __name__ == '__main__':
    TagesschauScraper.test_scraper([
        'https://www.tagesschau.de/inland/cdu-parteitag-185.html',
        'https://www.tagesschau.de/ausland/impeachment-schiff-101~_origin-5edd7d7c-309b-445b-8cc1-d98aa2901486.html',
        'https://www.tagesschau.de/investigativ/ndr/antibiotika-gefluegel-101.html',
        'https://www.tagesschau.de/ausland/griechisch-tuerkische-grenze-101.html'
    ])
