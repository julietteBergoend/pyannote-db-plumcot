#!/usr/bin/env python
# coding: utf-8
"""
Fuses outputs of pyannote.audio and pyannote.video models

Usage:
    multimodal.py fuse <serie_uri.task.protocol> <validate_dir> [--set=<set>]
    multimodal.py map <serie_uri.task.protocol> <validate_dir> [--set=<set>]
    multimodal.py -h | --help

Arguments:
    <serie_uri.task.protocol>     Experimental protocol (e.g. "Friends.SpeakerDiarization.FA-UEM")
    <validate_dir>                Output of pyannote.audio

Options:
    --set=<set>                   one of 'train', 'development', 'test', as defined in pyannote.database
                                  Defaults to 'test'.
    -h --help                     Show this screen.
"""
# Dependencies

import os
from docopt import docopt

from pyannote.database.util import load_rttm
from pyannote.video.face.clustering import FaceClustering
from pyannote.metrics.diarization import DiarizationErrorRate
from images import CLUSTERING_THRESHOLD
DATA_PATH=os.path.join("Plumcot","data")

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
    audio_hypothesis, face_id=map(video_features_path,audio_hypothesis,file_uri)
    fusion=audio_hypothesis.crop(face_id,mode=mode)

    return fusion

def map(video_features_path,audio_hypothesis,file_uri):
    """Maps outputs of pyannote.audio and pyannote.video models

    Parameters:
    -----------
    video_features_path: str
        Path to the video features (.npy) file as defined in pyannote.video
    audio_hypothesis: Annotation
        hypothesis made by the audio model
    file_uri: str
        uri of the file you're interested in (used to filter out audio_hypothesis)
    """
    clustering = FaceClustering()
    #TODO : move the preprocess (i.e. npy to pyannote) to some other place ?
    face_id, _ = clustering.model.preprocess(video_features_path,CLUSTERING_THRESHOLD)

    optimal_mapping=DiarizationErrorRate().optimal_mapping(face_id, audio_hypothesis)
    mapped_hypothesis=audio_hypothesis.rename_labels(mapping=optimal_mapping)

    return mapped_hypothesis, face_id

def main(args):
    serie_uri,task,protocol=args['<serie_uri.task.protocol>'].split(".")
    validate_dir=args['<validate_dir>']
    set=args['--set'] if args['--set'] else "test"
    multimodal_path=os.path.join(DATA_PATH,serie_uri,"multimodal")
    video_features=os.path.join(DATA_PATH,serie_uri,"video")
    audio_hypothesis_path=os.path.join(validate_dir,'apply', 'latest',
                                       f"{serie_uri}.{task}.{protocol}.{set}.rttm")
    if not os.path.exists(multimodal_path):
        os.mkdir(multimodal_path)

    audio_hypotheses=load_rttm(audio_hypothesis_path)
    usage='fuse' if args['fuse'] else 'map'
    output_path=os.path.join(multimodal_path,f'{serie_uri}.{task}.{protocol}.{set}.{CLUSTERING_THRESHOLD}.{usage}.rttm')
    if os.path.exists(output_path):
        raise ValueError(f"{output_path} already exists")
    for uri,audio_hypothesis in audio_hypotheses.items():
        print(f"Processing {uri}",end='\r')
        video_features_path=os.path.join(video_features,f"{uri}.npy")
        if args['fuse']:
            output=fuse(video_features_path,audio_hypothesis,uri)
        elif args['map']:
            output,_=map(video_features_path,audio_hypothesis,uri)
        with open(output_path,'a') as file:
            output.write_rttm(file)
    print(f"dumped {output_path}")
if __name__=="__main__":
    args = docopt(__doc__)
    main(args)
