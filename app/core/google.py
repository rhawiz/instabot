import re
from time import sleep
from xml.sax.saxutils import unescape

from BeautifulSoup import BeautifulSoup
import requests

from app.core.utils import generate_request_header


class GoogleResult(object):
    pass


class GoogleImageSearch(object):
    BASE_URL = "https://www.google.co.uk/search?q={q}&safe=off&tbm=isch&tbs=ic:specific,"
    RESOLUTION_FILTER = "islt:{resolution},"
    TYPE_FILTER = "itp:{type},"
    COLOUR_FILTER = "isc:{colour},"
    MIN_DATE_FILTER = "cd_min:{min_date},"
    MAX_DATE_FILTER = "cd_max:{max_date}"

    def __init__(self, keywords, type=None, resolution=None, colour=None, min_date=None, max_date=None):
        self.keywords = keywords
        self.type = type
        self.resolution = resolution
        self.colour = colour
        self.min_date = min_date
        self.max_date = max_date

    def _construct_query(self, q, **kwargs):
        url_template = self.BASE_URL.format(q=q)

        if "type" in kwargs:
            url_template += self.TYPE_FILTER

        if "resolution" in kwargs:
            url_template += self.RESOLUTION_FILTER

        if "colour" in kwargs:
            url_template += self.COLOUR_FILTER

        if "max_date" in kwargs:
            url_template += self.MAX_DATE_FILTER

        if "min_date" in kwargs:
            url_template += self.MIN_DATE_FILTER

        return url_template.format(**kwargs).rstrip(",")

    def search(self):
        filters = dict([item for item in self.__dict__.items() if item[1]])
        filters.pop("keywords")

        for q in self.keywords:
            url = self._construct_query(q, **filters)
            html = requests.get(url, headers=generate_request_header()).text
            html = re.sub("\&lt\;", "<", html)
            html = re.sub("\&gt\;", ">", html)
            html = re.sub("\&amp\;", "&", html)

            print(html)
            soup = BeautifulSoup(html)

            contents = soup.findAll(name="a", attrs={"jsname": "hSRGPd"})
            print contents
            for content_soup in contents:
                self._scrape_contents(content_soup)
            if not url:
                continue

    def _scrape_contents(self, content_soup):
        url = content_soup["href"] if "href" in content_soup else None
        if not url:
            return None
        url = "https://www.google.com{}".format(url)
        html = requests.get(url, headers=generate_request_header()).content
        soup = BeautifulSoup(html)
        source_soup = soup.find(name="a", attrs={"class": "irc_vpl irc_but i3599", "href": re.compile("http\:.*")})
        source = source_soup["href"] if source_soup is not None and "href" in source_soup else None

        url_soup = soup.find(name="a", attrs={"class": "irc_fsl irc_but i3596", "href": re.compile("http\:.*")})
        url = source_soup["href"] if url_soup is not None and "href" in url_soup else None

        print source, url

        sleep(1)


gis = GoogleImageSearch(["Hello"])
gis.search()
