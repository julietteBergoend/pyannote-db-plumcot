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

from pathlib import Path
from docopt import docopt
import re
from tqdm import tqdm

from pyannote.database import get_protocol, FileFinder
import pyannote.database
import Plumcot as PC

import numpy as np
import wave
from deepspeech import Model
from spacy.gold import align

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
    "Calculates the Levenshtein distance between a and b."
    cost, _, _, _, _, = align(a, b)
    return cost


def evaluate(subset, output_path):
    CER, WER = [], []
    print("uri & CER & WER \\\\")
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

        cer = levenshtein(transcription, hypothesis) / len(transcription)
        wer = levenshtein(transcription.split(), hypothesis.split()) / len(
            transcription.split())
        print(f"{uri} & {cer * 100:.2f} & {wer * 100:.2f} \\\\")
        CER.append(cer)
        WER.append(wer)
    print('TOTAL', end=" & ")
    for metric in [CER, WER]:
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
