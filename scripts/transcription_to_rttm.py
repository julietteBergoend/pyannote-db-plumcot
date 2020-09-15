"""Converts 'transcription' (or 'entity' if available) from spacy Doc to RTTM file via pyannote Annotation
Also maps speaker identifier to their most common name if requested.
Note that only speech segments will be considered as annotated (i.e. discarded from the UEM).

Usage: transcription_to_rttm.py <protocol> [--common_name --confidence=<threshold>]

Options:
--common_name               Map speaker identifier to their most common name
                            using hand-crafted mapping.
                            If speaker identifier is not in the mapping it will be discarded from the UEM
--confidence=<threshold>    Discard words with a confidence lower than <threshold> from the UEM
                            Defaults to keep all words [Recommended: 0.5]
"""

from docopt import docopt
from tqdm import tqdm
from pathlib import Path
import json

from pyannote.core import Segment, Timeline, Annotation
from pyannote.database import get_protocol
import Plumcot as PC

DATA_PATH = Path(PC.__file__).parent / 'data'
TRANSCRIPT = 'annotated_transcripts'


def transcription_to_annotation(transcription, uri=None, mapping=None, confidence=0.0):
    annotation = Annotation(uri=uri, modality='speaker')
    annotated = Timeline(uri=uri)
    for word in transcription:
        segment = Segment(word._.time_start, word._.time_end)
        # map speaker identifier to common name if mapping else keep identifier
        speaker = mapping.get(word._.speaker) if mapping else word._.speaker
        if speaker and word._.confidence >= confidence:
            annotation[segment, speaker] = speaker
            annotated.add(segment)
    return annotation, annotated


def protocol_to_rttm(protocol, rttm_out, uem_out, mapping=None, confidence=0.0):
    for current_file in tqdm(protocol.files(), desc='Converting transcriptions'):
        transcription = current_file.get('entity', current_file['transcription'])
        uri = current_file['uri']
        annotation, annotated = transcription_to_annotation(transcription, uri,
                                                            mapping, confidence)
        with open(rttm_out, 'a') as file:
            annotation.write_rttm(file)
        with open(uem_out, 'a') as file:
            annotated.write_uem(file)


if __name__ == '__main__':
    args = docopt(__doc__)
    protocol_name = args['<protocol>']
    confidence = float(args['--confidence']) if args['--confidence'] else 0.
    protocol = get_protocol(protocol_name)
    serie, _, _ = protocol_name.split('.')
    output_path = DATA_PATH / serie / TRANSCRIPT
    rttm_out = output_path / f'{protocol_name}.rttm'
    uem_out = output_path / f'{protocol_name}.uem'
    for path in [rttm_out, uem_out]:
        if path.exists():
            raise ValueError(f"'{path}' already exists, you probably don't want "
                             f"to append any more data to it")
    if args['--common_name']:
        # load mapping
        with open(DATA_PATH / serie / TRANSCRIPT / 'names_dict.json') as file:
            mapping = json.load(file)
    else:
        mapping = None
    protocol_to_rttm(protocol, rttm_out, uem_out, mapping, confidence)

