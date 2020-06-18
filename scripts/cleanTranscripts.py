# -*- coding: utf-8 -*-
"""
Created on Thu Dec 19 15:04:23 2019

@author: lefevre
"""
msg = 'This file should clean the transcripts scraped using extractTranscripts.py\n ' \
      'However paths are inconsistent with Plumcot structure and it is not clear in which order functions should be processed.\n ' \
      'In any case it should be not launched as is and has been pushed to the git repo only for future reference.\n ' \
      'Apologies for the french comments.'
raise NotImplementedError(msg)

import codecs
import os
import re
import sys

# nlp = spacy.load('en_core_web_sm')
sys.setrecursionlimit(90000)


def openFilesTXT():
    path = 'txt/'
    texts = {}
    for foldername in os.listdir(path):
        if os.path.isdir(path + foldername):
            for filename in os.listdir(path + foldername):
                if '.txt' in filename:
                    file = codecs.open(path + foldername + '/' + filename, 'r',
                                       'utf8').read()
                    texts[filename.replace(".txt", "")] = file
    return texts


def openFilesTXT_cleaned():
    path = 'txt_cleaned/'
    texts = {}
    for foldername in os.listdir(path):
        if os.path.isdir(path + foldername):
            for filename in os.listdir(path + foldername):
                if '.txt' in filename:
                    file = codecs.open(path + foldername + '/' + filename, 'r',
                                       'utf8').read()
                    texts[filename.replace(".txt", "")] = file
    return texts


def openFilesTEMP():
    path = 'temp/'
    texts = {}
    for foldername in os.listdir(path):
        if os.path.isdir(path + foldername):
            for filename in os.listdir(path + foldername):
                # os.rename(path+foldername+'/'+filename, path+foldername+'/'+filename.replace('.temp', '.txt'))
                if '.txt' in filename:
                    file = codecs.open(path + foldername + '/' + filename, 'r',
                                       'utf8').read()
                    texts[filename.replace(".txt", "")] = file
    return texts


