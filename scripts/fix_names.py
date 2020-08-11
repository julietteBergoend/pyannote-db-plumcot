from pathlib import Path
import Plumcot as PC
import json

DATA_PATH = Path(PC.__file__).parent / 'data'


def diff_to_json():
    with open(DATA_PATH/'characters.diff') as file:
        diff = file.read().split('\n')

    per_serie = {}

    a, b = [], []
    for line in diff:
        if line.startswith('---'):
            a, b = [], []
            # starting diff from a new serie
            serie = line[4:].split('/')[3]
            per_serie[serie] = {}
        elif line.startswith('+++'):
            # no to get confused with '+'
            pass
        elif line.startswith('-'):
            a.append(line[1:])
        elif line.startswith('+'):
            b.append(line[1:])
        elif line.startswith('@@'):
            # map a and b
            if len(a) == len(b):
                for old, new in zip(a, b):
                    old, _, _, _, _ = old.split(',')
                    new, _, _, _, _ = new.split(',')
                    if old != new:
                        per_serie[serie][old] = new
            a, b = [], []
        else:
            continue

    for name, serie in per_serie.items():
        with open(DATA_PATH/name/'characters.diff.json', 'w') as file:
            json.dump(serie, file, sort_keys=True, indent=4)

