# How to contribute

1. Fork the repository.
2. Make changes.
3. Open a pull request.

Make sure all files are UTF8.

Make sure to follow conventions and file formats described in this document.

Open an issue if something is not clear -- we will decide on a solution and update this document accordingly.


- [series.txt](#seriestxt)
  * [One sub-directory per series / movies](#one-sub-directory-per-series---movies)
- [Scripts](#scripts)
- [Data](#data)
  * [text](#text)
    + [`characters.txt`](#-characterstxt-)
    + [`episodes.txt`](#-episodestxt-)
    + [`credits.txt`](#-creditstxt-)
    + [`transcripts/ folder`](#-transcripts--folder-)
      - [`{idEpisode}.temp`](#--idepisode-temp-)
      - [`{idEpisode}.txt`](#--idepisode-txt-)
    + [`forced-alignment/ folder`](#-forced-alignment--folder-)
      - [`<file_uri>.aligned`](#--file-uri-aligned-)
    + [`merge_{idEpisode}.csv`](#-merge--idepisode-csv-)
      - [.csv Format](#csv-format)
      - [linguistic rules for semi-automatic annotation](#linguistic-rules-for-semi-automatic-annotation)
      - [manual annotation (i.e. correction) instructions](#manual-annotation--ie-correction--instructions)
  * [images](#images)
  * [multimodal](#multimodal)
    + [fuse](#fuse)
    + [map (i.e. identify)](#map--ie-identify-)
  * [scene / narrative stuff](#scene---narrative-stuff)
- [Experiments](#experiments)
  * [ASR](#asr)
  * [NER](#ner)
  * [Speaker Diarization and Identification](#speaker-diarization-and-identification)
  
# series.txt

`series.txt` contains one line per TV (or movie) series.
Each line provides a (CamelCase) identifier, a full name, a link to its IMDB.com page, a link to its TV.com page, and a boolean set to 1 if the line corresponds to a movie.

```
$ cat series.txt
TheBigBangTheory,The Big Bang Theory,https://www.imdb.com/title/tt0898266/,http://www.tv.com/shows/the-big-bang-theory/,0
```

## One sub-directory per series / movies

For each entries in `series.txt`, there is a corresponding sub-directory called after its CamelCase identifier into the scripts folder and into the data folder.

# Scripts

All the scripts need to put on the `scripts` folder into the corresponding serie's name.

```
characters.py
credits.py
entities.py
TheLordOfTheRings/
  transcripts.py
...
```

# Data

All the clean data with be put at the root directory of the serie into a `.txt` file.
We also download all the webpages where we extract the informations into the `html_pages` folder into the corresponding task folder.

```
TheBigBangTheory/
  characters.txt
  credits.txt
  images/
    images.json
    leonard_hofstadter/
      leonard_hofstadter.0.jpg
      leonard_hofstadter,sheldon_cooper.1.jpg
      leonard_hofstadter.2.jpg
  forced-alignment/
    TheBigBangTheory_0.15collar.rttm
    TheBigBangTheory_0.5confidence.uem
    <file_uri>.aligned
  transcripts/
	TheBigBangTheory.Season01.Episode01.temp
	TheBigBangTheory.Season01.Episode01.txt
  alignment.txt
  entities.txt
  html_pages/
    characters/
    credits/
    transcripts/
      season01.episode01.html
      season01.episode02.html
      season01.episode03.html
    alignment/
    entities/
```
## text
### `characters.txt`

This file provides the list of characters (gathered from IMDb). It contains one line per character with the following information: underscore-separated identifier, actor's normalized name, character's full name, actor's full name, IMDb character page.

Note that this script is actor-centric, an actor can only play one character.

```
leonard_hofstadter,johnny_galecki,Leonard Hofstadter,Johnny Galecki,https://www.imdb.com/title/tt0898266/characters/nm0301959
```

Usage:
```bash
characters.py --serie=TheBigBangTheory
```

### `episodes.txt`

This file provides the list of episodes (gathered from IMDb). It contains one line per episode with the following information: unique episode identifier, name of the episode, IMDb episode page, TV.com episode page.

```
TheBigBangTheory.Season01.Episode01,Pilot,https://www.imdb.com/title/tt0775431/,http://www.tv.com/shows/the-big-bang-theory/pilot-939386/
```

Usage:
```bash
episodes.py --serie=TheBigBangTheory
```

For movies, we use `<serie_uri>.<episode_number>` as "episode" unique identifier (e.g. `HarryPotter.Episode01`).

### `credits.txt`

This file provides the list of characters credited in each episode. It contains one line per episode. Each episode is denoted by its normalized identifier (e.g. `TheBigBangTheory.Season01.Episode01`).

The line starts with one field for the episode and then one boolean for each character of the series/movie, with 1 if the character appears in the episode, 0 otherwise.

For instance, the line below tells that 3 characters appear in episode 1 of season 1 of The Big Bang Theory

```
TheBigBangTheory.Season01.Episode01,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0...
```

The ith binary column corresponds to the ith line in characters.txt

```bash
episodes.py --serie=TheBigBangTheory -c
```

> The Friends case: weirdly, in IMDb, the serie final is split in 2 episodes. I merged those manually so I recommend you don't rerun the episodes/credits scripts 
### `transcripts/ folder`

The transcripts folder contains 2 files for all episodes in `episodes.txt`:

#### `{idEpisode}.temp`

This file provides the manual transcript of the {idEpisode} episode without normalized names. It contains one line per speech turn.

The expected file format is the following: character identifier, followed by the actual transcription.

```
Sheldon How are you, Leonard?
Leonard Good, and you?
```

#### `{idEpisode}.txt`

This file is the same as {idEpisode}.temp file but with normalized names.

```
sheldon_cooper How are you, Leonard?
leonard_hofstadter Good, and you?
```

All normalized names should appear in the IMDB credits except for few cases:

When a character from the transcript doesn't have an equivalent in IMDB, we name it as *{transcriptName}#unknown#{idEpisode}*.

When several characters speak at the same time, we concatenate normalized names in alphabetical order with "@" as separator like *penny@sheldon_cooper*.

*all@* is used as the "all" tag.

To normalize names, you can use the script normalizeTranscriptsNames.py like that:

```bash
normalizeTranscriptsNames.py TheBigBangTheory
```

You can precise a season with -s option and an episode with -e option.

For a given episode, the script presents normalized names from IMDB for this episode.

Then, the script show the result of the automatic alignment as *{transcriptName} -> {predictedIMDBName}*.

You can then select a {transcriptName} you want to change, and the script asks for the normalized name. If you can't find a matching, just type
*unk* or leave the field blank and the script automatically asigns the right unknown format to the {transcriptName}.

You can finally save the changes and create the appropriate `{idEpisode}.txt` file with *end*.

### `forced-alignment/ folder`

Forced alignment was done using VRBS (closed-source), the rest of the code (e.g. add speaker id to the forced-alignment output) is [available here](https://github.com/PaulLerner/Forced-Alignment).

We save :
- RTTM files for diarization/identification : `<SERIE_URI>_<FORCED_ALIGNMENT_COLLAR>collar.rttm`. We merge tracks with same label and separated by less than `FORCED_ALIGNMENT_COLLAR` seconds, as forced-alignment output is usually over-segmented
- UEM file : `<SERIE_URI>_<VRBS_CONFIDENCE_THRESHOLD>confidence.uem`. Keeps track of the "annotated" parts of the file (i.e. discard the parts were VRBS is not confident)
- train, dev and test lists : `<set>.lst` for reproducible results. If transcripts with speaker name is not available, forced-alignment still provides speech turn segmentation. If the serie has mixed transcripts (some episodes named, and some anonymous) then another list `<set>.SAD.lst` is used for the anonymous episodes.

#### `<file_uri>.aligned`
Inspired by [`stm`](http://www1.icsi.berkeley.edu/Speech/docs/sctk-1.2/infmts.htm#stm_fmt_name_0) the `aligned` format provides additionally the confidence of the model in the transcription :

```
<file_uri> <speaker_id> <start_time> <end_time> <token> <confidence_score>
```
e.g. :

```
TheBigBangTheory.Season01.Episode01 sheldon_cooper 12.0 12.14 both 0.990
TheBigBangTheory.Season01.Episode01 sheldon_cooper 12.14 12.530000000000001 slits 0.990
TheBigBangTheory.Season01.Episode01 sheldon_cooper 12.53 12.53 . 0.950
TheBigBangTheory.Season01.Episode01 leonard_hofstadter 13.1 13.37 Agreed 0.990
TheBigBangTheory.Season01.Episode01 leonard_hofstadter 13.37 13.37 , 0.100
TheBigBangTheory.Season01.Episode01 leonard_hofstadter 14.03 14.25 what's 0.990
```

### `merge_{idEpisode}.csv`
You'll find these in the `annotated_transcripts/` folder of the serie, if available. 
See [#15](https://github.com/PaulLerner/pyannote-db-plumcot/issues/15) for a brief description of temporary formats 
(located in `conll_semi-auto-annotation/`, `csv_doccano/`, `csv_semi-auto-annotation/`).

See also issues [#13](https://github.com/PaulLerner/pyannote-db-plumcot/issues/13) for thoughts about a better annotation 
and [#15](https://github.com/PaulLerner/pyannote-db-plumcot/issues/15) for thoughts about a better [entities.py](./scripts/entities.py) script.

This only describes the current format and annotation process.

#### .csv Format
The file is a semi-colon (`;`)-separated csv with a lot of useless fields. POS, tag, dep, lemma and entity type have been set automatically.

The ground truth fields are "token", "speaker" and "labelDoccano". I recommand using `Plumcot.loader.CsvLoader` to load the file in a `spaCy Doc`
.

#### linguistic rules for semi-automatic annotation

- "you", "ya", "your", "yourself", "yours" processing:
    - If the name of the speaker in the previous sentence = the name of the speaker in the next sentence &rarr; name of the speaker in the next sentence
    - If "you/your/etc." followed by a character name &rarr; that character's standard name
    - If "you/your/etc." is in a query sentence and preceded or followed by "do" or "did" &rarr; standardized name of the speaker of the next sentence,
    - If "you" is followed by "guys" &rarr; "multiple_persons" (see below)
    - Otherwise &rarr; name of the speaker of sentence -1
    - If the name of the speaker of the current sentence is the same as that of previous sentence &rarr; name of the speaker of the next sentence
    - If the name of the speaker of the current sentence is the same as the name of the speaker of the next sentence &rarr; name of the speaker of the next-next sentence.
- "i", "my", "me", "myself", "mine" processing &rarr; name of the speaker of the current sentence.
- "she", "her", "herself" processing &rarr; "UNKNOWN"
- "he", "his", "him", "himself" processing &rarr; "UNKNOWN"
- parents processing:
    Two lists are established: masculine_parents / feminine_parents containing the standardized names of the parents,
    - If the word is in the list ["mommy", "mom", "daddy", "dad", "papa", "mother", "father"], and if the word is preceded by "my", then we look at the surname of the current speaker and that of the father/mother in the masculine_parents and feminine_parents lists, if it matches &rarr; normalized name of the detected father or mother
    - If you don't know the parents and you have "my dad" annotated with the name of the current speaker + "'s_father", e.g "sheldon_cooper's_father"
    - Otherwise if you have "your dad" &rarr; "PARENTS".
- "we", "us", "our" processing &rarr; "multiple_persons".

#### manual annotation (i.e. correction) instructions
See also [#15](https://github.com/PaulLerner/pyannote-db-plumcot/issues/15) for technical instructions

**We only annotate person named-entites, others (e.g. organizations) are not annotated.**

In Doccano, if you come across entities composed of multiple units, you will need to annotate 
entity by entity so that the character identifiers match the tokenization of the .csv files "semi-auto-annot". 
E.g. "Buffy Summers" &rarr;
- "Buffy" &rarr; "buffy_summers"
- "Summers" &rarr; "buffy_summers"

Special entites: "UNKNOWN" and "multiple_persons":
- Names of persons which are not present in the IMDb credits of the serie are annotated as "UNKNOWN" 
- Mentions refering to multiple persons (e.g. "you guys") are annotated as "multiple_persons".

We do not annotate the following pronouns: 
- "them" 
- "they" 
- "You" from "thank you" (unless the turn of phrase means that it needs to be annotated, for example, "I thank you"), 
- "you" from "you're welcome." 
- In GameOfThrones, we can have this form: "the Lannisters", "the Starks", to name the houses. These cases are not annotated.

## images

Usage:
```
images.py [options]
images.py scrap [options]
images.py features [options]
images.py references [options]
images.py visualize [options]


Options:
--uri=<uri> Only process this serie, defaults to process all
```
* `main`: do `scrap`, `features` and `references`
* `scrap`: Get images from IMDB character's page given a list of urls and character's names
   
* `features`: Then extracts features off theses images.
* `references`: Then cluster image features, tag clusters based on image caption
           and compute average embedding for (labelled) cluster to keep as reference
* `visualize`: same as `references` but saves figure with cropped faces

Note that, since the IMDB caption only contains info about the actors, it does a 1-1 mapping between actor and character. Thus it's not functional if one actor plays several character, as the `characters.py` script only extracts the main character that an actor plays.

Images are stored in the `images/` folder, each character gets its own directory, e.g. `images/leonard_hofstadter`.
Thus images are duplicated if there are several characters on the same picture.
Images are enumerated per character, e.g. :
```images/
  images.json
  leonard_hofstadter/
    leonard_hofstadter.0.jpg
    leonard_hofstadter,sheldon_cooper.1.jpg
    leonard_hofstadter.2.jpg
```

In addition, we save a json file under `images.json`. The format follows the one from imdb (that gets scraped by the `get_image_jsons_from_url` function), which, to the best of my knowledge, isn't described anywhere.

Therefore, we'll focus here only on the sub-json `image_jsons['allImages']`. It contains a list of objects which describe an image :
- the `src` field contains the url of the image
- the `altText` field contains the caption used to infer the image label (and not the actual `caption` field as it contains links)
- the `imageType` field which categorizes images in 7 types (that I know of):
  * production_art
  * still_frame
  * product
  * publicity
  * behind_the_scenes
  * poster
  * event

I added :
- the `path` field which contains a list of paths under which the image was saved (e.g. `[Plumcot/data/TheBigBangTheory/images/leonard_hofstadter/leonard_hofstadter,sheldon_cooper.1.jpg, Plumcot/data/TheBigBangTheory/images/sheldon_cooper/leonard_hofstadter,sheldon_cooper.42.jpg]`).
- the `label` field which is a list of all normalized characters detected in the picture (e.g. `[leonard_hofstadter, sheldon_cooper]`)
- the `features` field which, in the same way, contains a list of paths to numpy arrays, described in `pyannote.video`. There should be one feature file per image, located in the same directory, it should be named like `<model_name>.<file_uri>.npy`.

I also added a `characters` object (i.e. python `dict`) in `image_jsons['characters']`. It counts the number of images which was scraped for each character and keeps track of the paths where each individual image was stored. Also keeps track of the features computed for each character : a json object which looks like :
```json
{
  "path":"<model_name>.<file_uri>.npy",
  "model_name":"<model_name>",
  "imageType":"<imageType>"
}
```

## multimodal

Fuses outputs of `pyannote.audio` and `pyannote.video` models

Requires that you first ran speaker diarization as described in [pyannote.audio tutorials](https://github.com/pyannote/pyannote-audio/tree/develop/tutorials/pipelines/speaker_diarization) and face identification using [pyannote.video](https://github.com/PaulLerner/pyannote-video/blob/feat/identify/scripts/pyannote-face.py) (the latter output path should be like `Plumcot/data/<serie_uri>/video/<file_uri>.npy`).

### fuse
`multimodal.py fuse <serie_uri.task.protocol> <validate_dir> [--set=<set>]`

1. computes optimal mapping between speaker diarization output (i.e. speech clusters) and face identification tracks.
2. keep only parts where the character is *speaking* and *visible*

> FIXME this relies on https://github.com/pyannote/pyannote-core/pull/33

### map (i.e. identify)
`multimodal.py map <serie_uri.task.protocol> <validate_dir> [--set=<set> --ier]`

maps speaker diarization output (i.e. speech clusters) and face identification tracks, either by:
- using `pyannote.metrics` optimal mapping like in `fuse` (one-to-one mapping between cluster and face id)
- else, if `--ier`, mapping whatever face id co-occurs the most with the cluster in order to minimize IER
 

## scene / narrative stuff

Aman will come up with a file format and data.

# Experiments

## ASR

```
asr.py run <protocol> <model> <scorer> [--subset=<subset>]
asr.py evaluate <protocol> [--subset=<subset>]
```

This relies on `deepspeech-gpu 0.7.3`:

```
wget https://github.com/mozilla/DeepSpeech/releases/download/v0.7.3/deepspeech-0.7.3-models.pbmm 
wget https://github.com/mozilla/DeepSpeech/releases/download/v0.7.3/deepspeech-0.7.3-models.scorer

# this will write output to Plumcot/data/HarryPotter/experiments/ASR/HarryPotter.Episode01.txt
asr.py run HarryPotter.SpeakerDiarization.0 deepspeech-0.7.3-models.pbmm deepspeech-0.7.3-models.scorer

# this will evaluate the output according to HarryPotter.Episode01 "transcription" (after some post-processing)
# and should print WER and CER in a LaTeX formatted-table 
asr.py evaluate HarryPotter.SpeakerDiarization.0
```

## NER
```
ner.py [--uri=<uri> -v -vv]
```

This relies on `spacy 2.2.4`:

```
python -m spacy download en_core_web_lg

# This will run model over HarryPotter's test set and evaluate it according to the "entity" key
# it will save confusion table to Plumcot/data/HarryPotter/experiments/NER/confusion.csv
# and print out F-score, precision and recall in a LaTeX formatted-table
ner.py --uri=HarryPotter -v
```
## Speaker Diarization and Identification

TODO: add model weights to [pyannote.audio hub](https://github.com/pyannote/pyannote-audio-hub) ?