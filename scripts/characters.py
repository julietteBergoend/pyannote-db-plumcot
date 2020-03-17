#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Usage: characters.py SOURCEFILE [SERIES] [-v FILE]

Arguments:
    SOURCEFILE    input series list file
    SERIES        optionnal normalized name of a series

Options:
    -v FILE  creates normalization verification for names in FILE

"""

import requests
from bs4 import BeautifulSoup
import codecs  # for encoding the data as utf-8
import unidecode
import re
from docopt import docopt
import numpy as np
import pyannote.database
import Plumcot as PC
from pathlib import Path

DATA_PATH=Path(PC.__file__).parent / "data"

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


def scrapPage(pageIMDB):
    """Extracts characters list of a series.

    Given an IMDB page, extracts characters information in this format:
    actor's normalized name, character's full name, actor's full name,
    IMDB.com character page.

    Parameters
    ----------
    pageIMDB : `str`
        IMDB page with the list of characters.

    Returns
    -------
    cast : `list`
        List with one tuple per character.
    """
    urlIDMB = requests.get(pageIMDB).text
    soup = BeautifulSoup(urlIDMB, 'lxml')
    seriesTable = soup.find('table', {'class': 'cast_list'}).find_all('tr')

    cast = []

    for char in seriesTable:
        charInfo = char.find_all('td')
        if len(charInfo) == 4:
            actorName = charInfo[1].text.strip()

            charNorm = charInfo[3].find('a')
            charLink = ""
            if not charNorm:
                charName = charInfo[3].text.strip().split('\n')[0].strip()
            elif charNorm.get('href') != "#":
                charName = charNorm.text.strip()
                charLink = "https://www.imdb.com" \
                    + charNorm.get('href').strip().split('?')[0]
            else:
                charName = charNorm.previous_sibling.strip()\
                    .split('\n')[0].strip()
            charName=charName.replace(",","")
            normActorName = normalizeName(actorName)
            normCharName = normalizeName(charName)
            if normCharName and normActorName:
                cast.append((normCharName, normActorName, charName,
                             actorName, charLink))

    return cast


def getData(pageIDMB):
    """Extracts characters list of a series.

    Given an IMDB page, extracts characters information in this format:
    actor's normalized name, character's full name, actor's full name,
    IMDB.com character page, separated with commas.

    Parameters
    ----------
    pageIMDB : `str`
        IMDB page with the list of characters.

    Returns
    -------
    cast : `list`
        List with one string per character.
    """

    textFile = []
    cast = scrapPage(pageIDMB)

    for normCharName, normActorName, charName, actorName, charLink in cast:
        text = normCharName + ',' + normActorName + ',' + charName + ',' + \
            actorName + ',' + charLink + '\n'
        text = text.encode('utf-8')
        textWrite = text.decode('utf-8')
        textFile.append(textWrite)

    return textFile


def writeData(series, data):
    """Writes characters information in `characters.txt`.

    Parameters
    ----------
    series : `str`
        Folder of the series.
    data : `str`
        Data to write.
    """

    with codecs.open(DATA_PATH/series/"characters.txt", "w", "utf-8") as chars:
        chars.write(data)


def verifNorm(idSeries, fileName, data):
    """Creates the normalization verification file.

    Parameters
    ----------
    idSeries : `str`
        Folder of the series.
    fileName : `str`
        Wanted file name.
    data : `str`
        Data to write.
    """

    file = DATA_PATH / idSeries / fileName
    with open(file, mode="w", encoding="utf-8") as f:
        for char in data:
            charSp = char.split(',')
            normName = charSp[0]
            name = charSp[2]

            f.write(normName + ";" + name + "\n")


def main(args):
    sourceFile = args["SOURCEFILE"]
    onlyOne = args["SERIES"]
    if onlyOne:
        series = args["SERIES"]

    with open(sourceFile, 'r') as f:
        for line in f:
            sp = line.split(',')
            idSeries = sp[0]
            isMovie = int(sp[4])

            if not onlyOne or idSeries == series:
                if not isMovie:
                    link = sp[2]
                    data = set(getData(link + "fullcredits/"))
                    if args["-v"]:
                        verifNorm(idSeries, args["-v"], data)
                    finalText = "".join(data)
                    writeData(idSeries, finalText)

                else:
                    sagaChars = set()
                    with open(DATA_PATH/idSeries/"episodes.txt", 'r') as fMovie:
                        for lineMovie in fMovie:
                            link = lineMovie.split(',')[2]
                            movieChars = set(getData(link + "fullcredits/"))
                            sagaChars.update(movieChars)
                    # sagaChars = list(set(sagaChars)) to remove duplicates
                    if args["-v"]:
                        verifNorm(idSeries, args["-v"], sagaChars)
                    finalText = "".join(sagaChars)
                    writeData(idSeries, finalText)


if __name__ == '__main__':
    args = docopt(__doc__)
    main(args)
