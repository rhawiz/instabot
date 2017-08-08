
from random import randint

import re
from time import sleep

import requests
from bs4 import BeautifulSoup

from app.core.utils import generate_request_header


class ContentCollector:
    REDDIT_URL = "https://www.reddit.com/r/{}/top/?sort=top&t={}&count={}"
    TUMBLR_URL = "https://www.tumblr.com/search/{}"

    def _get_reddit_content(self, subreddit, sort):
        random_page = randint(0, 10) * 25
        reddit_url = self.REDDIT_URL.format(subreddit, sort, random_page)

        html = requests.get(reddit_url, headers=generate_request_header()).content

        soup = BeautifulSoup(html, "lxml")

        content = soup.findAll(name="a", attrs={"class": "title may-blank outbound "})

        content = content[randint(0, len(content) - 1)]

        title = re.sub(r"\[.*\]", "", content.text).strip()
        img_url = content["href"]

        print title, img_url

    def _get_tumblr_content(self, search_query):
        search_query = re.sub("[ ]+", "+", search_query)
        tumblr_url = self.TUMBLR_URL.format(search_query)
        html = requests.get(tumblr_url, headers=generate_request_header()).content
        soup = BeautifulSoup(html)

        content_containers = soup.findAll(name="article", attrs={"data-type": "photo"})
        for container in content_containers:
            content = container.find(name="img")
            tags_container = container.findAll(name="a", attrs={"class": "post_tag"})

            if hasattr(content, "app"):
                url = content["core"]
                tags = []

                for tag in tags_container:
                    tags.append(tag.text.strip())
                file_name = ''
                extension = url.split(".")[-1]
                for tag in tags:
                    temp = tag.replace(" ", "-")

                    file_name += temp + "_"

                    # TODO: Save file to relevant location
                    # file_name = "{}.{}".format(file_name, extension)
                    # resource = urllib.urlopen(url)
                    # path = "../data/hwzfit/{}".format(file_name)
                    # output = open(path, "wb+")
                    # output.write(resource.read())
                    # output.close()



if __name__ == '__main__':
    collector = ContentCollector()
    while True:
        collector._get_reddit_content("funny", "month")
        sleep(10)