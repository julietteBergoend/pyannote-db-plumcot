#!/usr/bin/env python
# coding: utf-8
"""
Fuses outputs of pyannote.audio and pyannote.video models
"""
from pyannote.database.util import load_rttm
from pyannote.video.face.clustering import FaceClustering
from pyannote.metrics.diarization import DiarizationErrorRate

def fuse(video_features_path,audio_hypothesis_path,file_uri,mode='intersection'):
    """
    Fuses outputs of pyannote.audio and pyannote.video models

    Parameters:
    -----------
    video_features_path: str
        Path to the video features (.npy) file as defined in pyannote.video
    audio_hypothesis_path: str
        Path to the diarization output (.rttm) file as defined in pyannote.audio
    file_uri: str
        uri of the file you're interested in (used to filter out audio_hypothesis)
    mode: str
        See `Annotation.crop`
    """
    clustering = FaceClustering()
    #TODO : move the preprocess (i.e. npy to pyannote) to some other place ?
    face_id, _ = clustering.model.preprocess(video_features_path)
    
    audio_hypothesis=load_rttm(audio_hypothesis_path)[file_uri]

    optimal_mapping=DiarizationErrorRate().optimal_mapping(face_id, audio_hypothesis)
    audio_hypothesis=audio_hypothesis.rename_labels(mapping=optimal_mapping)

    fusion=audio_hypothesis.crop(face_id,mode=mode)

    return fusion
