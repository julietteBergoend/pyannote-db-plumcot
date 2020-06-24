#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Usage: episodes.py [--series=<series> --serie=<serie> -c]

Options:
    --series=<series>    Path to a file containing information about the series
                         formatted as 'Plumcot/data/series.txt' (see CONTRIBUTING).
                         Defaults to 'Plumcot/data/series.txt'
    --serie=<serie>      Process only this `serie`.
                         Defaults to processing all `series`
    -c                   creates credits.txt file (needs characters.txt)
"""

import codecs  # for encoding the data as utf-8
import re
from collections import OrderedDict
from pathlib import Path

import requests
import unidecode
from bs4 import BeautifulSoup
from docopt import docopt

import Plumcot as PC

DATA_PATH = Path(PC.__file__).parent / "data"


def normalizeName(fullName):
    """Normalizes characters and actors names.

    Removes parenthesis, commas, diacritics and non-alphanumerics characters,
    except _.

    Parameters
    ----------
    fullName : `str`
        Full name (of a character or a person).

    Returns
    -------
    normName : `str`
        Normalized name.
    """

    fullName = fullName.lower()

    fullName = fullName.split('\n')[0].strip()
    fullName = re.sub(r'\([^()]*\)', '', fullName)  # Remove parenthesis
    fullName = re.sub(r"\'[^'']*\'", '', fullName)  # Remove commas
    fullName = unidecode.unidecode(fullName)  # Remove diacritics
    fullName = fullName.replace(' ', '_')
    # Remove all non-alphanumerics characters (except _)
    fullName = re.sub(r'\W+', '', fullName)
    fullName = re.sub(r"[_]+", '_', fullName)
    return fullName


def scrapPage(idSeries, pageIMDB, credit=False, dicChars=None):
    """Extracts episodes list of a series.

    Given an IMDB page, extracts episodes information in this format:
    unique episode identifier, name of the episode, IMDB.com episode page,
    TV.com episode page.

    Parameters
    ----------
    idSeries : `str`
        Folder of the series.
    pageIMDB : `str`
        IMDB page with the list of episodes.
    credit : `bool`
        Set to True to create credits.txt.
    dicChars : `OrderedDict`
        Ordered dictionnary generated from characters.txt.

    Returns
    -------
    seriesData : `str`
        String with the correct format, one line per episode.
    creditsData : `str`
        String with the correct format for credits.txt
    """

    urlIDMB = requests.get(pageIMDB).text
    soup = BeautifulSoup(urlIDMB, 'lxml')
    seriesData = ""
    creditsData = ""

    nbSeasons = len(soup.find(id="bySeason").find_all('option')) + 1

    for season in range(1, nbSeasons):
        linkSeason = pageIMDB + "?season=" + str(season)
        urlIDMB = requests.get(linkSeason).text
        soup = BeautifulSoup(urlIDMB, 'lxml')

        table = soup.find('div', {'class': 'eplist'})
        episodesTable = table.find_all('div', class_="list_item")

        for episode in episodesTable:
            infos = episode.find('div', {'class': 'info'})
            nbEpisode = int(infos.find('meta').get('content'))
            link = infos.find('a')
            title = link.get('title')

            if "Episode #" not in title:
                link = link.get('href').split('?')[0]
                imdbLink = "https://www.imdb.com" + link
                seasonStr = f"{season:02d}"
                epStr = f"{nbEpisode:02d}"

                epNorm = idSeries + '.Season' + seasonStr + '.Episode' + epStr

                epString = epNorm + ',' + title + ',' + imdbLink + ','

                if credit:
                    epCast = getEpCast(imdbLink, dicChars)
                    creditsData += epNorm + ',' + epCast + '\n'

                seriesData += epString + '\n'

    return seriesData, creditsData


def getEpCast(imdbLink, dicChars):
    """Extracts cast of an episode.

    Given the episode cast IMDB page and the series characters dictionnary set
    to zeros, sets ones if the character appears in the episode.


    Parameters
    ----------
    pageIMDB : `str`
        IMDB episode cast link.
    dicChars : `OrderedDict`
        Ordered dictionnary generated from characters.txt.

    Returns
    -------
    creditsData : `str`
        String with one if the character is in the episode and zero if not,
        separated with commas.
    """

    dicEpCast = dicChars.copy()

    urlIDMB = requests.get(imdbLink + "fullcredits").text
    soup = BeautifulSoup(urlIDMB, 'lxml')
    seriesTable = soup.find('table', {'class': 'cast_list'}).find_all('tr')

    for char in seriesTable:
        charInfo = char.find_all('td')
        if len(charInfo) == 4:
            actorName = charInfo[1].text.strip()

            key = normalizeName(actorName)

            if key in dicEpCast:
                dicEpCast[key] = '1'

    return ",".join(x for x in dicEpCast.values())


def writeData(series, data, file):
    """Writes characters information in `characters.txt`.

    Parameters
    ----------
    series : `str`
        Folder of the series.
    data : `str`
        Data to write.
    """

    with codecs.open(DATA_PATH / series / file, "w", "utf-8") as chars:
        chars.write(data)


def initDicChars(idSeries):
    """Creates a dictionnary in the format (idCharacter, 0)

    Creates an OrderedDict dictionnary in the format (idCharacter, 0) from
    characters.txt.


    Parameters
    ----------
    idSeries : `str`
        Id of the series.

    Returns
    -------
    dicChars : `OrderedDict`
        OrderedDict in the format (idCharacter, 0).
    """
    dicChars = OrderedDict()

    with open(DATA_PATH / idSeries / "characters.txt", 'r') as chars:
        for charLine in chars:
            charSp = charLine.split(',')
            key = charSp[1]

            dicChars[key] = '0'

    return dicChars


def main(args):
    series = args["--series"] if args["--series"] else DATA_PATH / 'series.txt'
    serie = args["--serie"]
    credit = True if args['-c'] else False

    with open(series, 'r') as f:
        for line in f:
            sp = line.split(',')
            idSeries = sp[0]
            isMovie = int(sp[4])

            if not isMovie and (not serie or idSeries == serie):
                if args['-c']:
                    dicChars = initDicChars(idSeries)
                link = sp[2]
                dataSeries, dataCredits = scrapPage(idSeries,
                                                    link + "episodes",
                                                    credit, dicChars)
                finalText = "".join(dataSeries)
                writeData(idSeries, finalText, "episodes.txt")
                if credit:
                    writeData(idSeries, dataCredits, "credits.txt")

            if credit and isMovie and (not serie or idSeries == serie):
                with open(DATA_PATH / idSeries / "episodes.txt", 'r') as movies:
                    dataMovie = ""
                    for movie in movies:
                        movieSp = movie.split(',')
                        normName = movieSp[0]
                        linkIMDB = movieSp[2]
                        dic = initDicChars(idSeries)

                        epCast = getEpCast(linkIMDB, dic)
                        dataMovie += (f"{normName},{epCast}\n")

                    writeData(idSeries, dataMovie, "credits.txt")


if __name__ == '__main__':
    args = docopt(__doc__)
    main(args)
