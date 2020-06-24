# coding: utf-8
"""
Usage:
id_to_names.py <protocol>

Arguments:
<protocol>        pyannote Protocol, e.g. 'GameOfThrones.SpeakerDiarization.0'
"""

import json
from pathlib import Path
from docopt import docopt
from collections import Counter
import numpy as np
import re
from warnings import warn
from termcolor import colored

from pyannote.database import get_protocol
from Plumcot.loader import NA
import Plumcot as PC
from Plumcot import Plumcot

DATA_PATH = Path(PC.__file__).parent / 'data'


def proper_entity(token):
    return token.ent_kb_id_ != '' and token.pos_ == 'PROPN' and token.ent_kb_id_ not in NA


def id_to_name(transcription, mapping={}):
    """Takes transcription annotated with entities and updates/outputs a dict mapping
    entity identifier and counted proper names
    """
    for i, token in enumerate(transcription):
        # keep only proper names
        if proper_entity(token):
            mapping.setdefault(token.ent_kb_id_, Counter())
            if token.ent_kb_id_ != transcription[i - 1].ent_kb_id_:
                mapping[token.ent_kb_id_][token.text] += 1
            elif proper_entity(transcription[i - 1]):
                mapping[token.ent_kb_id_][transcription[i - 1].text] -= 1
                mapping[token.ent_kb_id_][
                    transcription[i - 1].text_with_ws + token.text] += 1
    return mapping


def get_test_mapping(protocol):
    """Get initial mapping from entities annotation
    beware this only works with protocol where entities were annotated
    """

    mapping = {}
    for current_file in protocol.test():
        transcription = current_file['entity']
        # update counter with transcription
        mapping = id_to_name(transcription, mapping)

    # keep only the most common name among all mentions
    manual = {}
    for identifier, counts in mapping.items():
        name, count = counts.most_common(1)[0]
        mapping[identifier] = name
        manual[identifier] = True
    return mapping, manual


def populate_mapping(protocol, mapping={}):
    """populate mapping with unknown characters from training and dev sets
    if they're in the last quartile of speech duration
    """

    stats = Counter(protocol.stats('train')['labels']) + \
            Counter(protocol.stats('development')['labels'])
    third_quartile = np.quantile(list(stats.values()), 0.75)

    durations = {}
    for label, duration in stats.items():
        if duration > third_quartile and label not in mapping:
            mapping[label] = ''
            durations[label] = duration
            manual[label] = True
    return mapping, durations


def find_candidates(db, protocol, mapping={}, manual={}):
    """Find candidates name for un-matched identifiers based on their first name"""

    # gather first names
    first_names = set()
    for identifier, name in mapping.items():
        if name:
            continue
        for first_name in identifier.split('_'):
            if first_name in db.SPECIAL_NOUNS:
                continue
            first_name = first_name.title()
            first_names.add(first_name)
            mapping[identifier] = first_name
            manual[identifier] = False
            break

    # find candidates name
    candidates = Counter()
    for subset in ['development', 'train']:
        for current_file in getattr(protocol, subset)():
            transcription = current_file['transcription'].text
            for first_name in first_names:
                # find with regex then update candidates counter
                candidates += Counter(re.findall(fr'\b{first_name}\b', transcription))

    return candidates, manual


def annotate_mapping(mapping, candidates, durations={}, manual={}):
    """Fill in the blanks until user is done"""
    while True:
        print("Candidates [{candidate} ({count})]:")
        for candidate, count in sorted(candidates.items()):
            print(f'{candidate} ({count})', end=', ')
        print('\n\nMapping:')
        for id, name in sorted(mapping.items()):
            duration = durations.get(id, 0.)
            if name:
                color = 'green' if manual.get(id) else 'red'
                print(colored(f'{id} ({duration:.2f}): {name} ({candidates.get(name, 0)})', color))
            else:
                print(f'{id} ({duration:.2f}): ?')
        id = None
        while id not in mapping and id != '':
            id = input('\nEnter the id that you want to annotate (blank to stop):\n')
        if id == '':
            break
        name = input(f'Enter the name of {id}:\n')
        mapping[id] = name
        manual[id] = True
        if name not in candidates:
            warn(f'{name} is not in the candidate list.')

    return mapping


if __name__ == '__main__':
    # parse args, load protocol and make appropriate file structure
    args = docopt(__doc__)
    protocol_name = args['<protocol>']
    protocol = get_protocol(protocol_name)
    serie, _, _ = protocol_name.split('.')
    output_path = DATA_PATH / serie / 'annotated_transcripts' / 'names_dict.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    db = Plumcot()

    # get initial mapping from entities annotation
    # beware this only works with protocol where entities were annotated
    mapping, manual = get_test_mapping(protocol)

    # populate mapping with unknown characters from training and dev sets
    # if they're in the last quartile of speech duration
    mapping, durations = populate_mapping(protocol, mapping)

    # Find candidates name for un-matched identifiers based on their first name
    candidates, manual = find_candidates(db, protocol, mapping, manual)

    mapping = annotate_mapping(mapping, candidates, durations, manual)

    with open(output_path, 'w') as file:
        json.dump(mapping, file, sort_keys=True, indent=4)
