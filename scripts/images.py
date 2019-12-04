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
MODEL_NAME="dlib_face_recognition_resnet_model_v1"
DLIB_MODELS="/people/lerner/pyannote/pyannote-video/dlib-models"
DLIB_EMBEDDING=os.path.join(DLIB_MODELS,f"{MODEL_NAME}.dat")
DLIB_LANDMARKS=os.path.join(DLIB_MODELS,"shape_predictor_68_face_landmarks.dat")
DLIB_THRESHOLD=0.6#threshold for clustering, see https://github.com/davisking/dlib-models
MIN_IMAGES=5
EMBEDDING_DIM=128
EMBEDDING_DTYPE=('embeddings', 'float64', (EMBEDDING_DIM,))
BBOX_DTYPE=('bbox', 'float64', (4,))
CLUSTERING_THRESHOLD=DLIB_THRESHOLD#'auto'
CLUSTERING_METHOD='complete'
KEEP_IMAGE_TYPES={'still_frame'}

def main(SERIE_URI,SERIE_IMDB_URL,IMAGE_PATH,CHARACTERS_PATH,N_COL,SEPARATOR,IMAGE_FORMAT,
    MODEL_NAME,DLIB_LANDMARKS,DLIB_EMBEDDING):
    image_jsons=scrap(SERIE_URI,SERIE_IMDB_URL,IMAGE_PATH,CHARACTERS_PATH,N_COL,SEPARATOR,IMAGE_FORMAT)
    #image_jsons=compute_references(image_jsons,MODEL_NAME,DLIB_LANDMARKS,DLIB_EMBEDDING)
    with open(os.path.join(IMAGE_PATH,"images.json"),"w") as file:
        json.dump(image_jsons,file)
    print("\ndone ;)")

if __name__ == '__main__':
    # characters=read_characters(CHARACTERS_PATH,N_COL,SEPARATOR)
    # actor2character={actor:character for character,_,_,actor,_ in characters}
    # with open(os.path.join(IMAGE_PATH,"images.json"),"r") as file:
    #     image_jsons=json.load(file)
    # query_image_from_json(image_jsons,IMAGE_PATH,actor2character,SEPARATOR)
    for serie in series:
        SERIE_URI,_,SERIE_IMDB_URL,_,_=serie.split(",")
        if SERIE_IMDB_URL=='':#film -> open episode:
            SERIE_IMDB_URL=np.loadtxt(os.path.join(DATA_PATH,SERIE_URI,'episodes.txt'),dtype=str,delimiter=SEPARATOR)[:,2]
        else:#only one but turn it to a list so we can iterate it
            SERIE_IMDB_URL=[SERIE_IMDB_URL]
        CHARACTERS_PATH=os.path.join(DATA_PATH,SERIE_URI,'characters.txt')
        IMAGE_PATH=os.path.join(DATA_PATH,SERIE_URI,'images')

        main(SERIE_URI,SERIE_IMDB_URL,IMAGE_PATH,CHARACTERS_PATH,N_COL,SEPARATOR,IMAGE_FORMAT,
            MODEL_NAME,DLIB_LANDMARKS,DLIB_EMBEDDING)
