#!/usr/bin/env python
# coding: utf-8

"""
Extracts features from images given IMDB-compliant JSON file,
    described in `CONTRIBUTING.md` (scraped in `image_scraping`)
"""

# Dependencies

import os
from pathlib import Path
from shutil import copyfile

## ML/image processing
import imageio
## core
import numpy as np
## clustering
from pyannote.core.utils.distance import pdist
from pyannote.core.utils.hierarchy import linkage, fcluster_auto
from pyannote.video import Face
from pyannote.video.utils.scale_frame import scale_up_bbox, rectangle_to_bbox, \
    parts_to_landmarks
from scipy.cluster.hierarchy import fcluster
from scipy.spatial.distance import squareform

# Hyperparameters are defined in scripts/images.py
MODEL_NAME = "dlib_face_recognition_resnet_model_v1"
DLIB_MODELS = "/people/lerner/pyannote/pyannote-video/dlib-models"
DLIB_EMBEDDING = os.path.join(DLIB_MODELS, f"{MODEL_NAME}.dat")
DLIB_LANDMARKS = os.path.join(DLIB_MODELS, "shape_predictor_68_face_landmarks.dat")
DLIB_THRESHOLD = 0.6  # threshold for clustering, see https://github.com/davisking/dlib-models
MIN_IMAGES = 5
EMBEDDING_DIM = 128
EMBEDDING_DTYPE = ('embeddings', 'float64', (EMBEDDING_DIM,))
BBOX_DTYPE = ('bbox', 'float64', (4,))
LANDMARKS_DTYPE = ('landmarks', 'float64', (68, 2))
CLUSTERING_THRESHOLD = DLIB_THRESHOLD  # 'auto'
CLUSTERING_METHOD = 'complete'
KEEP_IMAGE_TYPES = {'still_frame'}


def extract_image(rgb, landmarks_model, embedding_model, output,
                  return_landmarks=False, return_embedding=False):
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
    face = Face(landmarks=landmarks_model, embedding=embedding_model)
    faces = []
    frame_height = rgb.shape[0]
    frame_width = rgb.shape[1]
    for rectangle in face(rgb):
        bbox = rectangle_to_bbox(rectangle, frame_width, frame_height)
        result = (bbox,)
        if return_landmarks or return_embedding:
            landmarks = face.get_landmarks(rgb, rectangle)
            if return_landmarks:
                landmarks = parts_to_landmarks(landmarks, frame_width, frame_height)
                result += (landmarks,)
            if return_embedding:
                embedding = face.get_embedding(rgb, landmarks)
                result += (embedding,)
        faces.append(result)
    face_dtype = [BBOX_DTYPE]
    if return_landmarks:
        face_dtype += [LANDMARKS_DTYPE]
    if return_embedding:
        face_dtype += [EMBEDDING_DTYPE]
    faces = np.array(
        faces,
        dtype=face_dtype
    )
    np.save(output, faces)


def image_to_output_path(image_path, MODEL_NAME):
    dir_path, file_name = os.path.split(image_path)
    file_uri = os.path.splitext(file_name)[0]
    # HACK should not be necessary if images have been scrapped with a low enough MAX_FILE_NAME_LENGTH
    if len(file_uri) > 128:
        names, counter = file_uri.split(".")
        names = names[:128] + "#trim#"
        file_uri = f"{names}.{counter}"
    output_path = os.path.join(dir_path, f"{MODEL_NAME}.{file_uri}.npy")
    return output_path


def compute_features(image_jsons, MODEL_NAME, DLIB_LANDMARKS, DLIB_EMBEDDING):
    grayscale = 0
    no_image = 0
    not_exists = 0
    for i, image_json in enumerate(image_jsons['allImages']):
        print((
            f"\rimage {i + 1}/{image_jsons['totalImageCount']}."
        ), end="                    ")
        image_path = image_json.get("path")
        if image_path is not None:
            image_path = image_path[0]
            if not os.path.exists(image_path):
                not_exists += 1
                continue
            else:
                rgb = imageio.imread(image_path)
                if len(rgb.shape) == 2:
                    grayscale += 1
                    continue  # dlib doesn't handle grayscale images
        else:
            no_image += 1
            continue
        output_path = image_to_output_path(image_path, MODEL_NAME)
        extract_image(rgb, landmarks_model=DLIB_LANDMARKS, embedding_model=DLIB_EMBEDDING,
                      output=output_path,
                      return_landmarks=False, return_embedding=True)

        # update features path per image
        image_jsons['allImages'][i]["features"] = [output_path]
        for image_path in image_json['path'][1:]:
            other_output_path = image_to_output_path(image_path, MODEL_NAME)
            copyfile(output_path, other_output_path)
            image_jsons['allImages'][i]["features"].append(other_output_path)

        # update features path per character
        feature_object = {
            "path": output_path,
            "model_name": MODEL_NAME,
            "imageType": image_json['imageType']
        }
        characters = image_json['label']
        for character in characters:
            if "features" in image_jsons['characters'][character]:
                image_jsons['characters'][character]["features"].append(feature_object)
            else:
                image_jsons['characters'][character]["features"] = [feature_object]
    print((
        f"\nThere are {grayscale} grayscale images over {image_jsons['totalImageCount'] - no_image - not_exists}.\n"
        f"Over {image_jsons['totalImageCount']} images, {not_exists} do not exist "
        f"and {no_image} were never scraped because of a lack of labelling."
    ))
    return image_jsons


