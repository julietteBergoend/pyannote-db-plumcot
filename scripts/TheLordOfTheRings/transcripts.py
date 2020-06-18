#!/usr/bin/env python
# coding: utf-8

import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from bs4.element import NavigableString

scripts_url = "http://www.ageofthering.com/atthemovies/scripts/"
import Plumcot as PC

DATA_PATH = Path(PC.__file__).parent / "data"
uri = 'TheLordOfTheRings'
transcripts_path = DATA_PATH / uri / 'transcripts'

title_map = {
    'fellowshipof': 'TheLordOfTheRings.Episode01',
    'thetwotowers': 'TheLordOfTheRings.Episode02',
    'returnofthek': 'TheLordOfTheRings.Episode03'
}


def get_NavigableStrings(soup):
    navigableStrings = ""
    for a in soup.find_all('td'):
        for stuff in a:
            if isinstance(stuff, NavigableString):
                navigableStrings += stuff + '\n'
    return navigableStrings


def format_temp_transcript(navigableStrings):
    # remove everything in between <>, () et []
    navigableStrings = re.sub(r'(\<.*?\>)|(\[.*?\])|(\(.*?\))', '', navigableStrings)
    temp_transcript = "\n"
    for line in navigableStrings.split('\n'):
        line = line.strip()
        if line.isspace() or line == '' or '~' in line:
            continue
        if line[-1] == ':':
            temp_transcript += '\n'
            temp_transcript += re.sub('VOICE.*OVER', '', line[:-1]).strip() + ' '
        else:
            temp_transcript += line + ' '
    return temp_transcript


html_page = requests.get(scripts_url).text
soup = BeautifulSoup(html_page, features="html.parser")
links = soup.findAll("a")
for link in links:
    if link['href'].endswith("php"):  # query transcript
        if 'script' in link['href']:
            continue
        title = title_map.get(link['href'][:12])
        if not title:
            continue
        output_path = transcripts_path / f'{title}.temp'
        print(link['href'], title, output_path)

        request = requests.get(scripts_url + link['href'])
        html_page = request.text
        soup = BeautifulSoup(html_page, features="html.parser")
        navigableStrings = get_NavigableStrings(soup)
        temp_transcript = format_temp_transcript(navigableStrings)

        with open(output_path, 'a') as file:
            file.write(temp_transcript)