def clearDataTXT():
    filesTXT = openFilesTXT()

    for fileName, fileContent in filesTXT.items():

        regex = r'(\<.*?\>)|(\[.*?\])|(\(.*?\))'
        fileContent = re.sub(regex, '',
                             fileContent)  # Retirer ce qui est entre <>, () et []

        if "TheWalkingDead" in fileName or "TheOffice" in fileName:
            locIdentification = r'([a-zA-Zéè\-\#]*?)( ?)(\:)'
            automaticMessage = r'(<!-- )(NewPP)(.*\n)*(.)*'
            automaticMessage2 = r'(\.push\;)([a-zA-Z ]*)(Office.*)'
            spaceNamePunct = r'([a-zA-Zéè]*?)(\:)'
            addWhitespace = r'([a-zA-Z ]*)(\,|\.){1,3}([a-zA-Z]*)'
            beforeScript = r'[0-9]{2,}(.*\n.*push\; )(\n)'

            fileContent = fileContent.replace(
                '(adsbygoogle = window.adsbygoogle || ).push({});',
                '')  # Retirer un message automatique
            emptyLinesRemoved = " ".join(fileContent.split())  # Retirer les lignes vides
            fileContent = re.sub(locIdentification, r'\n\1\2\3',
                                 emptyLinesRemoved)  # Mettre les locuteurs en début de ligne
            fileContent = re.sub(automaticMessage, '',
                                 fileContent)  # Retirer un message automatique
            fileContent = re.sub(automaticMessage2, '',
                                 fileContent)  # Retirer un message automatique
            fileContent = re.sub(spaceNamePunct, r'\1 \2',
                                 fileContent)  # Mettre un espace entre le nom et les :
            fileContent = re.sub(addWhitespace, r'\1\2 \3',
                                 fileContent)  # Mettre un espace entre une ponctuation et le mot suivant
            fileContent = fileContent.replace('  ',
                                              ' ')  # Transformer les doubles espaces en un seul espace
            fileContent = re.sub(beforeScript, '',
                                 fileContent)  # Retirer un message automatique

            # with codecs.open ("txt_cleaned/"+fileName.split(".")[0]+"/"+fileName+".txt",'w', "utf8") as f:
            #    f.write(fileContent) 

        elif "HarryPotter" in fileName:
            for line in fileContent.split('\n'):
                episode = ""
                findLineWithLoc = r'^((?!Scene|LOCATION).){1,20}(:).*$'
                removeOnParenthesis = r'(\{.*\})'
                lineWithLoc = re.match(findLineWithLoc, line)

                if lineWithLoc:
                    lines = lineWithLoc.group()
                    lines = re.sub(removeOnParenthesis, '', lines)
                    lines = lines.replace("  ", " ")
                    episode = lines + "\n"

                # with codecs.open ("txt_cleaned/"+fileName.split(".")[0]+"/"+fileName+".txt",'a', "utf8") as f:
                #    f.write(e) 

        elif "GameOfThrones" in fileName:

            for line in fileContent.split('\n'):
                episode = ""
                findLineWithLoc = r'^((?!INT|EXT|CUT TO).){1,20}(:).*$'
                lineWithLoc = re.match(findLineWithLoc, line)
                if lineWithLoc:
                    lines = lineWithLoc.group()
                    episode = lines + "\n"

                # with codecs.open ("txt_cleaned/"+fileName.split(".")[0]+"/"+fileName+".txt",'a', "utf8") as f:
                #    f.write(episode) 


        elif "StarWars" in fileName:
            episode = ""
            automaticMessage = r'(\n<!-- \n)(.*\n)*(-->\n\n)'
            narr = r'(INT. |EXT. |IN THE COCKPIT. |PAGE. |OUTSIDE. |CUT TO)(.*)'
            narr2 = r'(\[.*\])|(\(.*\) )|(\[)'
            betweenStarPunct = r'(\*)(.*)(\*)'
            loc = r'([A-Z0-9]{1,}[a-zA-Z0-9éÉ. -]+)( )([A-Z0-9]{1,}[a-zA-Z0-9éÉ. ]+)( )(:)'
            narr3 = r'([0-9]+)( )(\n)'

            fileContent = re.sub(betweenStarPunct, '', fileContent)
            fileContent = re.sub(automaticMessage, '', fileContent)
            fileContent = re.sub(narr, '', fileContent)
            fileContent = re.sub(narr2, '', fileContent)
            fileContent = re.sub(loc, r'\1\2\3\5', fileContent)
            fileContent = re.sub(narr3, '', fileContent)
            fileContent = fileContent.replace("  ", " ")
            for line in fileContent.split('\n'):
                if len(line) > 0:  # si ligne n'est pas vide
                    episode = line + "\n"  # on l'ajoute à la chaine vide avec un retour de chariot
                    with codecs.open("txt_cleaned/" + fileName.split(".")[
                        0] + "/" + fileName + ".txt", 'a', "utf8") as f:
                        f.write(episode)


def finalDataTXT():
    filesTXT = openFilesTXT_cleaned()
    for fileName, fileContent in filesTXT.items():
        loc = r'(.*)( )?(:)'
        end = r'( )(\n)'
        for f in re.findall(loc, fileContent):
            fileContent = fileContent.replace(f[0], f[0].lower()).replace(f[2], '')
        fileContent = re.sub(end, '\n', fileContent)
        fileContent = fileContent.replace('  ', ' ')
        with codecs.open("txt_final/" + fileName.split(".")[0] + "/" + fileName + ".temp",
                         'w', "utf8") as f:
            f.write(fileContent)


