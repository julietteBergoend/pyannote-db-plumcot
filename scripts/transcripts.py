#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os
import pyannote.database


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
old_season_number=None
for transcript in sorted(os.listdir(transcript_path)):
    uri,extension=os.path.splitext(transcript)
    season_number=int(re.findall(r'\d+', uri.split(".")[1])[0])
    if season_number!=old_season_number:
        old_season_number=season_number
        print("\n",season_number)
        decrement=0
    if uri.split(".")[-1].isdigit():

        new_uri=".".join(uri.split(".")[:-1])
        episode_number=int(new_uri.split(".")[-1][-2:])-decrement
        new_uri=f'{".".join(new_uri.split(".")[:-1])}.Episode{episode_number:02d}'
        #print(uri)
        decrement+=1
    else:
        episode_number=int(uri.split(".")[-1][-2:])-decrement
        new_uri=f'{".".join(uri.split(".")[:-1])}.Episode{episode_number:02d}'
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
