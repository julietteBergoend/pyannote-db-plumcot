#!/usr/bin/env python
# coding: utf-8

"""Usage:
images.py [options]
images.py scrap [options]
images.py features [options]
images.py references [options]
images.py visualize [options]


Options:
--uri=<uri> Only process this serie, defaults to process all

* main: do 'scrap', 'features' and 'references'
* scrap: Get images from IMDB character's page given a list of urls and character's names
    (following the format of `characters.txt` described in CONTRIBUTING.md)
* features: Then extracts features off theses images.
* references: Then cluster image features, tag clusters based on image caption
           and compute average embedding for (labelled) cluster to keep as reference
* visualize: same as 'references' but saves figure with cropped faces
"""

# Dependencies
from docopt import docopt
import json
from pathlib import Path
from image_scraping import main as scrap
from image_features import *

import Plumcot as PC

# Hyperparameters

## core
N_COL = 5  # the CHARACTERS file should have 5 columns, separated by SEPARATOR
SEPARATOR = ","

DATA_PATH = Path(PC.__file__).parent / "data"
IMAGE_FORMAT = "jpg"

## web
IMDB_URL = "https://www.imdb.com"
THUMBNAIL_CLASS = "titlecharacters-image-grid__thumbnail-link"
IMAGE_CLASS = "pswp__img"

if __name__ == '__main__':
    args = docopt(__doc__)
    uri = args['--uri']
    main = not (args['scrap'] or args['features'] or args['references'] or args['visualize'])
    with open(os.path.join(DATA_PATH, "series.txt")) as file:
        series = file.readlines()
    for serie in series:
        SERIE_URI, _, SERIE_IMDB_URL, _, _ = serie.split(",")
        if SERIE_URI != uri and uri is not None:
            continue
        if SERIE_IMDB_URL == '':  # film -> open episode:
            SERIE_IMDB_URL = np.loadtxt(
                os.path.join(DATA_PATH, SERIE_URI, 'episodes.txt'), dtype=str,
                delimiter=SEPARATOR)[:, 2]
        else:  # only one but turn it to a list so we can iterate it
            SERIE_IMDB_URL = [SERIE_IMDB_URL]
        CHARACTERS_PATH = os.path.join(DATA_PATH, SERIE_URI, 'characters.txt')
        IMAGE_PATH = Path(DATA_PATH, SERIE_URI, 'images')
        if args['scrap'] or main:
            scrap(SERIE_URI, SERIE_IMDB_URL, IMAGE_PATH, CHARACTERS_PATH, N_COL, SEPARATOR, IMAGE_FORMAT)
        if args['features'] or main:
            with open(os.path.join(IMAGE_PATH, "images.json"), "r") as file:
                image_jsons = json.load(file)
            image_jsons = compute_features(image_jsons, MODEL_NAME, DLIB_LANDMARKS, DLIB_EMBEDDING)
            with open(os.path.join(IMAGE_PATH, "images.json"), "w") as file:
                json.dump(image_jsons, file)
        if args['references'] or main:
            with open(os.path.join(IMAGE_PATH, "images.json"), "r") as file:
                image_jsons = json.load(file)
            image_jsons = compute_references(image_jsons, IMAGE_PATH, CLUSTERING_THRESHOLD,
                                             CLUSTERING_METHOD, KEEP_IMAGE_TYPES, keep_faces=False)
            with open(os.path.join(IMAGE_PATH, "images.json"), "w") as file:
                json.dump(image_jsons, file)
        if args['visualize'] or main:
            with open(os.path.join(IMAGE_PATH, "images.json"), "r") as file:
                image_jsons = json.load(file)
            image_jsons = compute_references(image_jsons, IMAGE_PATH, CLUSTERING_THRESHOLD,
                                             CLUSTERING_METHOD, KEEP_IMAGE_TYPES, keep_faces=True)
            with open(os.path.join(IMAGE_PATH, "images.json"), "w") as file:
                json.dump(image_jsons, file)
