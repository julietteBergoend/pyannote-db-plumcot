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

## clustering
from pyannote.core.utils.distance import cdist,pdist
from scipy.spatial.distance import squareform
from scipy.cluster.hierarchy import fcluster
from pyannote.core.utils.hierarchy import linkage,fcluster_auto

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

def compute_features(image_jsons,MODEL_NAME,DLIB_LANDMARKS,DLIB_EMBEDDING):
    grayscale=0
    no_image=0
    not_exists=0
    for i,image_json in enumerate(image_jsons['allImages']):
        print((
            f"\rimage {i+1}/{image_jsons['totalImageCount']}."
        ),end="                    ")
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
        image_jsons['allImages'][i]["features"]=[output_path]
        for image_path in image_json['path'][1:]:
            other_output_path=image_to_output_path(image_path,MODEL_NAME)
            copyfile(output_path,other_output_path)
            image_jsons['allImages'][i]["features"].append(other_output_path)

        #update features path per character
        feature_object={
            "path":output_path,
            "model_name":MODEL_NAME,
            "imageType":image_json['imageType']
        }
        characters=image_json['label']
        for character in characters:
            if "features" in image_jsons['characters'][character]:
                image_jsons['characters'][character]["features"].append(feature_object)
            else:
                image_jsons['characters'][character]["features"]=[feature_object]
    print((
        f"\nThere are {grayscale} grayscale images over {image_jsons['totalImageCount']-no_image-not_exists}.\n"
        f"Over {image_jsons['totalImageCount']} images, {not_exists} do not exist "
        f"and {no_image} were never scraped because of a lack of labelling."
    ))
    return image_jsons

def compute_reference(character,t=0.6,method='complete',KEEP_IMAGE_TYPES=None,keep_faces=False):
    """
    Cluster over features then save the biggest cluster as reference.
    The file should be named like `<model_name>.<MIN_IMAGES>.<character_uri>.npy`.
    It should contain one line per reference embedding.

    Parameters:
    -----------
    character: dict
        described in `CONTRIBUTING.md`, it contains the path towards precomputed features.
    t: float, str, optional
        Threshold to apply when forming flat clusters.
        If 'auto' (case-sensitive) then we use pyannote.core.utils.hierarchy.fcluster_auto
            to automatically determine the threshold
        Defaults to 0.6 because of dlib (see https://github.com/davisking/dlib-models)
    method: str, optional
        Method used to calculate the distance between the
        newly formed cluster :math:`u` and each :math:`v`
        see scipy.cluster.hierarchy.linkage
    KEEP_IMAGE_TYPES: set, optional
        Restricts the cluster to features which were computed on a given imageType (e.g. 'still_frame')
        See `CONTRIBUTING.md`
        Defaults to keep all features (i.e. None)
    keep_faces: bool, optional
        keep track of rgb image of faces (cropped with the bounding box) for debugging and visualization

    Returns:
    --------
    references: numpy array,
        contains one embedding per line
    faces: list, optional
        a list of all faces in the character images
        Returns only if keep_faces
    """
    features=[]
    if keep_faces:
        faces=[]
    for feature_object,image_file in zip(character['features'],character['paths']):
        if KEEP_IMAGE_TYPES is not None:
            if feature_object['imageType'] not in KEEP_IMAGE_TYPES:
                continue
        if keep_faces:
            rgb=imageio.imread(image_file)
            frame_height=rgb.shape[0]
            frame_width=rgb.shape[1]

        for feature in np.load(feature_object['path']):#this way we skip those that are empty (because no (frontal) face was detected)
            features.append(feature["embeddings"])
            if keep_faces:
                left, top, right, bottom=scale_up_bbox(feature["bbox"],frame_width,frame_height)
                faces.append(rgb[top:bottom,left:right])
    if len(features) < 2:
        return None
    features=np.vstack(features)

    #clustering
    Z=linkage(features,method=method, metric='euclidean')
    if t == 'auto':
        clustering=fcluster_auto(features,Z, metric='euclidean')
    else:
        clustering=fcluster(Z,t,criterion='distance')
    unique, counts = np.unique(clustering, return_counts=True)
    biggest_cluster=unique[np.argmax(counts)]
    references_i=np.where(clustering==biggest_cluster)[0]
    references=features[references_i]
    if keep_faces:
        return references,faces
    return references
