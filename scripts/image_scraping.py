#!/usr/bin/env python
# coding: utf-8

"""
Get images from IMDB character's page given a list of urls and character's names
    (following the format of `characters.txt` described in CONTRIBUTING.md)
"""
# Dependencies
## core
import numpy as np
import os
import json
import warnings
import json

## web
import requests
from bs4 import BeautifulSoup
import re

MAX_FILE_NAME_LENGTH=255
PHOTOS_CLASS='mediastrip'
def get_url_from_character_page(url_IDMB,THUMBNAIL_CLASS="titlecharacters-image-grid__thumbnail-link"):
    """
    Gets url of image viewer of a serie pictures on IMDB (e.g. https://www.imdb.com/title/tt0108778/mediaviewer/rm3406852864)
    Given the url of a character of that serie (e.g. 'https://www.imdb.com/title/tt0108778/characters/nm0000098')

    Parameters:
    -----------
    url_IDMB: url of a character of the serie we're interested in.
    THUMBNAIL_CLASS: IMDB html class which containes the link to the series images url.

    Returns:
    --------
    media_viewer_url: url of image viewer of a serie pictures on IMDB
    """
    page_IMDB = requests.get(url_IDMB).text
    soup = BeautifulSoup(page_IMDB, 'lxml')
    media_viewer_url=soup.findAll("a", {"class":THUMBNAIL_CLASS})[0]["href"]
    return media_viewer_url

def get_url_from_serie_page(url_IDMB,PHOTOS_CLASS='mediastrip'):
    """
    Gets url of image viewer of a serie pictures on IMDB (e.g. https://www.imdb.com/title/tt0108778/mediaviewer/rm3406852864)
    Given the url of that serie (e.g. 'https://www.imdb.com/title/tt0108778/')

    Parameters:
    -----------
    url_IDMB: url of a character of the serie we're interested in.
    PHOTOS_CLASS: IMDB html class which containes the link to the series images url.

    Returns:
    --------
    media_viewer_url: url of image viewer of a serie pictures on IMDB
    """
    page_IMDB = requests.get(url_IDMB).text
    soup = BeautifulSoup(page_IMDB, 'lxml')
    media_viewer_url=soup.findAll("div", {"class":PHOTOS_CLASS})[0].a["href"]
    return media_viewer_url

def get_image_jsons_from_url(media_viewer_url,old_image_jsons=None,IMDB_URL="https://www.imdb.com"):
    """
    Parses a json object in a dict containing a list of image urls of a IMDB serie

    Parameters:
    -----------
    media_viewer_url: url of image viewer of a serie pictures on IMDB
    IMDB_URL: base of the IMDB url, i.e. domain name etc.
        Defaults to "https://www.imdb.com"

    Returns:
    --------
    json.loads(str_script): dict parsed from a json object containing a list of image urls of a IMDB serie
    """
    image_page = requests.get(IMDB_URL+media_viewer_url).text
    soup = BeautifulSoup(image_page, 'lxml')
    tag_script=soup.find_all('script')[1]
    str_script=tag_script.get_text(strip=True)
    str_script=str_script.replace("'mediaviewer'",'"mediaviewer"')#replace simple with double quotes
    json_begins_at=str_script.find("{")
    str_script=str_script[json_begins_at:-1]#the last character is ";" for some reason so we discard it
    image_jsons=json.loads(str_script)['mediaviewer']['galleries']
    #discard anything before the serie_imdb_id
    image_jsons=next(iter(image_jsons.values()))
    if old_image_jsons is None:
        return image_jsons
    else:#merge the two objects
        for key,value in old_image_jsons.items():
            if isinstance(value,int) or isinstance(value,list):
                old_image_jsons[key]+=image_jsons[key]
            elif isinstance(value,str):
                old_image_jsons[key]= [value,image_jsons[key]]
            elif isinstance(value,dict):
                old_image_jsons[key].update(image_jsons[key])
        return old_image_jsons

def write_image(request,dir_path,path):
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)
    with open(path,'wb') as file:
        file.write(request.content)

def read_characters(CHARACTERS_PATH,N_COL,SEPARATOR=","):
    with open(CHARACTERS_PATH,'r') as file:
        raw=file.read()
    print("\n")
    for i,line in enumerate(raw.split("\n")):
        len_line=len(line.split(SEPARATOR))
        if len_line > N_COL:
            print("\nthis line has too many columns")
            print(i,len_line,line.split(SEPARATOR))
        elif len_line < N_COL:
            print("\nthis line does not have enough columns")
            print(i,len_line,line.split(SEPARATOR))
    characters=[line.split(SEPARATOR) for i,line in enumerate(raw.split("\n")) if line !='']
    characters=np.array(characters,dtype=str)
    return characters

