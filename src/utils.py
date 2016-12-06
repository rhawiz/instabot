# -*- coding: utf-8 -*-

import csv
import os
import re

import sys
from bs4 import BeautifulSoup


def append_to_file(string, file):
    with open(file, "ab") as f:
        f.write(string)


def write_to_file(string, file):
    with open(file, "wb") as f:
        f.write(string)


def read_file(file):
    with open(file, 'rb') as f:
        file = f.read()
    return file


def visible(element):
    if element.parent.name in ['style', 'script', '[document]', 'title', 'head']:
        return False
    elif re.match('<!--.*-->', str(element.encode('utf-8'))):
        return False
    return True


def html_to_text(html, delete_chars=[]):
    soup = BeautifulSoup(html)
    data = soup.findAll(text=True)
    result = filter(visible, data)
    result = " ".join(result)
    text = re.sub('[\\r\\n\\t]+', ' ', result)
    text = re.sub('\\s+', ' ', text)
    text = os.linesep.join([s for s in text.splitlines() if s])

    for char in delete_chars:
        text = text.replace(char, '')

    return text.encode('utf-8').strip()


def list_to_csv(list, file, mode='ab'):
    with open(file, mode=mode) as f:
        writer = csv.writer(f, delimiter=',', quotechar='"')
        writer.writerow(list)


def csv_to_list(file, delimiter=',', quotechar='"', has_headers=True):
    delimiter = delimiter.__str__()
    quotechar = quotechar.__str__()
    with open(file) as f:
        data = [row for row in csv.reader(f, delimiter=delimiter, quotechar=quotechar)]
        if has_headers:
            data = data[1:]
    return data


def text_to_list(file):
    with open(file) as f:
        data = f.readlines()
    content = []
    for row in data:
        row = re.sub("\n", "", row)
        content.append(row)


    return content


# Print iterations progress
def print_progress(iteration, total, prefix='', suffix='', decimals=1, bar_len=100):
    """Call in a loop to create terminal progress bar

    Parameters
    ----------
    iteration: int
        Current iteration
    total: int
        Total iterations
    prefix: str
        Prefix string
    suffix: str
        Suffix string
    decimals: int
        Positive number of decimals in percent complete
    bar_len: int
        Character length of bar

    """
    format_str = "{0:." + str(decimals) + "f}"
    percents = format_str.format(100 * (iteration / float(total)))
    filled_len = int(round(bar_len * iteration / float(total)))
    bar = '█' * filled_len + '-' * (bar_len - filled_len)
    sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, percents, '%', suffix)),
    if iteration == total:
        sys.stdout.write('\n')
    sys.stdout.flush()
