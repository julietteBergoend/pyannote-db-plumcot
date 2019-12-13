#!/usr/bin/env python
# coding: utf-8
"""
Fuses outputs of pyannote.audio and pyannote.video models

Usage:
    multimodal.py <serie_uri> [--set=<set>]
    multimodal.py -h | --help

Arguments:
    <serie_uri>     One of the series normalized name defined in Plumcot/data/series.txt

Options:
    --set=<set>     one of 'train', 'development', 'test', as defined in pyannote.database
                    Defaults to 'test'.
    -h --help       Show this screen.
"""
# Dependencies

import os
from docopt import docopt

from pyannote.database.util import load_rttm
from pyannote.video.face.clustering import FaceClustering
from pyannote.metrics.diarization import DiarizationErrorRate
from images import CLUSTERING_THRESHOLD

def fuse(video_features_path,audio_hypothesis,file_uri,mode='intersection'):
    """
    Fuses outputs of pyannote.audio and pyannote.video models

    Parameters:
    -----------
    video_features_path: str
        Path to the video features (.npy) file as defined in pyannote.video
    audio_hypothesis: Annotation
        hypothesis made by the audio model
    file_uri: str
        uri of the file you're interested in (used to filter out audio_hypothesis)
    mode: str
        See `Annotation.crop`
    """

    clustering = FaceClustering()
    #TODO : move the preprocess (i.e. npy to pyannote) to some other place ?
    face_id, _ = clustering.model.preprocess(video_features_path,CLUSTERING_THRESHOLD)

    optimal_mapping=DiarizationErrorRate().optimal_mapping(face_id, audio_hypothesis)
    audio_hypothesis=audio_hypothesis.rename_labels(mapping=optimal_mapping)

    fusion=audio_hypothesis.crop(face_id,mode=mode)
    return fusion

def main(audio_hypothesis_path,video_features,output_path,
    DATABASE,TASK,PROTOCOL,set):
    """
    audio_hypothesis_path: str
        Path to the diarization output (.rttm) file as defined in pyannote.audio
    """
    if not os.path.exists(output_path):
        os.mkdir(output_path)
    audio_hypotheses=load_rttm(audio_hypothesis_path)
    for uri,audio_hypothesis in audio_hypotheses.items():
        print(f"Fusing {uri}",end='\r')
        video_features_path=os.path.join(video_features,f"{uri}.npy")
        fusion=fuse(video_features_path,audio_hypothesis,uri)
        with open(os.path.join(output_path,f'{DATABASE}.{TASK}.{PROTOCOL}.{set}.{CLUSTERING_THRESHOLD}.rttm'),'a') as file:
            fusion.write_rttm(file)

if __name__=="__main__":
    args = docopt(__doc__)
    serie_uri=args['<serie_uri>']
    DATABASE=f"Plumcot-{serie_uri}"
    TASK="SpeakerDiarization"
    PROTOCOL="UEM"
    set=args['--set'] if args['--set'] else "test"
    DATA_PATH=os.path.join("Plumcot","data")
    OUTPUT_PATH=os.path.join(DATA_PATH,serie_uri,"multimodal")
    VIDEO_FEATURES=os.path.join(DATA_PATH,serie_uri,"video")
    AUDIO_HYPOTHESIS_PATH=("/vol/work/lerner/baseline/dia/Plumcot-Friends-Adversarial/"
                           "der_uem/train/Plumcot-Friends.SpeakerDiarization.UEM.development/"
                           f"/apply/latest/{DATABASE}.{TASK}.{PROTOCOL}.{set}.rttm")

    main(AUDIO_HYPOTHESIS_PATH,VIDEO_FEATURES,OUTPUT_PATH,
        DATABASE,TASK,PROTOCOL,set)
