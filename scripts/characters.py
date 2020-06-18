#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Scrap character list from IMDb
Usage: characters.py [--series=<series> --serie=<serie>]
characters.py count [--series=<series> --serie=<serie>]
characters.py duplicates [--series=<series> --serie=<serie>]

Options:
    --series=<series>    Path to a file containing information about the series
                         formatted as 'Plumcot/data/series.txt' (see CONTRIBUTING).
                         Defaults to 'Plumcot/data/series.txt'
    --serie=<serie>      Process only this `serie`.
                         Defaults to processing all `series`
"""

import requests
from bs4 import BeautifulSoup
import codecs  # for encoding the data as utf-8
import unidecode
import re
import json
from docopt import docopt
import numpy as np
import pyannote.database
import Plumcot as PC
from Plumcot import Plumcot
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

    cast = {}

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
                cast[normActorName] = (normCharName, normActorName, charName,
                                        actorName, charLink)
    return cast


def formatData(cast):
    """Formats IMDb cast in the following format:
    actor's normalized name, character's full name, actor's full name,
    IMDb.com character page, separated with commas.

    Parameters
    ----------
    cast : `dict`
        IMDB cast with actor normalized names as keys.

    Returns
    -------
    cast : `list`
        List with one string per character.
    """

    textFile = []
    for normCharName, normActorName, charName, actorName, charLink in cast.values():
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

def scrap(series,serie):
    with open(series, 'r') as f:
        for line in f:
            sp = line.split(',')
            idSeries = sp[0]
            isMovie = int(sp[4])

            if not serie or idSeries == serie:
                if not isMovie:
                    link = sp[2]
                    data = scrapPage(link + "fullcredits/")
                else:
                    data = {}
                    with open(DATA_PATH/idSeries/"episodes.txt", 'r') as fMovie:
                        for lineMovie in fMovie:
                            link = lineMovie.split(',')[2]
                            movieChars = scrapPage(link + "fullcredits/")
                            data.update(movieChars)
                formatted_data=formatData(data)
                finalText = "".join(formatted_data)
                writeData(idSeries, finalText)

def find_duplicates(series,serie,actors=False,write = False):
    unique_per_series, unique_actor_per_series = {}, {}
    series = np.loadtxt(series, dtype=str, delimiter=',', usecols=(0,))
    for idSeries in series:
        if not serie or idSeries == serie:
            serie_characters=np.loadtxt(DATA_PATH/idSeries/"characters.txt",
                              dtype=str, delimiter=',', usecols=(0,1))
            serie_characters_dict = {}
            for character, actor in serie_characters:
                serie_characters_dict.setdefault(character,[]).append(actor)
            serie_characters_dict = {character: actors for character, actors in serie_characters_dict.items() if len(actors)>1}

            for character in serie_characters_dict.keys():
                unique_per_series.setdefault(character,[]).append(idSeries)
            for actor in set(serie_characters[:,1]):
                unique_actor_per_series.setdefault(actor,[]).append(idSeries)
            if not write:
                continue
            with open(DATA_PATH/idSeries/"not_unique.json",'w') as file:
                json.dump(serie_characters_dict,file,indent=4,sort_keys=True)
    unique_per_series = {character: series for character, series in unique_per_series.items() if len(series) > 1}
    unique_actor_per_series = {actor: series for actor, series in unique_actor_per_series.items() if len(series) > 1}
    with open(DATA_PATH/"not_unique_across_series.json",'w') as file:
        json.dump(unique_per_series,file,indent=4,sort_keys=True)
    with open(DATA_PATH/"not_unique_actors_across_series.json",'w') as file:
        json.dump(unique_actor_per_series,file,indent=4,sort_keys=True)

def count(serie,actors=False):
    db = Plumcot()
    counter = {}
    for idSeries in db.series['short_name']:
        if not serie or idSeries == serie:
            field = 'actor_uri' if actors else 'character_uri'
            serie_characters=db.get_characters(idSeries, field=field)
            #loop through episodes
            for character_list in serie_characters.values():
                #loop through characters in episode
                for character in character_list:
                    counter.setdefault(character,{})
                    counter[character].setdefault(idSeries,0)
                    counter[character][idSeries]+=1
    counter = {character: series for character, series in counter.items() if len(series) > 1}
    name = "actor_counter.json" if actors else "counter.json"
    with open(DATA_PATH/name,'w') as file:
        json.dump(counter,file,indent=4,sort_keys=True)

def main(args):
    series = args["--series"] if args["--series"] else DATA_PATH / 'series.txt'
    serie = args["--serie"]
    if args['count']:
        count(serie)
    elif args['duplicates']:
        find_duplicates(series,serie)
    else:
        scrap(series,serie)



if __name__ == '__main__':
    args = docopt(__doc__)
    main(args)