def compute_references(image_jsons,t=0.6,method='complete',KEEP_IMAGE_TYPES=None,keep_faces=False):
    """
    Clusters over every image in image_jsons
    then assigns to every cluster the most recurring label in the caption
    Starts with the biggest clusters first
    Parameters:
    -----------
    image_jsons: dict
        described in `CONTRIBUTING.md`, it contains the path towards precomputed features for every character
    t: float, str, optional
        Threshold to apply when forming flat clusters.
        If 'auto' (case-sensitive) then we use pyannote.core.utils.hierarchy.fcluster_auto
            to automatically determine the threshold
        Defaults to 0.6 because of dlib (see https://github.com/davisking/dlib-models)
    method: str, optional
        Method used to calculate the distance between the
        newly formed cluster :math:`u` and each :math:`v`
        see scipy.cluster.hierarchy.linkage
    KEEP_IMAGE_TYPES: set, optional
        Restricts the cluster to features which were computed on a given imageType (e.g. 'still_frame')
        See `CONTRIBUTING.md`
        Defaults to keep all features (i.e. None)
    keep_faces: bool, optional
        keep track of rgb image of faces (cropped with the bounding box)
        for debugging and visualization.
        Heavy in memory.
        Defaults to False.
    Returns:
    --------
    image_jsons: dict
        updated database with the path towards the reference embedding
    """
    features=[]
    save_labels=[]
    if keep_faces:
        import matplotlib.pyplot as plt
        faces=[]

    #Clusters over every image in image_jsons
    for i,image in enumerate(image_jsons['allImages']):
        print((
                f"\rimage {i+1}/{image_jsons['totalImageCount']}."
            ),end="                    ")
        if 'features' not in image:
            continue
        if KEEP_IMAGE_TYPES is not None:
            if image['imageType'] not in KEEP_IMAGE_TYPES:
                continue
        if keep_faces:
            rgb=imageio.imread(image['path'][0])
            frame_height=rgb.shape[0]
            frame_width=rgb.shape[1]
        for feature in np.load(image['features'][0]):#this way we skip those that are empty (because no (frontal) face was detected)
            features.append(feature["embeddings"])
            save_labels.append(image['label'])
            if keep_faces:
                left, top, right, bottom=scale_up_bbox(feature["bbox"],frame_width,frame_height)
                faces.append(rgb[top:bottom,left:right])
    features=np.vstack(features)
    #clustering
    Z=linkage(features,method=method, metric='euclidean')
    if t == 'auto':
        clustering=fcluster_auto(features,Z, metric='euclidean')
    else:
        clustering=fcluster(Z,t,criterion='distance')
    unique, counts = np.unique(clustering, return_counts=True)

    #assigns to every cluster the most recurring label in the caption
    assigned_labels=[]
    unassigned_clusters=[]
    sorted_counts=np.sort(np.unique(counts))[::-1]
    keep_centroid=[]

    for count in sorted_counts:
        for cluster in np.where(counts==count)[0]:#start with the biggest clusters
            cluster_i=np.where(clustering==unique[cluster])[0]#get the indexes of the cluster
            cluster_labels=np.array(save_labels)[cluster_i]#get the labels associated to the cluster
            #flatten the labels
            flat_cluster_labels = np.array([label for labels in cluster_labels for label in labels])
            unique_labels, count_labels = np.unique(flat_cluster_labels, return_counts=True)
            #assign the most reccuring label to the cluster
            cluster_label=unique_labels[np.argmax(count_labels)]
            #except if we already assigned it to a bigger cluster
            if cluster_label in assigned_labels:
                unassigned_clusters.append(cluster)
                continue

            #save reference and update image_jsons
            str_KEEP_IMAGE_TYPES = ".".join(KEEP_IMAGE_TYPES) if KEEP_IMAGE_TYPES is not None else str(KEEP_IMAGE_TYPES)
            output_path=os.path.join(IMAGE_PATH,cluster_label,f'{str_KEEP_IMAGE_TYPES}.{MODEL_NAME}.{cluster_label}.{method}.{t}.references.npy')
            np.save(output_path,features[cluster_i])
            if "references" in image_jsons['characters'][cluster_label]:
                image_jsons['characters'][cluster_label]["references"].append(output_path)
            else:
                image_jsons['characters'][cluster_label]["references"]=[output_path]
            assigned_labels.append(cluster_label)
            if keep_faces:
                distance_from_cluster=np.mean(squareform(pdist(features[cluster_i],metric='euclidean')),axis=0)
                centroid_face=faces[cluster_i[np.argmin(distance_from_cluster)]]
                keep_centroid.append(centroid_face)
    print(f"assigned {len(assigned_labels)} labels over {len(unique)} clusters")
    print(f"those cluster were not assigned any label :\n{unassigned_clusters}")
    if keep_faces:
        plt.figure(figsize=(16,16))
        for i,label in enumerate(assigned_labels[:81]):
            plt.subplot(9,9,i+1)
            plt.title(label[:12]+str(image_jsons['characters'][label]['count']))
            plt.imshow(keep_centroid[i])
            #plt.imshow(first_faces[i])
            plt.axis('off')
        plt.show()
        return image_jsons, faces
    return image_jsons

