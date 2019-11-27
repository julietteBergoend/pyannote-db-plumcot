#!/usr/bin/env python
# coding: utf-8

"""
image_scraping: Get images from IMDB character's page given a list of urls and character's names
    (following the format of `characters.txt` described in CONTRIBUTING.md)
image_features: Then extracts features off theses images.
"""
# Dependencies
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
SERIE_URI,_,SERIE_IMDB_URL,_,_=series[5].split(",")
CHARACTERS_PATH=os.path.join(DATA_PATH,SERIE_URI,'characters.txt')
IMAGE_PATH=os.path.join(DATA_PATH,SERIE_URI,'images')
IMAGE_FORMAT="jpg"

## web
IMDB_URL="https://www.imdb.com"
THUMBNAIL_CLASS="titlecharacters-image-grid__thumbnail-link"
IMAGE_CLASS="pswp__img"
SERIE_IMDB_ID=SERIE_IMDB_URL.split("/")[-2]

## ML
MODEL_NAME="dlib_face_recognition_resnet_model_v1"
DLIB_EMBEDDING=f"dlib-models/{MODEL_NAME}.dat"
DLIB_LANDMARKS="dlib-models/shape_predictor_68_face_landmarks.dat"
DLIB_THRESHOLD=0.6#threshold for clustering, see https://github.com/davisking/dlib-models
MIN_IMAGES=5
EMBEDDING_DIM=128
EMBEDDING_DTYPE=('embeddings', 'float64', (EMBEDDING_DIM,))
BBOX_DTYPE=('bbox', 'float64', (4,))

def main(SERIE_URI,SERIE_IMDB_URL,IMAGE_PATH,N_COL,SEPARATOR,
    MODEL_NAME,DLIB_LANDMARKS,DLIB_EMBEDDING,SERIE_IMDB_ID):
    image_jsons=scrap(SERIE_URI,SERIE_IMDB_URL,IMAGE_PATH,N_COL,SEPARATOR)
    image_jsons=compute_references(image_jsons,MODEL_NAME,DLIB_LANDMARKS,DLIB_EMBEDDING,SERIE_IMDB_ID)
    with open(os.path.join(IMAGE_PATH,"images.json"),"w") as file:
        json.dump(image_jsons,file)
    print("\ndone ;)")

if __name__ == '__main__':
    # characters=read_characters(CHARACTERS_PATH,N_COL,SEPARATOR)
    # actor2character={actor:character for character,_,_,actor,_ in characters}
    # with open(os.path.join(IMAGE_PATH,"images.json"),"r") as file:
    #     image_jsons=json.load(file)
    # query_image_from_json(image_jsons,IMAGE_PATH,actor2character,SEPARATOR)
    main(SERIE_URI,SERIE_IMDB_URL,IMAGE_PATH,N_COL,SEPARATOR,
        MODEL_NAME,DLIB_LANDMARKS,DLIB_EMBEDDING,SERIE_IMDB_ID)
