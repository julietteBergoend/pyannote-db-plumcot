#!/usr/bin/env python
# coding: utf-8
"""
Fuses outputs of pyannote.audio and pyannote.video models
"""
# Dependencies

import os

from pyannote.database.util import load_rttm
from pyannote.video.face.clustering import FaceClustering
from pyannote.metrics.diarization import DiarizationErrorRate

#hyper parameters

SERIE_URI="Friends"
DATABASE=f"Plumcot-{SERIE_URI}"
TASK="SpeakerDiarization"
PROTOCOL="UEM"
SET="test"
DATA_PATH=os.path.join("Plumcot","data")
OUTPUT_PATH=os.path.join(DATA_PATH,SERIE_URI,"multimodal")
VIDEO_FEATURES=os.path.join(DATA_PATH,SERIE_URI,"video")
AUDIO_HYPOTHESIS_PATH=f"/vol/work/lerner/baseline/dia/Plumcot-Friends-Adversarial/der_uem/train/Plumcot-Friends.SpeakerDiarization.UEM.development/{DATABASE}.{TASK}.{PROTOCOL}.{SET}.rttm"

def write_rttm(self, file):
    """Write annotation to "rttm" file
    Parameters
    ----------
    file : file object
    """
    for segment, _, label in self.itertracks(yield_label=True):
        line = (
            f'SPEAKER {self.uri} 1 {segment.start:.3f} {segment.duration:.3f} '
            f'<NA> <NA> {label} <NA> <NA>\n'
        )
        file.write(line)

def crop(self, support, mode='intersection'):
    """Crop annotation to new support

    Parameters
    ----------
    support : Segment, Timeline or Annotation
        If `support` is a `Timeline`, its support is used.
        Else, if `support` is an `Annotation` cropping is done only if
            both annotations share the same labels
    mode : {'strict', 'loose', 'intersection'}, optional
        Controls how segments that are not fully included in `support` are
        handled. 'strict' mode only keeps fully included segments. 'loose'
        mode keeps any intersecting segment. 'intersection' mode keeps any
        intersecting segment but replace them by their actual intersection.

    Returns
    -------
    cropped : Annotation
        Cropped annotation

    Note
    ----
    In 'intersection' mode, the best is done to keep the track names
    unchanged. However, in some cases where two original segments are
    cropped into the same resulting segments, conflicting track names are
    modified to make sure no track is lost.

    """
    # TODO speed things up by working directly with annotation internals

    cropped = self.__class__(uri=self.uri, modality=self.modality)

    if isinstance(support,Annotation):
        if mode == 'intersection':
            for segment, other_segment in \
                    self.get_timeline(copy=False).co_iter(support.get_timeline(copy=False)):
                label,other_label=self.get_labels(segment),support.get_labels(other_segment)
                labels=label & other_label
                if bool(labels):
                    intersection = segment & other_segment
                    for track,label in zip(self._tracks[segment],labels):
                        track = cropped.new_track(intersection,
                                                  candidate=track)
                        cropped[intersection, track] = label

            return cropped
        else:
            raise NotImplementedError("unsupported mode: '%s'" % mode)
    else:
        raise TypeError(f"got an invalid type for support: {type(support)}")
        
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
    face_id, _ = clustering.model.preprocess(video_features_path)

    optimal_mapping=DiarizationErrorRate().optimal_mapping(face_id, audio_hypothesis)
    audio_hypothesis=audio_hypothesis.rename_labels(mapping=optimal_mapping)

    #fusion=audio_hypothesis.crop(face_id,mode=mode)
    fusion=crop(audio_hypothesis,face_id,mode=mode)
    return fusion

def main(audio_hypothesis_path,video_features,output_path,
    DATABASE,TASK,PROTOCOL,SET):
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
        with open(os.path.join(output_path,f'{DATABASE}.{TASK}.{PROTOCOL}.{SET}.rttm'),'a') as file:
            #fusion.write_rttm(file)
            write_rttm(fusion,file)

if __name__=="__main__":
    main(AUDIO_HYPOTHESIS_PATH,VIDEO_FEATURES,OUTPUT_PATH,
        DATABASE,TASK,PROTOCOL,SET)
