import urllib
from random import randint
import moviepy.editor as mp
import re
from time import sleep

import requests
from bs4 import BeautifulSoup

from app.core.utils import generate_request_header


class ContentCollector:
    REDDIT_URL = "https://www.reddit.com/r/{category}/top/?sort=top&t={sort}&count={page}"
    TUMBLR_URL = "https://www.tumblr.com/search/{}"

    def _get_reddit_content(self, subreddit, sort):
        random_page = randint(0, 0) * 25
        for page in range(0, 200, 25):
            url = self.REDDIT_URL.format(category=subreddit, sort=sort, page=page)

            html = requests.get(url, headers=generate_request_header()).content

            soup = BeautifulSoup(html, "lxml")

            contents = soup.findAll(name="a", attrs={"class": "title may-blank outbound"})

            for content in contents:

                title = re.sub(r"\[.*\]", "", content.text).strip()
                content_url = content["href"]

                fmt = content_url.split(".")[-1]

                file_name = "tmp." + fmt

                urllib.urlretrieve(content_url, file_name.format(fmt))

                if "gif" in fmt:
                    clip = mp.VideoFileClip("test.gif")
                    clip.write_videofile("test.mp4")

                print(title, content_url)

    def _get_tumblr_content(self, search_query):
        search_query = re.sub("[ ]+", "+", search_query)
        tumblr_url = self.TUMBLR_URL.format(search_query)
        html = requests.get(tumblr_url, headers=generate_request_header()).content
        soup = BeautifulSoup(html)

        content_containers = soup.findAll(name="article", attrs={"data-type": "photo"})
        for container in content_containers:
            content = container.find(name="img")
            tags_container = container.findAll(name="a", attrs={"class": "post_tag"})
            url = content["src"]
            tags = []
            caption = content["data-pin-description"]
            for tag in tags_container:
                tags.append(tag.text.strip())

            extension = url.split(".")[-1]

            for tag in tags:
                temp = tag.replace(" ", "-")

            print(content, url)





if __name__ == '__main__':
    collector = ContentCollector()
    while True:
        collector._get_tumblr_content("earthporn")
        sleep(10)
