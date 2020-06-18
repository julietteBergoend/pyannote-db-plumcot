# -*- coding: utf-8 -*-
"""
This script will extract transcripts from fan-websites and save output to <serie>/transcripts/<episode>.temp
Apologies for the french comments

@author: Sharleyne Lefevre
@author: Paul Lerner
"""
from bs4 import BeautifulSoup
import urllib.request
import re
from urllib.parse import urlparse
import codecs
import os
import sys

sys.setrecursionlimit(90000)

import pyannote.database
import Plumcot as PC
from pathlib import Path

DATA_PATH = Path(PC.__file__).parent / "data"


def extractSpringfieldWebsite():
    """NO LOC SPRINGFIELD WEBSITE """
    url_no_loc = "https://www.springfieldspringfield.co.uk/episode_scripts.php?tv-show="
    series_no_loc = [["the-office-us", "TheOffice"],
                     ["24", "24"],
                     ["the-walking-dead", "TheWalkingDead"],
                     ["ER", "ER"],
                     ["homeland", "Homeland"],
                     ["six-feet-under", "SixFeetUnder"],
                     ["battlestar-galactica", "BattleStarGalactica"],
                     ["breaking-bad", "BreakingBad"],
                     ["lost", "Lost"],
                     ["buffy-the-vampire-slayer", "BuffyTheVampireSlayer"],
                     ["game-of-thrones", "GameOfThrones"],
                     ["big-bang-theory", "TheBigBangTheory"],
                     ["game-of-thrones", "GameOfThrones"]]  # a coller a l'url ci-dessus
    for serie in series_no_loc:
        html_page2 = urllib.request.urlopen(url_no_loc + serie[0])

        soup_page_web2 = BeautifulSoup(html_page2,
                                       'html.parser')  # parsing du html avec bs4
        data2 = soup_page_web2.findAll('a', attrs={
            'season-episode-title'})  # recherche de toutes les balises <a> dans section 'season-episode-title'

        for div in data2:
            parsed_url = urlparse(url_no_loc + serie[
                0])  # ParseResult(scheme='https', netloc='transcripts.fandom.com', path='/wiki/The_Walking_Dead_(TV_series)', params='', query='', fragment='')
            url_page_script = parsed_url._replace(path=str(div['href']))._replace(
                query="")  # Modifie le dernier element de l'url par le nom de l'episode
            new_url = url_page_script.geturl()  # Nouvel url pour acceder a la transcription de l'episode
            # if not "s07e01" in new_url: # pour GOT 1 episode sans contenu html
            html_script = urllib.request.urlopen(
                new_url)  # Parsing du lien ou se trouve la transcription
            soup_page_script = BeautifulSoup(html_script, 'html.parser')
            data_script = soup_page_script.findAll('div', attrs={
                'class': 'scrolling-script-container'})  # Se placer dans le div ou il y a le script

            # Obtention du format SaisonX.EpisodeX.txt
            idEpisode = url_page_script.path.split("=")[2]  # s01e01
            newIdEpisode = re.sub(r"(s)([0-9]{2,})(e)([0-9]{2,})", r"Season\2.Episode\4",
                                  idEpisode)  # Season01.Episode01
            # Ecriture de la transcription dans le fichier
            for div in data_script:
                html_path = DATA_PATH / serie[1] / "temp_html"
                html_path.mkdir(exist_ok=True)
                with codecs.open(html_path / f"{serie[1]}.{newIdEpisode}.temp", 'w',
                                 "utf8") as f:
                    f.write(str(div))  # Ecriture du script dans un fichier .txt


