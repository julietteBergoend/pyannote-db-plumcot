#!/usr/bin/env python
# coding: utf-8

"""
Extracts features from images given IMDB-compliant JSON file,
    described in `CONTRIBUTING.md` (scraped in `image_scraping`)
"""
# Dependencies

## core
import numpy as np
import os
import json
import warnings
from shutil import copyfile

## ML/image processing
import imageio
from pyannote.video import Face
from pyannote.video.utils.scale_frame import scale_up_bbox, rectangle_to_bbox

def extract_image(rgb,landmarks_model,embedding_model,output,
                 return_landmarks=False,return_embedding=False):
    """Facial features detection for an rgb image
    Parameters
    ----------
    rgb : np.array
        RGB image to be processed
    landmarks : str
        Path to dlib's 68 facial landmarks predictor model.
    embedding : str
        Path to dlib's face embedding model.
    output : str
        Path to features result file (should end with `.npy`).
    return_landmarks : bool
        Whether to save landmarks. Defaults to False.
    return_embedding : bool
        Whether to save embedding. Defaults to False.
    """
    face = Face(landmarks=landmarks_model,embedding=embedding_model)
    faces=[]
    frame_height=rgb.shape[0]
    frame_width=rgb.shape[1]
    for rectangle in face(rgb):
        bbox=rectangle_to_bbox(rectangle,frame_width,frame_height)
        result=(bbox,)
        if return_landmarks or return_embedding:
            landmarks = face.get_landmarks(rgb, rectangle)
            if return_landmarks:
                landmarks=parts_to_landmarks(landmarks,frame_width,frame_height)
                result+=(landmarks,)
            if return_embedding:
                embedding = face.get_embedding(rgb, landmarks)
                result+=(embedding,)
        faces.append(result)
    face_dtype=[BBOX_DTYPE]
    if return_landmarks:
        face_dtype+=[LANDMARKS_DTYPE]
    if return_embedding:
        face_dtype+=[EMBEDDING_DTYPE]
    faces=np.array(
        faces,
        dtype=face_dtype
    )
    np.save(output,faces)

def image_to_output_path(image_path,MODEL_NAME):
    dir_path,file_name=os.path.split(image_path)
    file_uri=os.path.splitext(file_name)[0]
    output_path=os.path.join(dir_path,f"{MODEL_NAME}.{file_uri}.npy")
    return output_path

def compute_features(image_jsons,MODEL_NAME,DLIB_LANDMARKS,DLIB_EMBEDDING,SERIE_IMDB_ID):
    grayscale=0
    no_image=0
    not_exists=0
    for i,image_json in enumerate(image_jsons['mediaviewer']['galleries'][SERIE_IMDB_ID]['allImages']):
        print((
            f"\rimage {i+1}/{image_jsons['mediaviewer']['galleries'][SERIE_IMDB_ID]['totalImageCount']}."
        ),end="")
        image_path=image_json.get("path")
        if image_path is not None:
            image_path=image_path[0]
            if not os.path.exists(image_path):
                not_exists+=1
                continue
            else:
                rgb = imageio.imread(image_path)
                if len(rgb.shape)==2:
                    grayscale+=1
                    continue#dlib doesn't handle grayscale images
        else:
            no_image+=1
            continue
        output_path=image_to_output_path(image_path,MODEL_NAME)
        extract_image(rgb,landmarks_model=DLIB_LANDMARKS,embedding_model=DLIB_EMBEDDING,output=output_path,
                     return_landmarks=False,return_embedding=True)

        #update features path per image
        image_jsons['mediaviewer']['galleries'][SERIE_IMDB_ID]['allImages'][i]["features"]=[output_path]
        for image_path in image_json['path'][1:]:
            other_output_path=image_to_output_path(image_path,MODEL_NAME)
            copyfile(output_path,other_output_path)
            image_jsons['mediaviewer']['galleries'][SERIE_IMDB_ID]['allImages'][i]["features"].append(other_output_path)

        #update features path per character
        feature_object={
            "path":output_path,
            "model_name":MODEL_NAME,
            "imageType":image_json['imageType']
        }
        characters=image_json['label']
        for character in characters:
            if "features" in image_jsons['mediaviewer']['galleries'][SERIE_IMDB_ID]['characters'][character]:
                image_jsons['mediaviewer']['galleries'][SERIE_IMDB_ID]['characters'][character]["features"].append(feature_object)
            else:
                image_jsons['mediaviewer']['galleries'][SERIE_IMDB_ID]['characters'][character]["features"]=[feature_object]
    print((
        f"\nThere are {grayscale} grayscale images over {image_jsons['mediaviewer']['galleries'][SERIE_IMDB_ID]['totalImageCount']-no_image-not_exists}.\n"
        f"Over {image_jsons['mediaviewer']['galleries'][SERIE_IMDB_ID]['totalImageCount']} images, {not_exists} do not exist "
        f"and {no_image} were never scraped because of a lack of labelling."
    ))
    return image_jsons

def main(image_jsons,MODEL_NAME,DLIB_LANDMARKS,DLIB_EMBEDDING,SERIE_IMDB_ID,IMAGE_PATH):
    image_jsons=compute_features(image_jsons,MODEL_NAME,DLIB_LANDMARKS,DLIB_EMBEDDING,SERIE_IMDB_ID)
    with open(os.path.join(IMAGE_PATH,"images.json"),"w") as file:
        json.dump(image_jsons,file)
    print("\ndone computing features ;)")

if __name__ == '__main__':
    #raise NotImplementedError()
    from images import MODEL_NAME,DLIB_LANDMARKS,DLIB_EMBEDDING,SERIE_IMDB_ID,IMAGE_PATH
    with open(os.path.join(IMAGE_PATH,"images.json"),"r") as file:
        image_jsons=json.load(file)
    main(image_jsons,MODEL_NAME,DLIB_LANDMARKS,DLIB_EMBEDDING,SERIE_IMDB_ID,IMAGE_PATH)
