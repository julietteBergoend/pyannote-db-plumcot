# coding: utf-8
"""
Usage:
asr.py run <protocol> [--subset=<subset>]
asr.py evaluate <protocol> [--subset=<subset>]

<protocol>        pyannote Protocol, e.g. 'GameOfThrones.SpeakerDiarization.0'
--subset=<subset> Serie subset [default: 'test'].
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

PLUMCOT_PATH = Path(PC.__file__).parent
DATA_PATH = PLUMCOT_PATH / 'data'
RESOURCE_PATH = PLUMCOT_PATH / 'resources'
model_path = RESOURCE_PATH / 'deepspeech-0.7.3-models.pbmm'
scorer_path = RESOURCE_PATH / 'deepspeech-0.7.3-models.scorer'

# same as string.punctuation without "'"
PUNCTUATION = '!"#$%&()*+,-./:;<=>?@[\\]^_`{|}~'

def run(subset, output_path):
    model = Model(model_path)
    model.enableExternalScorer(scorer_path)
    for current_file in subset:
        fin = wave.open(current_file['audio'], 'rb')
        audio = np.frombuffer(fin.readframes(fin.getnframes()), np.int16)
        fin.close()
        output = model.stt(audio)
        with open(output_path/current_file['uri']+'.txt', 'w') as file:
            file.write(output)

def levenshtein(a, b):
    "Calculates the Levenshtein distance between a and b."
    n, m = len(a), len(b)
    if n > m:
        # Make sure n <= m, to use O(min(n,m)) space
        a, b = b, a
        n, m = m, n

    current = list(range(n+1))
    for i in range(1, m+1):
        previous, current = current, [i]+[0]*n
        for j in range(1, n+1):
            add, delete = previous[j]+1, current[j-1]+1
            change = previous[j-1]
            if a[j-1] != b[i-1]:
                change = change + 1
            current[j] = min(add, delete, change)

    return current[n]

def evaluate(subset, output_path):
    CER, WER = [], []
    print("uri & CER & WER \\\\")
    for current_file in subset:
        uri = current_file['uri']
        # A. load hypothesis
        with open(output_path / uri + '.txt', 'r') as file:
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
        wer = levenshtein(transcription.split(), hypothesis.split()) / len(transcription.split())
        print(f"{uri} & {cer:.2f} & {wer:.2f} \\\\")
        CER.append(cer)
        WER.append(wer)
    print('TOTAL', end = " & ")
    for metric in [CER, WER]:
        mean, std = np.mean(metric), np.std(metric)
        print(f'{mean:.2f} $\\pm$ {std:.2f}', end=" & ")


if __name__ == '__main__':
    args = docopt(__doc__)

    preprocessors = {'audio': FileFinder()}
    subset_name = args['--subset']
    verbosity = args['-v']
    protocol_name = args['<protocol>']
    protocol = get_protocol(protocol_name, preprocessors=preprocessors)
    serie, _, _ = protocol_name.split('.')
    output_path = DATA_PATH / serie / 'experiments' / 'ASR'
    output_path.mkdir(parents=True, exist_ok=True)

    subset = tqdm(getattr(protocol, subset_name))
    if args['run']:
        print(f"Running {model_path} on {subset} subset of {protocol_name} protocol.")
        run(subset, output_path)
    if args['evaluate']:
        evaluate(subset, output_path)




