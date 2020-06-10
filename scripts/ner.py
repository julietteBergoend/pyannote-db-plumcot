# coding: utf-8
"""
Usage:
ner.py [--uri=<uri>]

--uri=<uri> Only process this serie, defaults to process all
"""

from pathlib import Path
from docopt import docopt
import sys

from pyannote.database import get_protocol
import pyannote.database
import Plumcot as PC

from spacy.gold import align
try:
    import en_core_web_lg
except ImportError:
    msg = 'ImportError: Seems like you did not install spaCy model "en_core_web_lg".\n' \
          'Try running "python -m spacy download en_core_web_lg"'
    sys.exit(msg)

args = docopt(__doc__)
uri = args['--uri']
DATA_PATH = Path(PC.__file__).parent / 'data'
PERSON = 'PERSON'
model = en_core_web_lg.load()
with open(DATA_PATH / "series.txt") as file:
    series = file.readlines()


def return_metrics(tp, tn, fp, fn):
    accuracy = (tp + tn) / (tp + tn + fp + fn)
    # without condition positives the recall should be 0
    recall = tp / (tp + fn) if (tp + fn) != 0 else 0.0
    # idem
    specificity = tn / (tn + fp) if (tn + fp) != 0 else 0.0
    # without predicted positives the precision should be 0
    precision = tp / (tp + fp) if tp + fp != 0 else 0.0
    # idem
    npv = tn / (tn + fn) if tn + fn != 0 else 0.0
    f_score = (2 * precision * recall) / (precision + recall)
    return accuracy, recall, specificity, precision, npv, f_score


for serie_ in series:
    serie = serie_[:serie_.find(',')]
    if serie != uri and uri is not None:
        continue
    protocol_name = f'{serie}.SpeakerDiarization.EL'
    # Entities annotation might not be available for all series
    try:
        protocol = get_protocol(protocol_name)
    except Exception:
        continue

    experiment = DATA_PATH / serie / "experiments" / "NER"
    experiment.mkdir(parents=True, exist_ok=True)

    TP, TN, FP, FN = 0, 0, 0, 0
    with open(experiment / "confusion.csv", "a") as file:
        file.write("TP,TN,FP,FN\n")
    print(f"Processing {protocol_name}'s test set.")
    short = ''.join([letter for letter in serie if
                     letter.isupper() or not letter.isalpha()])
    print('uri & F-score & Precision & Recall \\\\')
    for current_file in protocol.test():
        entity = current_file['entity']
        file_uri = current_file['uri']
        # 1. run model on text
        output = model(entity.text)

        # 2. align output and reference tokenization
        output_tokens = [token.text for token in output]
        input_tokens = [token.text for token in entity]
        _, one2one, _, _, _ = align(output_tokens, input_tokens)

        # 3. evaluate perfectly mapped tokens
        tp, tn, fp, fn = 0, 0, 0, 0
        for i, j in enumerate(one2one):
            hyp, ref = output[i].ent_type_, entity[j].ent_type_
            # we only evaluate proper names of person named-entities
            if entity[j].pos_ != 'PROPN' or (ref != PERSON and hyp != PERSON):
                continue

            if hyp == ref:
                if ref != '':
                    tp += 1
                else:
                    tn += 1
            else:
                if ref != '':
                    fn += 1
                else:
                    fp += 1
        # 4. save confusion matrix
        with open(experiment / "confusion.csv", "a") as file:
            file.write(','.join(map(str, [tp, tn, fp, fn])) + '\n')
        # 5. compute F-score, Precision and Recall
        _, recall, _, precision, _, f_score = return_metrics(tp, tn, fp, fn)
        print(f'{file_uri} & {100 * f_score:.2f} & {100 * precision:.2f} & {100 * recall:.2f} \\\\')
        TP += TP
        TN += tn
        FP += fp
        FN += fn
    with open(experiment / "confusion.csv", "a") as file:
        file.write(','.join(map(str, [TP, TN, FP, FN])) + '\n')
    _, recall, _, precision, _, f_score = return_metrics(TP, TN, FP, FN)
    print(f'{short} & {100 * f_score:.2f} & {100 * precision:.2f} & {100 * recall:.2f} \\\\')
