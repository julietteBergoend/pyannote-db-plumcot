#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Usage:
normalizeTranscriptsNames.py <id_series> [-s SEASON] [-e EPISODE] [--quiet]
normalizeTranscriptsNames.py check_names <id_series> [-s SEASON] [-e EPISODE]
normalizeTranscriptsNames.py check_files <id_series> [-s SEASON] [-e EPISODE] [--extension=<extension>]
normalizeTranscriptsNames.py -h|--help

Arguments:
    id_series    Id of the series

Options:
    -s SEASON               Season number to iterate on (all seasons if not specified)
    -e EPISODE              Episode number (all episodes of the season if not specified)
    --quiet                 Display only the names that have changed.
    --extension=<extension> Transcript file extension. Defaults to '.txt'
"""

import json
import os.path
import readline
import warnings
from pathlib import Path

from docopt import docopt
from termcolor import colored

import Plumcot as PC
from Plumcot import Plumcot

path_p = "/vol/work1/bergoend/pyannote-db-plumcot/Plumcot"

def input_with_prefill(prompt, text):
    def hook():
        readline.insert_text(text)
        readline.redisplay()

    readline.set_pre_input_hook(hook)
    result = input(prompt)
    readline.set_pre_input_hook()
    return result


def automatic_alignment(id_series, id_ep, refsT, hypsT):
    """Aligns IMDB character's names with transcripts characters names.

    Parameters
    ----------
    id_series : `str`
        Id of the series.
    id_ep : `str`
        Id of the episode.
    refsT : `dict`
        Dictionnary of character's names from transcripts as key and number of
        speech turns as value.
    hypsT : `list`
        List of character's names from IMDB.

    Returns
    -------
    names_dict : `dict`
        Dictionnary with character's names as key and normalized name as value.
    """

    names_dict = {}
    save_dict = {}

    hyps = hypsT[:]
    refs = refsT.copy()

    # Loading user previous matching names
    savePath = f'{path_p}/data/{id_series}/transcripts/names_dict.json'
    if os.path.isfile(savePath):
        with open(savePath, 'r') as f:
            save_dict = json.load(f)

        # Process data to take user matching names in account
        for trans_name in refs.copy():
            if trans_name in save_dict:
                if ('@' in save_dict[trans_name] or
                        save_dict[trans_name] in hyps):

                    names_dict[trans_name] = save_dict[trans_name]
                    refs.pop(trans_name)
                    if save_dict[trans_name] in hyps:
                        hyps.remove(save_dict[trans_name])

    # naive sub-string match: TODO improve
    for trans_char in refs:
        for suggestion in hyps:
            if trans_char.lower() in suggestion:
                names_dict[trans_char] = suggestion
                break
        if trans_char not in names_dict:
            # none of imdb character matches -> unknown character
            names_dict[trans_char] = unknown_char(trans_char, id_ep)

    return names_dict


def check_files(id_series, season_number, episode_number, extension=".txt"):
    """Check the difference in file names between IMDb and transcripts

    Parameters
    ----------
    id_series : `str`
        Id of the series.
    season_number : `str`
        The desired season number. If None, all seasons are processed.
    episode_number : `str`
        The desired episode_number. If None, all episodes are processed.
    extension : `str`
        Transcript file extension. Defaults to '.txt'
    """

    # Plumcot database object
    db = Plumcot()
    # Retrieve IMDB normalized character names
    imdb_chars_series = db.get_characters(id_series, season_number,
                                          episode_number)

    # Retrieve transcripts normalized character names
    trans_chars_series = db.get_transcript_characters(id_series, season_number,
                                                      episode_number, extension=extension)

    for episode_uri in imdb_chars_series:
        imdb = imdb_chars_series.get(episode_uri)
        if imdb is None:
            warnings.warn(f"{episode_uri} is not IMDB")
            continue
        transcripts = trans_chars_series.get(episode_uri)
        if transcripts is None:
            warnings.warn(f"{episode_uri} is not transcripts")
            continue
    print("Done. (no warnings means everything went okay)")


def check_normalized_names(id_series, season_number, episode_number):
    """Check normalized names. Print the difference between IMDb and transcripts

    Parameters
    ----------
    id_series : `str`
        Id of the series.
    season_number : `str`
        The desired season number. If None, all seasons are processed.
    episode_number : `str`
        The desired episode_number. If None, all episodes are processed.
    """

    # Plumcot database object
    db = Plumcot()
    # Retrieve IMDB normalized character names
    imdb_chars_series = db.get_characters(id_series, season_number,
                                          episode_number)

    # Retrieve transcripts normalized character names
    trans_chars_series = db.get_transcript_characters(id_series, season_number,
                                                      episode_number, extension=".txt")

    for episode_uri in imdb_chars_series:
        print("\n" + episode_uri)
        imdb = imdb_chars_series.get(episode_uri)
        if imdb is None:
            warnings.warn(f"{episode_uri} is not IMDB, jumping to next episode")
            continue
        else:
            imdb = set(imdb)
        transcripts = trans_chars_series.get(episode_uri)
        if transcripts is None:
            warnings.warn(f"{episode_uri} is not transcripts, jumping to next episode")
            continue
        else:
            transcripts = set([char for char in transcripts if
                               "#unknown#" not in char and "@" not in char])
        print("In imdb but not in transcripts:")
        print(imdb - transcripts)
        print("In transcripts but not imdb (not counting #unknown# and alice@bob):")
        print(transcripts - imdb)


def normalize_names(id_series, season_number, episode_number, verbose=True):
    """Manual normalization.

    Parameters
    ----------
    id_series : `str`
        Id of the series.
    season_number : `str`
        The desired season number. If None, all seasons are processed.
    episode_number : `str`
        The desired episode_number. If None, all episodes are processed.
    verbose : bool
        Display names even if they did not change (Default).

    Returns
    -------
    names_dict : `dict`
        Dictionnary with character's names as key and normalized name as value.
    """

    # Plumcot database object
    db = Plumcot()
    # Retrieve IMDB normalized character names
    imdb_chars_series = db.get_characters(id_series, season_number,
                                          episode_number)
    #print(imdb_chars_series)

    # Retrieve transcripts normalized character names
    trans_chars_series = db.get_transcript_characters(id_series, season_number,
                                                      episode_number, extension=".txt")
    #print(trans_chars_series)

    # Loading user previous matching names
    savePath = f'{path_p}/data/{id_series}/transcripts/names_dict.json'
    
    if os.path.isfile(savePath):
        with open(savePath, 'r') as f:
            old_matches = json.load(f)
    else:
        old_matches = {}
    # Iterate over episode IMDB character names
    for id_ep, imdb_chars in imdb_chars_series.items():
        if id_ep not in trans_chars_series:
            warnings.warn(f"{id_ep} is not transcripts, jumping to next episodeeee")
            continue
        trans_chars = trans_chars_series[id_ep]
        total_appearances = {}
        for ep_appearances in trans_chars_series.values():
            for character, appearence in ep_appearances.items():
                total_appearances.setdefault(character, 0)
                total_appearances[character] += appearence
        link = Path(PC.__file__).parent / 'data' / f'{id_series}' \
               / 'transcripts' / f'{id_ep}.txt'
        # If episode has already been processed
        if os.path.isfile(link):
            exists = f"{id_ep} already processed. y to processe, [n] to skip: "
            co = input(exists)
            if co != 'y':
                continue

        # Get automatic alignment as a dictionnary
        dic_names = automatic_alignment(id_series, id_ep, trans_chars,
                                        imdb_chars)
        save = True
        names_matched = {}
        # User input loop
        while True:
            print(f"----------------------------\n{id_ep}. Here is the list "
                  "of normalized names from IMDB: ")
            print(", ".join(sorted(imdb_chars[:])), '\n')

            print("Automatic alignment:")
            for name, norm_name in dic_names.items():
                # Get number of speech turns of the character for this episode
                appearence = trans_chars[name]
                total_appearance = total_appearances[name]
                previously_matched = old_matches.get(name)
                if previously_matched:
                    previously_matched = False if "#unknown" in previously_matched or "@" in previously_matched else previously_matched
                    names_matched[name] = previously_matched
                if (previously_matched or name == norm_name or names_matched.get(name)):
                    color = 'green'
                else:
                    color = 'red'
                if (previously_matched or name == norm_name) and not verbose:
                    pass
                else:
                    print(colored(
                        f"{name} ({appearence}, {total_appearance})  ->  {norm_name}",
                        color))
            request = input("\nType the name of the character which you want "
                            "to change normalized name (end to save, stop "
                            "to skip, unk to unknownize every character that didn't match): ")
            # Stop and save
            if request == "end" or not request:
                break
            # Stop without saving
            if request == "stop" or request == "skip":
                save = False
                break
            # all un-assigned -> unknown
            if request == "unk":
                for name in dic_names:
                    if not names_matched.get(name):
                        new_name = unknown_char(name, id_ep)
                        dic_names[name] = new_name
            # Wrong name
            if request not in dic_names:
                warnings.warn("This name doesn't match with any characters.\n")
            else:
                prefill = ""
                prompt = ("\nType the new character's name "
                          "(unk for unknown character): ")
                new_name = input_with_prefill(prompt, prefill)
                # Unknown character
                if new_name == "unk" or not new_name:
                    new_name = unknown_char(request, id_ep)
                dic_names[request] = new_name
                names_matched[request] = True

        # Save changes and create .txt file
        if save:
            save_matching(id_series, dic_names, db)
            db.save_normalized_names(id_series, id_ep, dic_names)


def unknown_char(char_name, id_ep):
    """Transforms character name into unknown version."""
    if "#unknown#" in char_name:  # trick when re-processing already processed files
        return char_name
    return f"{char_name}#unknown#{id_ep}"


def save_matching(id_series, dic_names, db):
    """Saves user matching names

    Parameters
    ----------
    id_series : `str`
        Id of the series.
    dic_names : `dict`
        Dictionnary with matching names (transcript -> normalized).
    """

    save_dict = {}
    savePath = Path(PC.__file__).parent / 'data' / f'{id_series}' \
               / 'transcripts' / 'names_dict.json'
    if os.path.isfile(savePath):
        with open(savePath, 'r') as f:
            save_dict = json.load(f)

    for name_trans, name_norm in dic_names.items():
        if "#unknown" not in name_norm and name_trans.lower() not in db.SPECIAL_NOUNS:
            save_dict[name_trans] = name_norm

    with open(savePath, 'w') as f:
        json.dump(save_dict, f, indent=4)


def main(args):
    id_series = args["<id_series>"]
    season_number = args['-s']
    if season_number:
        season_number = f"{int(season_number):02d}"
    episode_number = args['-e']
    if episode_number:
        episode_number = f"{int(episode_number):02d}"
    if args["check_names"]:
        check_normalized_names(id_series, season_number, episode_number)
    elif args["check_files"]:
        extension = args["--extension"] if args["--extension"] else ".txt"
        check_files(id_series, season_number, episode_number, extension)
    else:
        verbose = not args["--quiet"]
        normalize_names(id_series, season_number, episode_number, verbose)


if __name__ == '__main__':
    args = docopt(__doc__)
    main(args)
