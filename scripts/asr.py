# coding: utf-8
"""
Usage:
asr.py run <protocol> <model> <scorer> [--subset=<subset>]
asr.py evaluate <protocol> [--subset=<subset>]

<protocol>        pyannote Protocol, e.g. 'GameOfThrones.SpeakerDiarization.0'
<model>           path to deepspeech model, e.g. /path/to/deepspeech-0.7.3-models.pbmm
<scorer>          path to deepspeech score, e.g. /path/to/deepspeech-0.7.3-models.scorer
--subset=<subset> Serie subset, defaults to 'test'.
"""

import re
import wave
from pathlib import Path

import numpy as np
from deepspeech import Model
from docopt import docopt
from pyannote.database import get_protocol, FileFinder
from spacy.gold import align
from tqdm import tqdm

import Plumcot as PC

DATA_PATH = Path(PC.__file__).parent / 'data'

# same as string.punctuation without "'"
PUNCTUATION = '!"#$%&()*+,-./:;<=>?@[\\]^_`{|}~'


def run(subset, output_path, model):
    for current_file in subset:
        fin = wave.open(str(current_file['audio']), 'rb')
        audio = np.frombuffer(fin.readframes(fin.getnframes()), np.int16)
        fin.close()
        output = model.stt(audio)
        with open(str(output_path / current_file['uri']) + '.txt', 'w') as file:
            file.write(output)


def levenshtein(a, b):
    """Calculates the Levenshtein distance between a and b.
    
    Returns
    -------
    cost: int
        Levenshtein distance
    insertions: int
        Number of insertions + subtitutions
    deletions: int
        Number of deletions + subtitutions
    """
    cost, a2b, b2a, _, _, = align(a, b)
    insertions = len((b2a<0).nonzero()[0])
    deletions = len((a2b<0).nonzero()[0])
    return cost, insertions, deletions


def evaluate(subset, output_path):
    CER, WER, IR, DR = [], [], [], []
    print("uri & CER & WER & IR & DR\\\\")
    for current_file in subset:
        uri = current_file['uri']
        # A. load hypothesis
        with open(str(output_path / uri) + '.txt', 'r') as file:
            hypothesis = file.read()

        # B. load and post-process ground-truth transcription
        transcription = current_file['transcription'].text
        # 1. lower-case
        transcription = transcription.lower()
        # 2. strip all punctuation except for "'"
        transcription = transcription.translate(str.maketrans('', '', PUNCTUATION))
        # 3. remove extra whitespaces
        transcription = re.sub(' +', ' ', transcription)
        
        cer = levenshtein(transcription, hypothesis)[0] / len(transcription)
        cost, insertions, deletions = levenshtein(transcription.split(), hypothesis.split())
        wer = cost / len(transcription.split())
        insertion_rate = insertions / len(hypothesis.split())
        deletion_rate = deletions / len(transcription.split())
        print(f"{uri} & {cer*100:.2f} & {wer*100:.2f} & {insertion_rate*100:.2f} & {deletion_rate*100:.2f}\\\\")
        CER.append(cer)
        WER.append(wer)
        IR.append(insertion_rate)
        DR.append(deletion_rate)
    print('TOTAL', end = " & ")
    for metric in [CER, WER, IR, DR]:
        mean, std = np.mean(metric), np.std(metric)
        print(f'{mean * 100:.2f} $\\pm$ {std * 100:.2f}', end=" & ")


if __name__ == '__main__':
    args = docopt(__doc__)

    preprocessors = {'audio': FileFinder()}
    subset_name = args['--subset'] if args['--subset'] else 'test'
    protocol_name = args['<protocol>']
    protocol = get_protocol(protocol_name, preprocessors=preprocessors)
    serie, _, _ = protocol_name.split('.')
    output_path = DATA_PATH / serie / 'experiments' / 'ASR'
    output_path.mkdir(parents=True, exist_ok=True)

    subset = tqdm(getattr(protocol, subset_name)())
    if args['run']:
        model_path = args['<model>']
        model = Model(model_path)
        model.enableExternalScorer(args['<scorer>'])
        print(
            f"Running {model_path} on {subset_name} subset of {protocol_name} protocol.")
        run(subset, output_path, model)
    if args['evaluate']:
        evaluate(subset, output_path)
