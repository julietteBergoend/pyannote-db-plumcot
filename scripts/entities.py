#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This script should automatically annotate entities based on simple rules
(e.g. assign 'I' pronoun to the current speaker)

@author: Sharleyne Lefevre
"""

msg = 'This script should automatically annotate entities based on simple rules\n ' \
      'However it is not clear in which order functions should be processed and some lines should be commented depending on the serie.\n ' \
      'In any case it should be not launched as is and has been pushed to the git repo only for future reference.\n ' \
      'Apologies for the french comments.'
raise NotImplementedError(msg)

import os
from os import path

import en_core_web_sm
import nltk
import pandas as pd
from nltk.stem import WordNetLemmatizer

nlp = en_core_web_sm.load()
import operator
from tempfile import mkstemp
from shutil import move, copymode
from os import fdopen, remove
import re

SERIE = "HarryPotter"
SEASON = "Episode02"

GLOBAL_PATH = "/vol/work3/lefevre/pyannote-db-plumcot/Plumcot/data/"
INPUT_FOLDER = str(GLOBAL_PATH) + SERIE + "/"
PATH_CSV = "/people/lefevre/Bureau/projet/dev/CSV/"

TXT = ".txt"
CONLL = ".conll"
CSV = ".csv"
JSON = ".json"


def getFiles(directory):
    texts = {}
    for foldername in os.listdir(directory):
        if os.path.isdir(path.join(directory, foldername)):
            for filename in os.listdir(path.join(directory, foldername)):
                (basename, ext) = path.splitext(filename)
                if ext == TXT and SERIE in filename and SEASON in filename:
                    with open(path.join(directory, foldername, filename), 'r',
                              encoding='utf8', errors='ignore') as file:
                        texts[str(directory) + str(foldername) + "/" + str(
                            basename)] = file.read()

    return texts


def getCSVFiles(directory):
    texts = {}
    for filename in os.listdir(directory):
        if CSV in filename:
            with open(path.join(directory, filename), 'r', encoding='utf8') as file:
                if "doccano" in filename:
                    texts[str(directory) + str(filename)] = pd.read_csv(file, sep='\t')
                else:
                    texts[str(directory) + str(filename)] = pd.read_csv(file, sep=';')
    return texts


def getJSONFiles(directory):
    texts = {}
    for filename in os.listdir(directory):
        if JSON in filename or CONLL in filename:
            with open(path.join(directory, filename), 'r', encoding='utf8') as file:
                texts[str(directory) + str(filename)] = pd.read_csv(file, sep='\t')
    return texts


def semi_auto_loc_annotation():
    print("Étape 1 : Création des CSV et CONLL...")

    files = getFiles(INPUT_FOLDER)
    names = []  # ['cooper', 'sheldon', 'sheldon_cooper', 'hofstadter', 'leonard', 'leonard_hofstadter', 'althea', 'penny', 'wolowitz', 'howard', 'howard_wolowitz', 'koothrappali', 'raj', 'raj_koothrappali', 'from', 'voice', 'voice_from_buzzer', 'kurt', 'man']

    for filename, fileContent in files.items():
        sentences = []

        """ A enrichir pour les surnoms ou si le nom normalisé de le contient pas """
        """BreakingBad"""
        # names.append("walt")
        # names.append("sky")

        """Lost"""
        # names.append("sawyer")

        """SW"""
        # names.append("artoo")
        # names.append("chancellor")

        """TWD"""
        # names.append("sophia")

        """TBBT"""
        # names.append("rajesh")
        # names.append("lesley") 
        # names.append("shelly") 

        """GOT"""
        # names.append("ned")
        # names.append("cat")
        # names.append("khaleesi")
        # names.append("littlefinger")
        # names.append("jon_arryn") # personnage mort qui n'a jamais parlé donc ajout manuel
        # names.append("gregor_clegane")
        # names.append("aerys_targaryen") # comme pour jon_arryn
        # names.append("sam")

        for i in range(1, len(fileContent.split("\n")) + 1):
            line = fileContent.split("\n")[i - 1]
            if line != "":
                if line.endswith("..."):
                    line = line.replace("...", "... .")
                if not line.endswith('.') and not line.endswith(
                        '?') and not line.endswith('!') and not line.endswith(
                        ' ') and not line.endswith("'"):
                    line = line.replace(line, line + ".")
                # Adding sentences in list
                sentences.append(line + ' ')

                # Adding speaker names in list        
                if not "#" in line.split()[0]:
                    if "_" in line.split()[0]:
                        lastName = line.split()[0].split("_")[1]
                        firstName = line.split()[0].split("_")[0]
                        if lastName != "in" and lastName != "who":
                            if firstName != "he":  # bartender_in_leaky_cauldron -> sinon tag tous les "in" avec ce nom
                                if lastName not in names or firstName not in names:
                                    names.append(lastName)
                                    names.append(firstName)
                                    names.append(line.split()[0])
                        else:
                            names.append(firstName)
                    else:
                        lastName = line.split()[0]
                        if lastName not in names:
                            names.append(
                                lastName)  # ajout des noms normalisés dans une liste
                else:
                    name = line.split()[0].split('#')[0]
                    names.append(name)

        names2 = [item for item in names if
                  not "." in item and item != "he" and item != "emily_" and item != "should" and item != "all" and item != "sir" and item != "portrait_" and item != "old" and item != "man" and item != "REDSHIRT_" and item != "professor" and item != "mr" and item != "the" and item != "of"]

        filename = filename.split("/")[-1]
        lemmatizer = WordNetLemmatizer()

        """Listes à enrichir selon la série concernée"""
        """TBBT"""
        # masculin_parents = ["dr_vm_koothrappali", "mike_rostenkowski"]
        # feminin_parents = ["mrs_koothrappali", "susan", "dr_beverly_hofstadter", "mary_cooper", "debbie_wolowitz"]

        """HP"""
        masculin_parents = ["james_potter", "mr_arthur_weasley"]
        feminin_parents = ["lily_potter", "mrs_molly_weasley"]

        """TWD"""
        # masculin_parents = ["rick_grimes", "hershel_greene"]
        # feminin_parents = ["lori_grimes"]

        """SW"""
        # masculin_parents = ["no_father"]
        # feminin_parents = ["shmi_skywalker"]

        """BreakingBad"""
        # masculin_parents = ["walter_white"]
        # feminin_parents = ["skyler_white"]

        """no_parents"""
        # masculin_parents = ["no_father"]
        # feminin_parents = ["no_mother"]

        dataframe = {}

        dataframe['token'] = []
        dataframe['referenceTo'] = []
        dataframe['POS'] = []
        dataframe['TAG'] = []
        dataframe['dep'] = []
        dataframe['idChar'] = []
        dataframe['lemma'] = []
        dataframe['speaker'] = []
        dataframe['entityType'] = []
        dataframe['idEntity'] = []
        dataframe['idDoc'] = []
        dataframe['idSent'] = []
        dataframe['idWord'] = []

        iterEntity = 0  # iterateur pour les identifiants d'entités

        iterSent = 0  # iterateur de phrase

        for j in range(len(sentences)):
            iterWord = 0  # iterateur de mot
            listTuples = []
            toMergeWithListTuples = []
            newListTuples = []
            iterSent += 1
            sentence = sentences[j]

            if "#" in sentence:  # voice_from_buzzer#unknown#TheBigBangTheory.Season01.Episode01
                sentence = sentence.replace(sentence.split(" ")[0],
                                            sentence.split(" ")[0].split("#")[0])

            if "Koothrapali" in sentence:  # faute dans le nom de Raj
                sentence = sentence.replace("Koothrapali", "Koothrappali")

            # Spacy    
            doc = nlp(sentence)
            listTuples = [(token.text, token.pos_, token.tag_, token.dep_) for token in
                          doc]
            toMergeWithListTuples = [(token.text, token.label_) for token in doc.ents]

            # Merge tuples from lists
            # ex : listTuples = ('ten', 'NUM', 'CD', 'nummod')
            #      toMergeWithListTuples = ('ten', 'CARDINAL')
            #      newListTuples = ('ten', 'NUM', 'CD', 'nummod', 'CARDINAL')
            id = operator.itemgetter(0)
            idinfo = {id(rec): rec[1:] for rec in toMergeWithListTuples}
            for info in listTuples:
                if id(info) in idinfo:
                    newListTuples.append(info + idinfo[id(info)])
                else:
                    newListTuples.append(info)

            startIndex = 0
            if len(newListTuples) > 0:
                startIndex = 0 - len(newListTuples[0][0])
            for k in range(len(newListTuples)):
                word = newListTuples[k][0]
                wordLower = word.lower()
                pos = newListTuples[k][1]
                tag = newListTuples[k][2]
                dep = newListTuples[k][3]
                typeEN = ''
                if len(newListTuples[k]) > 4:
                    typeEN = newListTuples[k][4]

                # Séparer les ponctuation des mots par un espace avant et après. Idem pour les don't -> do n't
                # Adapté à la tokenization de doccano    
                sentenceSepPunct = sentence.replace(". ", " . ")
                sentenceSepPunct = sentenceSepPunct.replace(", ", " , ")
                sentenceSepPunct = sentenceSepPunct.replace("! ", " ! ")
                sentenceSepPunct = sentenceSepPunct.replace("? ", " ? ")
                sentenceSepPunct = sentenceSepPunct.replace("'s ", " 's ")
                sentenceSepPunct = sentenceSepPunct.replace("n't ", " n't ")
                sentenceSepPunct = sentenceSepPunct.replace("'m ", " 'm ")
                sentenceSepPunct = sentenceSepPunct.replace("'ll ", " 'll ")
                sentenceSepPunct = sentenceSepPunct.replace("-", " - ")
                sentenceSepPunct = sentenceSepPunct.replace(".. . ", " ... ")
                sentenceSepPunct = re.sub(r'([A-Z]{1}) (\.)', r'\1\2', sentenceSepPunct)
                sentenceSepPunct = re.sub(r'([A-Za-z]{1}) (-) (.*)( )', r'\1\2\3\4',
                                          sentenceSepPunct)
                sentenceSepPunct = re.sub(r'(Mr|Mrs|¾|Ms) (\.)', r'\1\2',
                                          sentenceSepPunct)
                sentenceSepPunct = re.sub(r'(\.) (\.\.\.)', r'\1\2', sentenceSepPunct)
                sentenceSepPunct = sentence.replace(r'(C - 3)', "C-3")

                wordStartIndex = startIndex

                startIndex = startIndex + len(word)
                wordEndIndex = startIndex
                if k > 0:
                    startIndex = startIndex + 1

                if word != newListTuples[0][
                    0]:  # si le mot n'est pas le premer mot (nom normalisé du locuteur)
                    iterWord += 1

                    if iterWord == 1:
                        concatLocWord = newListTuples[0][0] + " " + word
                        onlyWord = concatLocWord.split(" ")[1]
                        dataframe['token'].append(concatLocWord)
                        dataframe['lemma'].append(lemmatizer.lemmatize(onlyWord))
                    else:
                        dataframe['token'].append(word)
                        dataframe['lemma'].append(lemmatizer.lemmatize(word))

                    dataframe['POS'].append(pos)
                    dataframe['TAG'].append(tag)
                    dataframe['dep'].append(dep)
                    dataframe['idChar'].append([wordStartIndex, wordEndIndex])
                    dataframe['entityType'].append(typeEN)
                    dataframe['speaker'].append(newListTuples[0][0])
                    dataframe['idDoc'].append(filename)
                    dataframe['idSent'].append(iterSent)
                    dataframe['idWord'].append(iterWord)

                    if wordLower in names2:
                        iterEntity += 1
                        dataframe['referenceTo'].append(wordLower)
                        dataframe['idEntity'].append(iterEntity)

                    elif wordLower in ["i", "my", "me", "myself", "mine"]:
                        iterEntity += 1
                        dataframe['referenceTo'].append(newListTuples[0][0])
                        dataframe['idEntity'].append(iterEntity)

                    elif wordLower in ["you", "ya", "your", "yourself",
                                       "yours"] and j - 1 >= 0:
                        locSentBefore = nltk.word_tokenize(sentences[j - 1])[
                            0]  # nom speaker phrase -1
                        if j < len(sentences) - 1:
                            locSentAfter = nltk.word_tokenize(sentences[j + 1])[
                                0]  # nom speaker phrase +1
                        if j < len(sentences) - 2:
                            locSentAfterAfter = nltk.word_tokenize(sentences[j + 2])[0]

                        if locSentBefore == locSentAfter:  # si le loc de la phrase d'avant et après est le même
                            iterEntity += 1
                            dataframe['referenceTo'].append(
                                locSentAfter)  # le you / your fait reference à cette personne
                            dataframe['idEntity'].append(iterEntity)

                        elif locSentBefore != locSentAfter and newListTuples[0][
                            0] != locSentBefore and newListTuples[0][0] != locSentAfter:
                            if newListTuples[k + 1][
                                0].lower() in names2:  # si le mot qui suit "you" est dans la liste des noms
                                iterEntity += 1
                                dataframe['referenceTo'].append(newListTuples[k + 1][
                                                                    0].lower())  # le "you" désigne cette personne
                                dataframe['idEntity'].append(iterEntity)

                            elif sentence.endswith('?') and newListTuples[k - 1][
                                0].lower() in ['do', 'did'] or newListTuples[k + 1][
                                0].lower() in ['do', 'did'] and newListTuples[k - 1][
                                0].lower() != "guys":  # si la phrase courante est une question et que "you" est précédé de "do"
                                iterEntity += 1
                                dataframe['referenceTo'].append(
                                    locSentAfter)  # on imagine que la personne va répondre donc est la référence au you
                                dataframe['idEntity'].append(iterEntity)

                            elif newListTuples[k + 1][0].lower() == "guys":
                                iterEntity += 1
                                dataframe['referenceTo'].append("multiple_persons")
                                dataframe['idEntity'].append(iterEntity)

                            elif sentence.endswith('?'):
                                iterEntity += 1
                                dataframe['referenceTo'].append(locSentAfter)
                                dataframe['idEntity'].append(iterEntity)

                            else:
                                iterEntity += 1
                                dataframe['referenceTo'].append(locSentBefore)
                                dataframe['idEntity'].append(iterEntity)

                        elif newListTuples[0][0] == locSentBefore:
                            iterEntity += 1
                            dataframe['referenceTo'].append(locSentAfter)
                            dataframe['idEntity'].append(iterEntity)

                        elif newListTuples[0][0] == locSentAfter:
                            iterEntity += 1
                            dataframe['referenceTo'].append(locSentAfterAfter)
                            dataframe['idEntity'].append(iterEntity)

                        else:
                            dataframe['referenceTo'].append('')
                            dataframe['idEntity'].append('')

                    elif wordLower in ["she", "her", "herself"]:
                        iterEntity += 1
                        """Listes à enrichir selon la série concernée"""
                        # dataframe['referenceTo'].append("penny")
                        dataframe['referenceTo'].append("hermione_granger")
                        # dataframe['referenceTo'].append("lori_grimes")
                        # dataframe['referenceTo'].append("padme")
                        # dataframe['referenceTo'].append("skyler_white")
                        # dataframe['referenceTo'].append("UNKNOWN")
                        dataframe['idEntity'].append(iterEntity)

                    elif wordLower in ["he", "his", "him", "himself"]:
                        iterEntity += 1
                        dataframe['referenceTo'].append("UNKNOWN")
                        dataframe['idEntity'].append(iterEntity)

                    elif wordLower in ["mommy", "mom", "daddy", "dad", "papa", "mother",
                                       "father"]:
                        # si le loc de la phrase d'avant et d'après est dans les listes des noms de parents et que ce sont les mêmes
                        if locSentAfter in masculin_parents and locSentBefore in masculin_parents or locSentAfter in feminin_parents and locSentBefore in feminin_parents and locSentAfter == locSentBefore:
                            iterEntity += 1
                            dataframe['referenceTo'].append(locSentAfter)
                            dataframe['idEntity'].append(iterEntity)

                        elif newListTuples[k - 1][0].lower() not in ["your", "'s", "his",
                                                                     "her", "our"]:
                            if word.lower() in ["father", "dad", "daddy", "papa"]:
                                for elem in masculin_parents:
                                    if newListTuples[0][0].split("_")[-1] == \
                                            elem.split("_")[-1]:
                                        iterEntity += 1
                                        dataframe['referenceTo'].append(elem)
                                        dataframe['idEntity'].append(iterEntity)
                                        break
                                    else:
                                        iterEntity += 1
                                        dataframe['referenceTo'].append(
                                            newListTuples[0][0] + "'s_father")
                                        dataframe['idEntity'].append(iterEntity)
                                        break
                            else:
                                for elem in feminin_parents:
                                    if newListTuples[0][0].split("_")[-1] == \
                                            elem.split("_")[-1]:
                                        iterEntity += 1
                                        dataframe['referenceTo'].append(elem)
                                        dataframe['idEntity'].append(iterEntity)
                                        break
                                    else:
                                        iterEntity += 1
                                        dataframe['referenceTo'].append(
                                            newListTuples[0][0] + "'s_mother")
                                        dataframe['idEntity'].append(iterEntity)
                                        break
                        else:
                            iterEntity += 1
                            dataframe['referenceTo'].append('PARENTS')
                            dataframe['idEntity'].append(iterEntity)

                    elif wordLower == "parents":
                        if newListTuples[k - 1][0].lower() == "my":
                            iterEntity += 1
                            dataframe['referenceTo'].append(
                                newListTuples[0][0] + "'s_parents")
                            dataframe['idEntity'].append(iterEntity)
                        else:
                            iterEntity += 1
                            dataframe['referenceTo'].append('PARENTS')
                            dataframe['idEntity'].append(iterEntity)

                    elif wordLower in ["we", "us", "our"]:
                        iterEntity += 1
                        dataframe['referenceTo'].append("multiple_persons")
                        dataframe['idEntity'].append(iterEntity)

                    else:
                        dataframe['referenceTo'].append('')
                        dataframe['idEntity'].append('')

            df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in dataframe.items()]))

            for index, row in df.iterrows():
                val = df.at[index, 'referenceTo']
                for name in names2:
                    if "_" in name:
                        if str(val).lower() == name.split("_")[0] or str(val).lower() == \
                                name.split("_")[1]:
                            df.at[index, 'referenceTo'] = name

                        """Listes à enrichir selon la série concernée"""
                        """SW"""
                        # if val.lower() == "artoo":
                        #     df.at[index,'referenceTo'] = "r2d2"
                        # if val.lower() == "chancellor":
                        #     df.at[index,'referenceTo'] = "senator_palpatine"

                        """Lost"""
                        # if val.lower() == "sawyer":
                        #     df.at[index,'referenceTo'] = "john_ford"

                        """BreakingBad"""
                        # if val.lower() == "walt":
                        #     df.at[index,'referenceTo'] = "walter_white"
                        # if val.lower() == "sky":
                        #     df.at[index,'referenceTo'] = "skyler_white"

                        """TBBT"""
                        # if val.lower() == "rajesh":
                        #     df.at[index,'referenceTo'] = "raj_koothrappali"
                        # if val.lower() == "shelly":
                        #     df.at[index,'referenceTo'] = "sheldon_cooper"    
                        # if val.lower() == "lesley":
                        #     df.at[index,'referenceTo'] = "leslie_winkle"  

                        """GOT"""
                        # if val.lower() == "ned":
                        #     df.at[index,'referenceTo'] = "eddard_stark"    
                        # if val.lower() == "cat":
                        #     df.at[index,'referenceTo'] = "catelyn_stark"
                        # if val.lower() == "khaleesi":
                        #     df.at[index,'referenceTo'] = "daenerys_targaryen"        
                        # if val.lower() == "littlefinger":
                        #   df.at[index,'referenceTo'] = "petyr_baelish"  
                        # if val.lower() == "sam":
                        #   df.at[index,'referenceTo'] = "samwell_tarly"

        # Pour formater le CoNLL -> Ajouter une ligne vide après chaque phrase
        mask = df['idSent'].ne(df['idSent'].shift(-1))
        df1 = pd.DataFrame('', index=mask.index[mask] + .5, columns=df.columns)
        df = pd.concat([df, df1]).sort_index().reset_index(drop=True).iloc[:-1]

        # ECRITURE
        print(filename, "OK")
        df.to_csv(PATH_CSV + "semi-auto-annot_" + filename + ".conll", sep='\t',
                  encoding='utf-8', index=False, header=False)
        df.to_csv(PATH_CSV + "semi-auto-annot_" + filename + ".csv", sep=';',
                  encoding='utf-8')


def removeTabLines(pattern, subst):
    print("Étape 2 : Formatage des CONLL pour Doccano...")

    conllFiles = getJSONFiles(PATH_CSV)
    for filename, fileContent in conllFiles.items():
        if CONLL in filename:
            # Create temp file
            fh, abs_path = mkstemp()
            with fdopen(fh, 'w') as new_file:
                with open(filename, encoding='utf8') as old_file:
                    for line in old_file:
                        new_file.write(line.replace(pattern, subst))
            # Copy the file permissions from the old file to the new file
            copymode(filename, abs_path)
            # Remove original file
            remove(filename)
            # Move new file
            move(abs_path, filename)
    print("Étape 2 : Terminée")


pattern = "\t\t\t\t\t\t\t\t\t\t\t\t"
subst = ""


def jsonToCSV():  # Convertir la sortie Doccano JSONL en CSV
    print("Étape 3 : Conversion des JSON (sortie Doccano) en CSV...")

    jsonFiles = getJSONFiles(PATH_CSV)
    for filename, fileContent in jsonFiles.items():
        if JSON in filename and SERIE in filename:
            # Modification de l'extension car doccano génère un .json1
            base = os.path.splitext(filename)[0]
            # Nouvelle ext = .json
            os.rename(filename, base + '.json')
            basename = filename.split('/')[-1].rsplit(".", 1)[0]
            df = pd.read_json(filename, lines=True)
            df["idChar"] = ""
            df["label"] = ""

            df2 = pd.DataFrame(columns=['idSent', 'idChar', 'label'])

            # Modification des index de start et end des mots sans prendre en compte le nom du loc en début de ligne
            for index, row in df.iterrows():
                idCharLabels = []
                listIdChar = []
                listLabels = []
                text = df.at[index, 'text']
                labels = df.at[index, 'labels']
                for label in labels:
                    if label[0] == 0:
                        idCharLabels.append(
                            [label[0], label[1] - len(text.split(' ')[0]) - 1, label[2]])
                        listIdChar.append(
                            [label[0], label[1] - len(text.split(' ')[0]) - 1])
                        listLabels.append(label[2])
                    else:
                        idCharLabels.append([label[0] - len(text.split(' ')[0]) - 1,
                                             label[1] - len(text.split(' ')[0]) - 1,
                                             label[2]])
                        listIdChar.append([label[0] - len(text.split(' ')[0]) - 1,
                                           label[1] - len(text.split(' ')[0]) - 1])
                        listLabels.append(label[2])

                # If 0 entity
                if len(labels) == 0:
                    df2 = df2.append({'idSent': index + 1, 'idChar': "", 'label': ""},
                                     ignore_index=True)
                # If 1 entity    
                elif len(labels) == 1:
                    for l, c in zip(listLabels, listIdChar):
                        df2 = df2.append({'idSent': index + 1, 'idChar': c, 'label': l},
                                         ignore_index=True)
                # If more than 1 entities
                elif len(labels) > 1:
                    # for each label and idChar in list of entities
                    for l, c in zip(listLabels, listIdChar):
                        df2 = df2.append({'idSent': index + 1, 'idChar': c, 'label': l},
                                         ignore_index=True)

            df2.to_csv(PATH_CSV + "doccano_" + basename + CSV, sep='\t', encoding='utf-8')
            print("Étape 3 : Terminée")
            print("Vous pouvez passer à l'annotation dans Doccano.")


def mergeData():
    print("Étape 4 : Fusion des données...")

    csvFiles = getCSVFiles(PATH_CSV)
    doccano = []
    semi_auto_annot = []
    sameFilename = []
    for filename, fileContent in csvFiles.items():
        filename = filename.split("/")[-1]
        if "semi-auto-annot" in filename and SERIE in filename:
            semi_auto_annot.append(filename)
        if "doccano" in filename and SERIE in filename:
            doccano.append(filename)

    # [['doccano_StarWars.Episode03.csv', 'semi-auto-annot_StarWars.Episode03.csv'], ...]
    for doc in doccano:
        for auto in semi_auto_annot:
            if doc.split("_")[1] == auto.split("_")[1]:
                sameFilename.append([doc, auto])

    os.chdir(PATH_CSV)
    for listFilename in sameFilename:
        temp = listFilename[0].split('_')
        temp = temp[1].rsplit('.', 1)
        basename = temp[0]
        doccano = []
        # on ouvre le csv Doccano et le csv Auto
        dfDoccano = pd.read_csv(listFilename[0], sep='\t')
        dfAuto = pd.read_table(listFilename[1], sep=';')

        dfAuto["labelDoccano"] = ""
        for index, row in dfAuto.iterrows():
            idCharAuto = row["idChar"]
            idSentAuto = row["idSent"]
            for index2, row2 in dfDoccano.iterrows():
                idCharDoccano = row2["idChar"]
                idSentDoccano = row2["idSent"]
                label = row2["label"]
                if idCharAuto == idCharDoccano and idSentAuto == idSentDoccano:
                    dfAuto.at[index, "labelDoccano"] = label
        dfAuto.to_csv(PATH_CSV + "merge_" + basename + CSV, sep=';', encoding='utf-8')
        print("Étape 4 : Terminée")
    return


def stats():
    print("Étape 5 : Création d'un tableau de statistiques...")

    csvMergeFiles = getCSVFiles(PATH_CSV)
    dfStats = pd.DataFrame(
        columns=['Serie', 'Nb episodes', 'Nb phrases', 'Nb annotations', 'Noms',
                 'Pronoms', 'Pronoms poss', 'Noms propres', 'multiple_persons', 'Autres',
                 'Auto=Manuel', 'Auto!=Manuel'])
    series = ["StarWars", "TheBigBangTheory", "TheWalkingDead", "HarryPotter",
              "GameOfThrones", "TheOffice", "BuffyTheVampireSlayer", "Lost",
              "BreakingBad", "Friends", "BattletarGalactica"]

    for serie in series:
        total_episodes = 0
        total_sent = 0
        total_annot = 0
        total_noun = 0
        total_pronoun = 0
        total_pronoun_poss = 0
        total_proper_noun = 0
        total_multiple_persons = 0
        other = 0

        annotation_identique = 0
        annotation_differente = 0
        for filename, fileContent in csvMergeFiles.items():
            # for serie in series:
            if "merge" in filename and serie in filename:
                total_episodes += 1
                for index, row in fileContent.iterrows():
                    annotAuto = row["referenceTo"]
                    annotManuelle = row["labelDoccano"]
                    word = row["token"]
                    pos = row["POS"]
                    tag = row["TAG"]
                    idSent = row["idSent"]

                    # compter le nombre d'annotations révisées Doccano
                    if isinstance(annotManuelle, str):
                        total_annot += 1
                        if tag == "PRP" and word.lower() != "we":
                            total_pronoun += 1
                        elif tag == "PRP$":
                            total_pronoun_poss += 1
                        elif tag == "NNP":
                            total_proper_noun += 1
                        elif annotManuelle == "multiple_persons":
                            total_multiple_persons += 1
                        elif tag == "NN" or tag == "NNPS":
                            total_noun += 1
                        else:
                            other += 1

                        if annotManuelle == annotAuto:
                            annotation_identique += 1
                        elif annotManuelle != annotAuto:
                            annotation_differente += 1

                # compter le nombre de lignes de dialogue    
                total_sent += fileContent["idSent"].iat[-1]

        dfStats = dfStats.append({'Serie': serie,
                                  'Nb episodes': int(total_episodes),
                                  'Nb phrases': int(total_sent),
                                  'Nb annotations': total_annot,
                                  'Noms': total_noun,
                                  'Pronoms': total_pronoun,
                                  'Pronoms poss': int(total_pronoun_poss),
                                  'Noms propres': total_proper_noun,
                                  'multiple_persons': total_multiple_persons,
                                  'Autres': other,
                                  'Auto=Manuel': annotation_identique,
                                  'Auto!=Manuel': annotation_differente},
                                 ignore_index=True)

    dfStats.to_csv("/people/lefevre/Bureau/projet/dev/Stat_Annotations.ods", sep='\t',
                   encoding='utf-8')
    print("Étape 5 : Terminée")
    return


semi_auto_loc_annotation()
removeTabLines(pattern, subst)
# jsonToCSV()
# mergeData()
# stats()
