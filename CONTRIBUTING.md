# How to contribute

1. Clone the repository.
2. Make changes.
3. Open a pull request.

Make sure all files are UTF8.

Make sure to follow conventions and file formats described in this document.

Open an issue if something is not clear -- we will decide on a solution and update this document accordingly.

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
We assume that we launch all the script from this root directory where README is stored (TODO: update this shouldn't be necessary anymore since we rely on the `__init__` path -> TODO rely on `__init__` path everywhere).

```
characters.py
credits.py
alignment.py
(entities.py)
TheBigBangTheory/
  transcripts.py
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

This file provides the list of characters (gathered from TV.com or IMDB.com). It contains one line per character with the following information: underscore-separated identifier, actor's normalized name, character's full name, actor's full name, IMDB.com character page.

```
leonard_hofstadter,johnny_galecki,Leonard Hofstadter,Johnny Galecki,https://www.imdb.com/title/tt0898266/characters/nm0301959
```

The creation of this file should be automated as much as possible. Ideally, a script would take `series.txt` as input and generate all `characters.txt` file at once (or just one if an optional series identifier is provided)
`-v fileName` creates a file with `characters.txt` to easily verify the characters normalization.

```bash
characters.py series.txt TheBigBangTheory -v normVerif.txt
```

### `episodes.txt`

This file provides the list of episodes (gathered from TV.com or IMDB.com). It contains one line per episode with the following information: unique episode identifier, name of the episode, IMDB.com episode page, TV.com episode page.

```
TheBigBangTheory.Season01.Episode01,Pilot,https://www.imdb.com/title/tt0775431/,http://www.tv.com/shows/the-big-bang-theory/pilot-939386/
```

The creation of this file should be automated as much as possible. Ideally, a script would take `series.txt` as input and generate all `episodes.txt` file at once (or just one if an optional series identifier is provided)

```bash
episodes.py series.txt TheBigBangTheory
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
episodes.py series.txt TheBigBangTheory -c
```

#### The friends case

TODO: find out a way to automate this or instead split the wav in two and describe it in README

One episode double episode in Friends, was, unlike usual (see README), split in half in IMDb and merged as one in the DVDs. Thus the credits were manually corrected in [this commit](https://github.com/PaulLerner/pyannote-db-plumcot/commit/b9a8ea8188f2e381a3c39e36705629b378db6285) to match the DVDs.

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
- train, dev and test lists : `<set>.lst` for reproducible results.

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

### `entities.txt`

This file contains named entities annotation of `alignment.stm`.

The proposed file format is the following:

```
word_id file_id channel_id speaker_id start_time end_time <> word named_entity_type normalized_name coreference_id
```

```
1 TheBigBangTheory.Season01.Episode01 1 sheldon_cooper start_time end_time <> How     <>     <>                  <>
2 TheBigBangTheory.Season01.Episode01 1 sheldon_cooper start_time end_time <> are     <>     <>                  <>
3 TheBigBangTheory.Season01.Episode01 1 sheldon_cooper start_time end_time <> you     <>     <>                  5/6
4 TheBigBangTheory.Season01.Episode01 1 sheldon_cooper start_time end_time <> ,       <>     <>                  <>
5 TheBigBangTheory.Season01.Episode01 1 sheldon_cooper start_time end_time <> Leonard PERSON leonard_hofstadter  <>
6 TheBigBangTheory.Season01.Episode01 1 sheldon_cooper start_time end_time <> Hofstadter PERSON leonard_hofstadter  <>
7 TheBigBangTheory.Season01.Episode01 1 sheldon_cooper start_time end_time <> ?       <>     <>                  <>
```

```
1 TheBigBangTheory.Season01.Episode01 1 sheldon_cooper start_time end_time <> How     <>     <>                  <>
2 TheBigBangTheory.Season01.Episode01 1 sheldon_cooper start_time end_time <> are     <>     <>                  <>
3 TheBigBangTheory.Season01.Episode01 1 sheldon_cooper start_time end_time <> you     <>     <>                  5/7
4 TheBigBangTheory.Season01.Episode01 1 sheldon_cooper start_time end_time <> ,       <>     <>                  <>
5 TheBigBangTheory.Season01.Episode01 1 sheldon_cooper start_time end_time <> Sheldon PERSON sheldon_cooper  <>
6 TheBigBangTheory.Season01.Episode01 1 sheldon_cooper start_time end_time <> and <> <>  <>
7 TheBigBangTheory.Season01.Episode01 1 sheldon_cooper start_time end_time <> Leonard PERSON leonard_hofstadter  <>
8 TheBigBangTheory.Season01.Episode01 1 sheldon_cooper start_time end_time <> ?       <>     <>                  <>
```

Note: Leo has a script to do that, though the (automatic) output will need a manual correction pass.

## images

The script is `images.py`. It scraps all images of a given serie and infers the label from the IMDB caption. Note that, since the IMDB caption only contains info about the characters, it does a 1-1 mapping between actor and character. Thus it's not functional if one actor plays several character, as the `characters.py` script which only extracts the main character that an actor plays.

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


## scene / narrative stuff

Aman will come up with a file format and data.
