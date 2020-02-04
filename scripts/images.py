#!/usr/bin/env python
# coding: utf-8

"""
image_scraping: Get images from IMDB character's page given a list of urls and character's names
    (following the format of `characters.txt` described in CONTRIBUTING.md)
image_features: Then extracts features off theses images.
"""

# Dependencies
import json
import numpy as np
import os
from image_scraping import main as scrap
from image_features import main as compute_references
# Hyperparameters

## core
N_COL=5#the CHARACTERS file should have 5 columns, separated by SEPARATOR
SEPARATOR=","
DATA_PATH=os.path.join("Plumcot","data")
with open(os.path.join(DATA_PATH,"series.txt")) as file:
    series=file.readlines()
IMAGE_FORMAT="jpg"

## web
IMDB_URL="https://www.imdb.com"
THUMBNAIL_CLASS="titlecharacters-image-grid__thumbnail-link"
IMAGE_CLASS="pswp__img"

## ML

def main(SERIE_URI,SERIE_IMDB_URL,IMAGE_PATH,CHARACTERS_PATH,N_COL,SEPARATOR,IMAGE_FORMAT):
    image_jsons=scrap(SERIE_URI,SERIE_IMDB_URL,IMAGE_PATH,CHARACTERS_PATH,N_COL,SEPARATOR,IMAGE_FORMAT)
    with open(os.path.join(IMAGE_PATH,"images.json"),"r") as file:
        image_jsons=json.load(file)
    image_jsons=compute_references(image_jsons,IMAGE_PATH)
    with open(os.path.join(IMAGE_PATH,"images.json"),"w") as file:
        json.dump(image_jsons,file)
    print("\ndone ;)")

if __name__ == '__main__':
    for serie in series:
        SERIE_URI,_,SERIE_IMDB_URL,_,_=serie.split(",")
        print(SERIE_URI)
        if SERIE_IMDB_URL=='':#film -> open episode:
            SERIE_IMDB_URL=np.loadtxt(os.path.join(DATA_PATH,SERIE_URI,'episodes.txt'),dtype=str,delimiter=SEPARATOR)[:,2]
        else:#only one but turn it to a list so we can iterate it
            SERIE_IMDB_URL=[SERIE_IMDB_URL]
        CHARACTERS_PATH=os.path.join(DATA_PATH,SERIE_URI,'characters.txt')
        IMAGE_PATH=os.path.join(DATA_PATH,SERIE_URI,'images')

        main(SERIE_URI,SERIE_IMDB_URL,IMAGE_PATH,CHARACTERS_PATH,N_COL,SEPARATOR,IMAGE_FORMAT)