def compute_references(image_jsons, IMAGE_PATH, t=0.6, method='complete',
                       KEEP_IMAGE_TYPES=None, keep_faces=False):
    """
    Clusters over every image in image_jsons
    then assigns to every cluster the most recurring label in the caption
    Starts with the biggest clusters first
    Parameters:
    -----------
    image_jsons: dict
        described in `CONTRIBUTING.md`, it contains the path towards precomputed features for every character
    IMAGE_PATH : Path
        something like '/path/to/data/serie/images'
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
    features = []
    save_labels = []
    if keep_faces:
        import matplotlib.pyplot as plt
        faces = []

    # Clusters over every image in image_jsons
    for i, image in enumerate(image_jsons['allImages']):
        print((f"\rimage {i + 1}/{image_jsons['totalImageCount']}."),
              end="                    ")
        if 'features' not in image:
            continue
        if KEEP_IMAGE_TYPES is not None and image['imageType'] not in KEEP_IMAGE_TYPES:
            continue
        if not Path(image['features'][0]).exists():
            continue
        if keep_faces:
            rgb = imageio.imread(image['path'][0])
            frame_height = rgb.shape[0]
            frame_width = rgb.shape[1]
        # this way we skip those that are empty (because no (frontal) face was detected)
        for feature in np.load(image['features'][0]):
            features.append(feature["embeddings"])
            save_labels.append(image['label'])
            if keep_faces:
                left, top, right, bottom = scale_up_bbox(feature["bbox"], frame_width,
                                                         frame_height)
                faces.append(rgb[top:bottom, left:right])
    features = np.vstack(features)
    # clustering
    Z = linkage(features, method=method, metric='euclidean')
    if t == 'auto':
        clustering = fcluster_auto(features, Z, metric='euclidean')
    else:
        clustering = fcluster(Z, t, criterion='distance')
    unique, counts = np.unique(clustering, return_counts=True)

    # assigns to every cluster the most recurring label in the caption
    assigned_labels = []
    unassigned_clusters = []
    sorted_counts = np.sort(np.unique(counts))[::-1]
    keep_centroid = []

    # start with the biggest clusters
    for count in sorted_counts:
        for cluster in np.where(counts == count)[0]:
            # get the indexes of the cluster
            cluster_i = np.where(clustering == unique[cluster])[0]
            # get the labels associated to the cluster
            cluster_labels = np.array(save_labels)[cluster_i]
            # flatten the labels
            flat_cluster_labels = np.array(
                [label for labels in cluster_labels for label in labels])
            unique_labels, count_labels = np.unique(flat_cluster_labels,
                                                    return_counts=True)
            # assign the most reccuring label to the cluster
            cluster_label = unique_labels[np.argmax(count_labels)]
            # except if we already assigned it to a bigger cluster
            if cluster_label in assigned_labels:
                unassigned_clusters.append(cluster)
                continue

            # save reference and update image_jsons
            str_KEEP_IMAGE_TYPES = ".".join(
                KEEP_IMAGE_TYPES) if KEEP_IMAGE_TYPES is not None else str(
                KEEP_IMAGE_TYPES)
            output_path = os.path.join(IMAGE_PATH, cluster_label,
                                       f'{str_KEEP_IMAGE_TYPES}.{MODEL_NAME}.{cluster_label}.{method}.{t}.references.npy')
            np.save(output_path, features[cluster_i])
            if "references" in image_jsons['characters'][cluster_label]:
                image_jsons['characters'][cluster_label]["references"].append(output_path)
            else:
                image_jsons['characters'][cluster_label]["references"] = [output_path]
            assigned_labels.append(cluster_label)
            if keep_faces:
                # 1. keep centroid
                distance_from_cluster = np.mean(
                    squareform(pdist(features[cluster_i], metric='euclidean')), axis=0)
                centroid_face = faces[cluster_i[np.argmin(distance_from_cluster)]]
                keep_centroid.append(centroid_face)

                # 2. save face grid
                plt.figure(figsize=(16, 16))
                grid_path = os.path.join(IMAGE_PATH, cluster_label,
                                         f'{str_KEEP_IMAGE_TYPES}.{MODEL_NAME}.{cluster_label}.{method}.{t}.grid.png')
                cols = int(np.sqrt(len(cluster_i))) + 1
                for i, j in enumerate(cluster_i):
                    if faces[j].size == 0:
                        continue
                    plt.subplot(cols, cols, i + 1)
                    plt.imshow(faces[j])
                    plt.axis('off')
                plt.savefig(grid_path)
    print(f"assigned {len(assigned_labels)} labels over {len(unique)} clusters")
    print(f"those cluster were not assigned any label :\n{unassigned_clusters}")
    if keep_faces:
        # save centroids
        plt.figure(figsize=(16, 16))
        cols = int(np.sqrt(len(assigned_labels))) + 1
        for i, label in enumerate(assigned_labels):
            if keep_centroid[i].size == 0:
                continue
            plt.subplot(cols, cols, i + 1)
            plt.title(label[:12] + str(image_jsons['characters'][label]['count']))
            centroid_path = os.path.join(IMAGE_PATH, label,
                                         f'{str_KEEP_IMAGE_TYPES}.{MODEL_NAME}.{label}.{method}.{t}.centroid.png')
            imageio.imwrite(centroid_path, keep_centroid[i])
            plt.imshow(keep_centroid[i])
            image_jsons['characters'][label]["centroid"] = centroid_path
            plt.axis('off')
        plt.savefig(os.path.join(IMAGE_PATH, "centroids.png"))

    return image_jsons