def query_image_from_json(image_jsons,IMAGE_PATH,actor2character,SEPARATOR=",",IMAGE_FORMAT="jpg"):
    characters={character:{"count":0,"paths":[]} for character in actor2character.values()}#counts the number of pictures per character
    key_error_messages=""#print at the end for a better console usage
    request_went_wrong=[]
    for i,image_json in enumerate(image_jsons['allImages']):
        label=[]
        caption=image_json['altText']
        caption=caption.replace(", and",", ").replace("Still of ","")
        caption=re.sub(" in .*"," ",caption)
        caption=re.sub(" at an event .*"," ",caption)
        for actor in re.split(",| and",caption):
            character=actor2character.get(actor.strip())
            if character is not None:
                label.append(character)
            else:
                key_error_messages+=f"{actor.strip()} is not in actor2character. (Original caption: {image_json['altText']})\n"
        if label != []:
            request=requests.get(image_json['src'])
            if request.status_code != requests.codes.ok:
                image_json["request_status_code"]=request.status_code
                request_went_wrong.append(image_json)
            else:
                image_jsons['allImages'][i]['path']=[]
                for character in label:
                    dir_path=os.path.join(IMAGE_PATH,character)
                    file_name=f"{SEPARATOR.join(label)}.{characters[character]['count']}.{IMAGE_FORMAT}"
                    cut_label=0#prevents OSError: [Errno 36] File name too long
                    while len(file_name) > MAX_FILE_NAME_LENGTH:
                        cut_label+=1
                        file_name=f"{SEPARATOR.join(label[:-cut_label])}.{characters[character]['count']}.{IMAGE_FORMAT}"
                    path=os.path.join(dir_path,file_name)
                    write_image(request,dir_path,path)
                    characters[character]["count"]+=1
                    characters[character]["paths"].append(path)
                    print((
                        f"\rimage {i}/{image_jsons['totalImageCount']}. "
                    ),end="")# from url {image_json['src']}
                    image_jsons['allImages'][i]['path'].append(path)
                    image_jsons['allImages'][i]['label']=label
    print()
    key_error_messages_path=os.path.join(IMAGE_PATH,f".key_error_messages.txt")
    n_key_error_messages=len(key_error_messages.split('\n'))
    print(f"there were {n_key_error_messages} images which had a problem mapping caption to a character :",end="")
    print(f"(Also gets logged in {key_error_messages_path})")
    print(key_error_messages,"\n")
    with open(key_error_messages_path,"w") as file:
        file.write(key_error_messages)
    print(f"Something went wrong with {len(request_went_wrong)} requests:")
    print(request_went_wrong)
    image_jsons['characters']=characters
    return image_jsons

def main(SERIE_URI,SERIE_IMDB_URL,IMAGE_PATH,CHARACTERS_PATH,N_COL,SEPARATOR,IMAGE_FORMAT):
    print(SERIE_URI,SERIE_IMDB_URL)
    if not os.path.exists(IMAGE_PATH):
        os.mkdir(IMAGE_PATH)
    characters=read_characters(CHARACTERS_PATH,N_COL,SEPARATOR)
    actor2character={actor:character for character,_,_,actor,_ in characters}
    warnings.warn("one to one mapping actor:character, not efficient if several actors play the same character")
    image_jsons=None
    for url in SERIE_IMDB_URL:
        media_viewer_url=get_url_from_serie_page(url)
        image_jsons=get_image_jsons_from_url(media_viewer_url,image_jsons)
        # imdb_id=url.split('/')[-2]
        # with open(f"{imdb_id}.json","w") as file:
        #     json.dump(image_jsons,file)
    image_jsons=query_image_from_json(image_jsons,IMAGE_PATH,actor2character,SEPARATOR,IMAGE_FORMAT)
    with open(os.path.join(IMAGE_PATH,"images.json"),"w") as file:
        json.dump(image_jsons,file)
    print("\ndone scraping ;)")
    return image_jsons

if __name__ == '__main__':
    from images import SERIE_URI,SERIE_IMDB_URL,IMAGE_PATH,N_COL,SEPARATOR
    main(SERIE_URI,SERIE_IMDB_URL,IMAGE_PATH,N_COL,SEPARATOR)

# # Keep for ref

# actor2character={actor:"" for character,_,_,actor,_ in characters}
# for character,_,_,actor,_ in characters:
#     if actor2character[actor]!="":
#         actor2character[actor]+=SEPARATOR
#     actor2character[actor]+=character