def clearDataTemp():
    filesTEMP = openFilesTEMP()

    identifiedLoc = r'(\w* on |FATHER )?(Rick Grimes|Deanna Monroe|Rich Monroe|Carol Peletier|Aiden \(VO\)|\w*)( )?(: )'
    # la regex identifiedLoc pour les cas :
    """
    not_available Narrator: Previously on AMC's The Walking Dead RICK: What is this place? DEANNA: This is the start of sustainability, community.
    not_available FATHER GABRIEL: Rick, his group they're dangerous.
    not_available GLENN: Noah died because of you.
    not_available You tried to kill me.
    not_available DARYL: Why? MORGAN: Cause all life is precious.
    not_available DEANNA: Do it.
    not_available Morgan: Rick? Rick: I know this sounds insane, but this is an insane world.
    not_available Sasha! Abraham! Abraham: Damn straight, we'll do it live.
    not_available Sasha on radio: We're at red at the bottom of the hill.
    not_available Daryl on radio: All right, here comes the parade.
    """

    identifiedLoc2 = r'(not_available )(\w* on |FATHER )?(Rick Grimes|Deanna Monroe|Rich Monroe|Carol Peletier|Aiden \(VO\)|\w*)( )?(: )'

    for fileName, fileContent in filesTEMP.items():
        if "TheWalkingDead.Season05.Episode14" in fileName:
            fileContent = fileContent.replace(
                '<div class="scrolling-script-container">\r\n\r\n', "")

            fileContent = fileContent.replace("<br/> ", "\n")
            fileContent = fileContent.replace("<br> ", "\n")
            fileContent = re.sub(r'(<br>)(\n)(</br>)*(</div>)', '',
                                 fileContent)  # retirer les balises html
            fileContent = re.sub(r'(.*)(\-)(.*)', r'\1\n\2\3',
                                 fileContent)  # enonces qui commencent par - : retirer le tiret et mettre a la ligne
            fileContent = fileContent.replace('- ', '').replace('-', '')
            fileContent = fileContent.replace('''<br>'" ''', '\n').replace("<br/>",
                                                                           "")  # retirer les balises html
            fileContent = re.sub(r'(\{.*\} )|(\[.*\])|(\(.*\) )', '',
                                 fileContent)  # retirer ce qui est contenu entre parentheses et crochets
            fileContent = fileContent.replace("   <br/>\n", "").replace("</div>",
                                                                        "").replace(
                '<br>"', '"\n').replace("<br>", "")  # retirer les balises html
            fileContent = fileContent.replace("Previously on AMC's The Walking Dead",
                                              "").replace(
                'Previously on AMC\'s "The Walking Dead" ', "").replace(
                'Previously on AMC\'s "The Walking Dead ', "")
            fileContent = re.sub(r'( ){2,}', " ",
                                 fileContent)  # enlever les espaces en trop

            fileContent = re.sub(identifiedLoc, r"\n\1\2\3\4",
                                 fileContent)  # quand on a 2 loc par enonce : mise a la ligne

            # ajout du faux nom de locuteur not_available
            fileContent = 'not_available '.join(fileContent.splitlines(True))
            fileContent = re.sub(r'(			 |			)', "",
                                 fileContent)  # retirer des espaces precis

            fileContent = re.sub(identifiedLoc2, r"\2\3\4\5 ",
                                 fileContent)  # lorsqu'on a le nom du locuteur on ne met pas "not-available"
            fileContent = re.sub(r'(\w*)( )?(: )', r"\1 ", fileContent)
            fileContent = fileContent.replace("(VO)", "").replace("VO ", "")

            fileContent = fileContent.replace("not_available \n", "")
            fileContent = fileContent.replace("  ", " ")

            with codecs.open(
                    "temp_cleaned/" + fileName.split(".")[0] + "/" + fileName + ".txt",
                    'w', "utf8") as f:
                f.write(fileContent)


# python forced-alignment.py 24 /vol/work3/lefevre/pyannote-db-plumcot 1,2-3,4-5-6-7-8-9 --expected_time=200 --conf_threshold=0.5 --collar=0.15 --wav_path=/vol/work3/lefevre/dvd_extracted --transcripts_path=/vol/work3/lefevre/pyannote-db-plumcot/Plumcot/data/24/transcripts-no_loc --aligned_path=/vol/work3/lefevre/pyannote-db-plumcot/Plumcot/data/24/forced-alignment-no_loc
# adapter serie-split au nombre d'épisode 1 = toujours test, 2 episodes ensuite et le reste en train

def main():
    # finalDataTXT()
    # clearDataTXT()
    # finalDataTXT()
    clearDataTemp()


main()