def extractFandomWebsite():
    """LOC FANDOM WEBSITE """
    url_loc = "https://transcripts.fandom.com/wiki/The_Walking_Dead_(TV_series)"

    html_page = urllib.request.urlopen(url_loc)
    soup_page_web = BeautifulSoup(html_page, 'html.parser')
    data = soup_page_web.findAll('div', attrs={'class': 'mw-content-ltr mw-content-text'})
    for div in data:
        links = div.findAll('a')
        for a in links:
            parsed_url = urlparse(
                url_loc)  # ParseResult(scheme='https', netloc='transcripts.fandom.com', path='/wiki/The_Walking_Dead_(TV_series)', params='', query='', fragment='')
            url_page_script = parsed_url._replace(path=str(a[
                                                               'href']))  # Modifie le dernier element de l'url par le nom de l'episode
            new_url = url_page_script.geturl()  # Nouvel url pour acceder a la transcription de l'episode
            html_script = urllib.request.urlopen(
                new_url)  # Parsing du lien ou se trouve la transcription
            soup_page_script = BeautifulSoup(html_script, 'html.parser')
            data_script = soup_page_script.findAll('div', attrs={
                'class': 'mw-content-ltr mw-content-text'})  # Se placer dans le div où il y a le script

            idEpisode = str(div.text.split(' ')[0] + div.text.split(' ')[1]).split('\n')[
                1]
            newIdEpisode = re.sub(r"(Season)([0-9]{1,})", r"Season0\2",
                                  idEpisode)  # Season01.Episode01

            for div in data_script:
                transcript_path = DATA_PATH / "TheWalkingDead" / "transcripts"
                transcript_path.mkdir(exist_ok=True)
                with codecs.open(
                        transcript_path / "TheWalkingDead" + newIdEpisode + ".temp", 'w',
                        "utf8") as f:
                    f.write(str(div))


def extractForeverDreamingWebsite():
    indexPage = [0, 25, 50, 75, 100, 125, 150, 175]
    for i in indexPage:
        url = "https://transcripts.foreverdreaming.org/viewforum.php?f=574&start="
        url = url.replace(url.split('&')[1], "start=" + str(i))

        html_page = urllib.request.urlopen(url)
        soup_page_web = BeautifulSoup(html_page,
                                      'html.parser')  # parsing du html avec bs4
        data = soup_page_web.findAll('a', attrs={
            'topictitle'})  # recherche de toutes les balises <a> dans section 'season-episode-title'

        for div in data:
            if not "Online Store" in div.text and not "Board Updates:" in div.text:
                # formatage du lien qui menera vers la page du script
                split_url = (str(div['href'])).split('&')
                split_url[0:2] = ['&'.join(split_url[0:2])]
                extension_url_script = str(split_url[0:2][0]).replace('.', '', 1)

                parsed_url = urlparse(url)
                url_page_script = parsed_url._replace(path=extension_url_script)._replace(
                    query="")  # Modifie le dernier element de l'url par le nom de l'episode
                new_url = url_page_script.geturl()
                html_script = urllib.request.urlopen(new_url)
                soup_page_script = BeautifulSoup(html_script, 'html.parser')
                data_script = soup_page_script.findAll('div', attrs={'class': 'boxbody'})

                idEpisode = div.text.split(' ')[0]

                if not "/" in idEpisode:
                    newIdEpisode = re.sub(r"([0-9]{2,})(x)([0-9]{2,})",
                                          r"Season\1.Episode\3",
                                          idEpisode)  # Season01.Episode01
                else:
                    newIdEpisode = re.sub(r"([0-9]{2,})(x)([0-9]{2,})(\/)([0-9]{2,})",
                                          r"Season\1.Episode\3.\5",
                                          idEpisode)  # Season01.Episode01

                for div in data_script:
                    transcript_path = DATA_PATH / "TheOffice" / "transcripts"
                    transcript_path.mkdir(exist_ok=True)
                    with codecs.open(
                            transcript_path / "TheOffice." + newIdEpisode + ".temp", 'w',
                            "utf8") as f:
                        f.write(div.text)


def main():
    extractSpringfieldWebsite()
    extractFandomWebsite()
    extractForeverDreamingWebsite()


if __name__ == '__main__':
    main()
