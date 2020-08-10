from pathlib import Path
import Plumcot as PC
import json
import re
import warnings

DATA_PATH = Path(PC.__file__).parent / 'data'


def diff_to_json(write=True):
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
    if write:
        for uri, serie in per_serie.items():
            with open(DATA_PATH/uri/'characters.diff.json', 'w') as file:
                json.dump(serie, file, sort_keys=True, indent=4)
    else:
        return per_serie


def fix_names(per_serie):
    for uri, serie in per_serie.items():
        if uri != 'Friends':
            continue
        serie_path = DATA_PATH/uri
        for data in serie_path.iterdir():
            if not data.is_dir():
                continue
            for file_path in data.iterdir():
                if not file_path.is_file():
                    continue
                print(file_path)
                with open(file_path) as file:
                    try:
                        old = file.read()
                    except UnicodeDecodeError as e:
                        warnings.warn(f"Skipping '{file_path} because of a "
                                      f"UnicodeDecodeError:\n{e}'")
                for old_name, new_name in serie.items():
                    old = re.sub(rf'\b{old_name}\b', new_name, old)
                with open(file_path, 'w') as file:
                    file.write(old)


fix_names(diff_to_json(False))
