#!/usr/bin/env python
# coding: utf-8

# # Dependencies
"""
Get images from IMDB character's page given a list of urls and character's names
    (following the format of `characters.txt` described in CONTRIBUTING.md)
"""
import requests
from bs4 import BeautifulSoup
import numpy as np
import os
import json
import re
import warnings


# # Hyperparameters

N_COL=5#the CHARACTERS file should have 5 columns, separated by SEPARATOR
SEPARATOR=","

IMDB_URL="https://www.imdb.com"
DATA_PATH=os.path.join("..","Plumcot","data")
THUMBNAIL_CLASS="titlecharacters-image-grid__thumbnail-link"
IMAGE_CLASS="pswp__img"
with open(DATA_PATH+"/series.txt") as file:
    series=file.readlines()
SERIE_URI,_,SERIE_IMDB_URL,_,_=series[5].split(",")
CHARACTERS_PATH=os.path.join(DATA_PATH,SERIE_URI,'characters.txt')

SERIE_IMDB_ID=SERIE_IMDB_URL.split("/")[-2]

def get_url_from_character_page(url_IDMB=characters[0,-1],THUMBNAIL_CLASS="titlecharacters-image-grid__thumbnail-link"):
    """
    Gets url of image viewer of a serie pictures on IMDB (e.g. https://www.imdb.com/title/tt0108778/mediaviewer/rm3406852864)
    Given the url of a character of that serie (e.g. 'https://www.imdb.com/title/tt0108778/characters/nm0000098')

    Parameters:
    -----------
    url_IDMB: url of a character of the serie we're interested in.
        Defaults to the url of the first character of that serie, i.e. characters[0,-1]
    THUMBNAIL_CLASS: IMDB html class which containes the link to the series images url.

    Returns:
    --------
    media_viewer_url: url of image viewer of a serie pictures on IMDB
    """
    page_IMDB = requests.get(url_IDMB).text

    soup = BeautifulSoup(page_IMDB, 'lxml')

    media_viewer_url=soup.findAll("a", {"class":THUMBNAIL_CLASS})[0]["href"]

    return media_viewer_url

def get_image_jsons_from_url(media_viewer_url,IMDB_URL="https://www.imdb.com"):
    """
    Parses a json object in a dict containing a list of image urls of a IMDB serie

    Parameters:
    -----------
    media_viewer_url: url of image viewer of a serie pictures on IMDB
    IMDB_URL: base of the IMDB url, i.e. domain name etc.
        Defaults to "https://www.imdb.com"

    Returns:
    --------
    json.loads(str_script): dict parsed from a json object containing a list of image urls of a IMDB serie
    """
    image_page = requests.get(IMDB_URL+media_viewer_url).text
    soup = BeautifulSoup(image_page, 'lxml')
    tag_script=soup.find_all('script')[1]
    str_script=tag_script.get_text(strip=True)
    str_script=str_script.replace("'mediaviewer'",'"mediaviewer"')#replace simple with double quotes
    json_begins_at=str_script.find("{")
    str_script=str_script[json_begins_at:-1]#the last character is ";" for some reason so we discard it
    return json.loads(str_script)

def write_image(request,path):
    with open(path,'wb') as file:
        file.write(request.content)

def read_characters(CHARACTERS_PATH,SEPARATOR=","):
    with open(CHARACTERS_PATH,'r') as file:
        raw=file.read()
    print("\n")
    for i,line in enumerate(raw.split("\n")):
        len_line=len(line.split(SEPARATOR))
        if len_line > N_COL:
            print(i,len_line,line.split(SEPARATOR))
        elif len_line < N_COL:
            print(i,len_line,line.split(SEPARATOR))
    characters=[line.split(SEPARATOR) for i,line in enumerate(raw.split("\n")) if line !='']
    characters=np.array(characters,dtype=str)

    return characters

def query_image_from_json(image_jsons):
    for image_json in image_jsons['mediaviewer']['galleries'][SERIE_IMDB_ID]['allImages']:
        label=""
        caption=image_json['altText']
        if "at an event" in caption:
            #discard "at an event pictures" such as https://www.imdb.com/title/tt0108778/mediaviewer/rm110304000
            continue
        caption=caption.replace(", and",", ").replace("Still of ","")
        caption=re.sub(" in .*"," ",caption)
        for actor in re.split(",| and",caption):
            try:
                label+=f"{actor2character[actor.strip()]}{SEPARATOR}"
            except KeyError:
                print(f"{actor.strip()} is not in actor2character. (Original caption: {image_json['altText']})")
        if label=="":
            pass
        else:
            request=requests.get(image_json['src'])
            write_image(request,f"{label}.jpg")

def main(SERIE_URI,SERIE_IMDB_URL):
    print(SERIE_URI,SERIE_IMDB_URL)
    characters=read_characters(CHARACTERS_PATH,SEPARATOR)
    actor2character={actor:character for character,_,_,actor,_ in characters}
    warnings.warn("one to one mapping actor:character, not efficient if several actors play the same character")
    media_viewer_url=get_url_from_character_page()
    image_jsons=get_image_jsons_from_url(media_viewer_url)
    query_image_from_json(image_jsons)
if __name__ == '__main__':
    main(SERIE_URI,SERIE_IMDB_URL)

# # Keep for ref

# actor2character={actor:"" for character,_,_,actor,_ in characters}
# for character,_,_,actor,_ in characters:
#     if actor2character[actor]!="":
#         actor2character[actor]+=SEPARATOR
#     actor2character[actor]+=character
