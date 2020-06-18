#!/usr/bin/env python3
# -*- coding: utf-8 -*-

raise NotImplementedError(
    "this script is a work in progress and shouldn't be executed as is.")

import re
import os
import pyannote.database
from pathlib import Path
import pyannote.database
import Plumcot as PC

DATA_PATH = Path(PC.__file__).parent / "data"

# pattern for '#' which is not unk
# pattern=r'\n.*(?<!unknown)#(?!unk).*'

# pattern for multiple new lines
# pattern=r'\n\n'
serie_uri = "Lost"
SERIE_PATH = DATA_PATH / serie_uri
wav_path = Path(f'/vol/work3/lefevre/dvd_extracted/{serie_uri}')
transcript_path = Path(SERIE_PATH, 'transcripts')
with open(Path(SERIE_PATH, "episodes.txt"), 'r') as file:
    episodes = file.read().split("\n")
    episodes = set([episode.split(',')[0] for episode in episodes])
correct = False


def temp_txt_gen(transcript_path, episodes):
    for episode in sorted(episodes):
        print(f"-------------------\n{episode}\n")
        if episode == "":
            continue
        file = Path(transcript_path, episode)
        temp = str(file) + ".temp"
        txt = str(file) + ".txt"
        with open(temp, 'r') as file:
            temp = file.read().split("\n")
        with open(txt, 'r') as file:
            txt = file.read().split("\n")
        for temp_line, txt_line in zip(temp, txt):
            if temp_line != "":
                yield (temp_line, txt_line)


def get_season_number(uri):
    return int(re.findall(r'\d+', uri.split(".")[1])[0])


def increment_episode_number(uri, increment):
    episode_number = int(uri.split(".")[-1][-2:]) + increment
    new_uri = f'{".".join(uri.split(".")[:-1])}.Episode{episode_number:02d}'
    return new_uri


def Increment(transcript_path):
    old_season_number = None
    todo = {}
    for transcript in sorted(os.listdir(transcript_path)):
        uri, extension = os.path.splitext(transcript)
        if extension != ".txt" and extension != ".temp":
            continue
        season_number = get_season_number(uri)
        if season_number != old_season_number:
            old_season_number = season_number
            print("\n", season_number)
            increment = 0
        if uri[-1] == "b":
            new_uri = uri[:-1]
            increment += 1
            new_uri = increment_episode_number(new_uri, increment)
        else:
            new_uri = increment_episode_number(uri, increment)
        if uri != new_uri:
            print(f"{uri} -> {new_uri}")
            todo[os.path.join(transcript_path, transcript)] = os.path.join(
                transcript_path, f"{new_uri}{extension}")

    for key, file_dir in sorted(todo.items(), key=lambda x: x[0], reverse=True):
        print(key, file_dir)
        if correct:
            os.rename(
                key,
                file_dir
            )
    return todo


def Decrement(transcript_path, with_ext=".txt", with_enc=None):
    old_season_number = None
    for transcript in sorted(os.listdir(transcript_path)):
        uri, extension = os.path.splitext(transcript)
        if extension != with_ext:
            continue
        if extension == ".wav" or extension == ".srt":
            uri, encoding = os.path.splitext(uri)
        else:
            encoding = ""
        if with_enc:
            if encoding != with_enc:
                continue
        season_number = get_season_number(uri)
        if season_number != old_season_number:
            old_season_number = season_number
            print("\n", season_number)
            decrement = 0
        if uri.split(".")[-1].isdigit():

            new_uri = ".".join(uri.split(".")[:-1])
            new_uri = increment_episode_number(new_uri, decrement)
            # print(uri)
            decrement -= 1
        else:
            new_uri = increment_episode_number(uri, decrement)
        if uri != new_uri:
            print(f"{uri} -> {new_uri}")
            old_path = os.path.join(transcript_path, transcript)
            new_path = os.path.join(transcript_path, f"{new_uri}{encoding}{extension}")
            print(f"{old_path} -> {new_uri}")
            if correct:
                os.rename(
                    old_path,
                    new_path
                )


Increment(transcript_path)
