#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os
import pyannote.database
from pathlib import Path

#pattern for '#' which is not unk
#pattern=r'\n.*(?<!unknown)#(?!unk).*'

#pattern for multiple new lines
#pattern=r'\n\n'
SERIE_PATH='Plumcot/data/TheOffice/'
transcript_path=os.path.join(SERIE_PATH,'transcripts')
with open(os.path.join(SERIE_PATH,"episodes.txt"),'r') as file:
        episodes=file.read().split("\n")
        episodes=set([episode.split(',')[0] for episode in episodes])
correct=False

def temp_txt_gen(transcript_path,episodes):
    for episode in sorted(episodes):
        print(f"-------------------\n{episode}\n")
        if episode=="":
            continue
        file=Path(transcript_path,episode)
        temp=str(file)+".temp"
        txt=str(file)+".txt"
        with open(temp,'r') as file:
            temp=file.read().split("\n")
        with open(txt,'r') as file:
            txt=file.read().split("\n")
        for temp_line, txt_line in zip(temp,txt):
            if temp_line!="":
                yield (temp_line, txt_line)

def get_season_number(uri):
    return int(re.findall(r'\d+', uri.split(".")[1])[0])

def increment_episode_number(uri,increment):
    episode_number=int(uri.split(".")[-1][-2:])+increment
    new_uri=f'{".".join(uri.split(".")[:-1])}.Episode{episode_number:02d}'
    return new_uri

def Increment(transcript_path):
    old_season_number=None
    todo={}
    for transcript in sorted(os.listdir(transcript_path)):
        uri,extension=os.path.splitext(transcript)
        if extension!=".txt" and extension != ".temp":
            continue
        season_number=get_season_number(uri)
        if season_number!=old_season_number:
            old_season_number=season_number
            print("\n",season_number)
            increment=0
        if uri[-1]=="b":
            new_uri=uri[:-1]
            increment+=1
            new_uri=increment_episode_number(new_uri,increment)
        else:
            new_uri=increment_episode_number(uri,increment)
        if uri != new_uri:
            print(f"{uri} -> {new_uri}")
            todo[os.path.join(transcript_path,transcript)]=os.path.join(transcript_path,f"{new_uri}{extension}")

    for key, file_dir in sorted(todo.items(), key=lambda x:x[0], reverse=True):
        print(key,file_dir)
        if correct:
            os.rename(
                key,
                file_dir
            )
    return todo

Increment(transcript_path)
def Decrement(transcript_path):
    old_season_number=None
    for transcript in sorted(os.listdir(transcript_path)):
        uri,extension=os.path.splitext(transcript)
        season_number=get_season_number(uri)
        if season_number!=old_season_number:
            old_season_number=season_number
            print("\n",season_number)
            decrement=0
        if uri.split(".")[-1].isdigit():
            new_uri=".".join(uri.split(".")[:-1])
            new_uri=increment_episode_number(new_uri,decrement)
            #print(uri)
            decrement-=1
        else:
            new_uri=increment_episode_number(uri,decrement)
        if uri != new_uri:
            print(f"{uri} -> {new_uri}")
            if correct:
                os.rename(
                    os.path.join(transcript_path,transcript),
                    os.path.join(transcript_path,f"{new_uri}{extension}")
                )
    # if uri not in episodes:
    #     print(uri)

    # with open(transcript_path+"/"+transcript,'r') as file:
    #     raw=file.read()
    #
    # if correct:
    #     corrected=re.sub(pattern, "", raw)
    #     with open(transcript_path+"/"+transcript,'w') as file:
    #         file.write(corrected)
    # else:
    #     for line in raw.split("\n"):
    #         if line.isspace():
    #             print(transcript)
        # matches=re.findall(pattern,raw)
        # if len(matches)!=0:
        #     print(transcript)
        #     print(matches)
