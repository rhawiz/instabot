# -*- coding: utf-8 -*-

import csv
import random

import sqlite3

import logging

BASE_REQUEST_HEADER = {
    'ACCEPT_LANGUAGE': 'en-GB,en;q=0.8,en-US;q=0.6'
}

"""
List of various browser User-Agent headers
"""
USER_AGENT_HEADER_LIST = [

    # I.E. 11.0
    "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko",
    "Mozilla/5.0 (compatible, MSIE 11, Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko",

    # I.E. 10.0
    "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 7.0; InfoPath.3; .NET CLR 3.1.40767; Trident/6.0; en-IN)",
    "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)",
    "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)",
    "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/5.0)",
    "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/4.0; InfoPath.2; SV1; .NET CLR 2.0.50727; WOW64)",
    "Mozilla/5.0 (compatible; MSIE 10.0; Macintosh; Intel Mac OS X 10_7_3; Trident/6.0)",
    "Mozilla/4.0 (Compatible; MSIE 8.0; Windows NT 5.2; Trident/6.0)",
    "Mozilla/4.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/5.0)",
    "Mozilla/1.22 (compatible; MSIE 10.0; Windows 3.1)",

    # Chrome 41.0.2228.0
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36",

    # Chrome 41.0.2227.1
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36",

    # Chrome 41.0.2227.0
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36",

    # Chrome 41.0.2226.0
    "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2226.0 Safari/537.36",

    # Chrome 41.0.2225.0
    "Mozilla/5.0 (Windows NT 6.4; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2225.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2225.0 Safari/537.36",

    # Chrome 41.0.2224.3
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2224.3 Safari/537.36",

    # Firefox 40.1
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1",

    # Firefox 36.0
    "Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0",

    # Firefox 33.0
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10; rv:33.0) Gecko/20100101 Firefox/33.0",

    # Firefox 31.0
    "Mozilla/5.0 (X11; Linux i586; rv:31.0) Gecko/20100101 Firefox/31.0",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:31.0) Gecko/20130401 Firefox/31.0",
    "Mozilla/5.0 (Windows NT 5.1; rv:31.0) Gecko/20100101 Firefox/31.0",

    # Firefox 29.0
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:29.0) Gecko/20120101 Firefox/29.0",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:25.0) Gecko/20100101 Firefox/29.0",

]


def pop_text_file(file):
    with open(file, 'rb') as fin:
        data = fin.read().splitlines(True)
    with open(file, 'wb') as fout:
        fout.writelines(data[1:])


def append_to_file(string, file):
    with open(file, "ab") as f:
        f.write(string)


def csv_to_list(file, delimiter=',', quotechar='"', has_headers=True):
    delimiter = delimiter.__str__()
    quotechar = quotechar.__str__()
    with open(file) as f:
        data = [row for row in csv.reader(f, delimiter=delimiter, quotechar=quotechar)]
        if has_headers:
            data = data[1:]
    return data


def generate_request_header():
    header = BASE_REQUEST_HEADER
    header["User-Agent"] = USER_AGENT_HEADER_LIST[random.randint(0, len(USER_AGENT_HEADER_LIST) - 1)]
    return header

def get_logger():
    logger = logging.getLogger(__name__)
    logging.getLogger("requests").setLevel(logging.WARNING)
    syslog = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s][%(levelname)s][%(user)s][%(bot)s] %(message)s')
    syslog.setFormatter(formatter)
    logger.setLevel(logging.DEBUG)
    # if not logger.handlers:
    logger.addHandler(syslog)
    return logger


def execute_query(db_path, sql_query):
    """Execute sql query on a sqlite databasse"""
    connection = sqlite3.connect(db_path)
    connection.text_factory = str
    cursor = connection.cursor()
    cursor.execute(sql_query)
    connection.commit()
    data = cursor.fetchall()
    connection.close()
    return data
