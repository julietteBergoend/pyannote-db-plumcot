from pathlib import Path
import Plumcot as PC
from Plumcot import Plumcot
import json
import re
import warnings
import pandas as pd

DATA_PATH = Path(PC.__file__).parent / 'data'


def df_to_dict_of_set(dataframe):
    dictionary = {}
    for _, row in dataframe.iterrows():
        dictionary.setdefault(row.actor_uri, set())
        dictionary[row.actor_uri].add(row.character_uri)
    return dictionary


def df_to_dict_of_str(dataframe):
    dictionary = {}
    for _, row in dataframe.iterrows():
        dictionary[row.actor_uri] = row.character_uri
    return dictionary


def diff_to_json(db, write=True):
    per_serie = {}
    fields = list(db.fields.keys())
    for uri in db.series['short_name']:
        serie = {}
        with open(DATA_PATH/uri/'characters.txt.old') as file:
            old = pd.read_csv(file, sep=',', header=None, names=fields)
        old = df_to_dict_of_set(old)
        with open(DATA_PATH/uri/'characters.txt') as file:
            new = pd.read_csv(file, sep=',', header=None, names=fields)
        new = df_to_dict_of_str(new)
        for actor, characters in old.items():
            new_character = new.get(actor)
            if new_character is None:
                warnings.warn(f"We don't have entry for actor '{actor}' (playing {characters}) "
                              f"It will be kept unchanged.")
                continue
            for character in characters:
                if character != new_character:
                    serie[character] = new_character
        per_serie[uri] = serie

    if write:
        for uri, serie in per_serie.items():
            with open(DATA_PATH/uri/'characters.diff.json', 'w') as file:
                json.dump(serie, file, sort_keys=True, indent=4)
    else:
        return per_serie


def fix_names(per_serie):
    for uri, serie in per_serie.items():
        serie_path = DATA_PATH/uri
        data = [
            # 1. transcripts -> name is at the beginning of the line
            (serie_path.glob("transcripts/*.txt"), r'^{}\b', '{}'),
            # 2. aligned -> name is the second token
            (serie_path.glob("forced-alignment/*.aligned"), r"(^\S+\W){}\b", r"\1{}"),
            # 3. RTTM -> simple enough
            (serie_path.glob("forced-alignment/*.rttm"), r'\b{}\b', "{}"),
            (serie_path.glob("annotated_transcripts/*.rttm"), r'\b{}\b', "{}"),
            # 4. merge_{idEpisode}.csv name can be:
            #   a. speaker field -> after "];<some field>;"
            (serie_path.glob("annotated_transcripts/*.csv"), r'(\];[^;]+;){}', r"\1{}"),
            #   b. labelDoccano field -> end of the line
            (serie_path.glob("annotated_transcripts/*.csv"), r';{}$', r";{}"),
            # 5. json files : simple enough
            (serie_path.rglob("*json"), r'\b{}\b', "{}")
        ]
        for files, old_regex, new_regex in data:
            for file_path in files:
                with open(file_path) as file:
                    try:
                        old = file.read()
                    except UnicodeDecodeError as e:
                        warnings.warn(f"Skipping '{file_path} because of a "
                                      f"UnicodeDecodeError:\n{e}'")
                        continue
                for old_name, new_name in serie.items():
                    old = re.sub(old_regex.format(old_name), new_regex.format(new_name), old)
                with open(file_path, 'w') as file:
                    file.write(old)


if __name__ == '__main__':
    db = Plumcot()
    #diff_to_json(db, True)
    fix_names(diff_to_json(db, False))