def compute_references_per_character(image_jsons,t=0.6,method='complete',MIN_IMAGES=1,KEEP_IMAGE_TYPES=None):
    """
    Cluster over each character folder if it has at least `MIN_IMAGES` images features in it
        then save the biggest cluster as the character reference.
    The file should be named like `<model_name>.<MIN_IMAGES>.<character_uri>.npy`.
    It should contain one line per reference embedding.

    Parameters:
    -----------
    image_jsons: dict
        described in `CONTRIBUTING.md`, it contains the path towards precomputed features for every character
    t: float, str, optional
        Threshold to apply when forming flat clusters.
        If 'auto' (case-sensitive) then we use pyannote.core.utils.hierarchy.fcluster_auto
            to automatically determine the threshold
        Defaults to 0.6 because of dlib (see https://github.com/davisking/dlib-models)
    method: str, optional
        Method used to calculate the distance between the
        newly formed cluster :math:`u` and each :math:`v`
        see scipy.cluster.hierarchy.linkage
    MIN_IMAGES: int, optional
        compute the references embeddings of every character which has at least MIN_IMAGES.
        Defaults to compute references for every character which has an image (i.e. 1)
    KEEP_IMAGE_TYPES: set, optional
        Restricts the cluster to features which were computed on a given imageType (e.g. 'still_frame')
        See `CONTRIBUTING.md`
        Defaults to keep all features (i.e. None)
    Returns:
    --------
    image_jsons: dict
        updated database with the path towards the reference embedding
    """
    warnings.warn("This function has been deprecated in favor of compute_references")
    n_characters=len(image_jsons['characters'])
    for i,(name,character) in enumerate(image_jsons['characters'].items()):
        print(f"\rprocessing {name} ({i}/{n_characters})",end="                           ")
        #using len(character['features']) instead of characer['count']
        #  as some images do not contain frontal face or are grayscale
        if 'features' in character and len(character['features'])>=MIN_IMAGES:
            references=compute_reference(character,t,method,KEEP_IMAGE_TYPES,keep_faces=False)
            str_KEEP_IMAGE_TYPES = ".".join(KEEP_IMAGE_TYPES) if KEEP_IMAGE_TYPES is not None else str(KEEP_IMAGE_TYPES)
            output_path=os.path.join(IMAGE_PATH,name,f'{str_KEEP_IMAGE_TYPES}.{MODEL_NAME}.{name}.{method}.references.npy')
            np.save(output_path,references)
            if "references" in character:
                image_jsons['characters'][name]["references"].append(output_path)
            else:
                image_jsons['characters'][name]["references"]=[output_path]
    return image_jsons

def main(image_jsons,MODEL_NAME,DLIB_LANDMARKS,DLIB_EMBEDDING,IMAGE_PATH,
    CLUSTERING_THRESHOLD,CLUSTERING_METHOD,KEEP_IMAGE_TYPES):
    image_jsons=compute_features(image_jsons,MODEL_NAME,DLIB_LANDMARKS,DLIB_EMBEDDING)
    image_jsons=compute_references(image_jsons,CLUSTERING_THRESHOLD,CLUSTERING_METHOD,KEEP_IMAGE_TYPES,keep_faces=False)
    with open(os.path.join(IMAGE_PATH,"images.json"),"w") as file:
        json.dump(image_jsons,file)
    print("\ndone computing features and references ;)")

if __name__ == '__main__':
    from images import MODEL_NAME,DLIB_LANDMARKS,DLIB_EMBEDDING,IMAGE_PATH,CLUSTERING_THRESHOLD,CLUSTERING_METHOD,KEEP_IMAGE_TYPES
    with open(os.path.join(IMAGE_PATH,"images.json"),"r") as file:
        image_jsons=json.load(file)
    main(image_jsons,MODEL_NAME,DLIB_LANDMARKS,DLIB_EMBEDDING,IMAGE_PATH,
        CLUSTERING_THRESHOLD,CLUSTERING_METHOD,KEEP_IMAGE_TYPES)
