# PLUMCOT 0

> TODO update with entity linking stuff

![wav-got](./wav-got.png)
![annotation-got](./annotation-got.png)
![grid-got](./grid-got.png)

The PLUMCOT corpus provides annotation for face recognition, speech activity detection, speaker diarization and speaker identification of 16 TV (or movie) series :

| title                    | episodes | duration | episodes | sentences | episodes | duration | episodes | duration |
|--------------------------|----------|----------|----------|-----------|----------|----------|----------|----------|
| 24                       | 195      | 142:45   | \-       | \-        | 195      | 36:17    | \-       | \-       |
| Battlestar Galactica     | 71       | 52:16    | \-       | \-        | 71       | 10:53    | 61       | 08:49    |
| Breaking Bad             | 61       | 47:15    | \-       | \-        | 61       | 17:06    | 61       | 17:06    |
| Buffy The Vampire Slayer | 143      | 101:18   | 12       | 5109      | 143      | 25:55    | 143      | 25:55    |
| ER                       | 283      | 235:29   | \-       | \-        | 283      | 63:06    | \-       | \-       |
| Friends                  | 233      | 84:56    | \-       | \-        | 233      | 28:04    | 233      | 28:04    |
| Game Of Thrones          | 60       | 53:09    | 10       | 3400      | 60       | 19:13    | 60       | 19:13    |
| Harry Potter             | 8        | 18:51    | 1        | 845       | 8        | 02:44    | 4        | 01:28    |
| Homeland                 | 70       | 59:27    | \-       | \-        | 70       | 12:24    | \-       | \-       |
| Lost                     | 66       | 74:36    | 7        | 2104      | 66       | 07:12    | 66       | 07:12    |
| Six Feet Under           | 63       | 56:43    | \-       | \-        | 63       | 15:11    | \-       | \-       |
| Star Wars                | 7        | 15:05    | 1        | 1185      | 7        | 02:13    | 7        | 02:13    |
| The Big Bang Theory      | 207      | 68:41    | 17       | 4159      | 207      | 25:23    | 207      | 25:23    |
| The Lord Of The Rings    | 3        | 08:56    | \-       | \-        | 3        | 00:47    | 3        | 00:47    |
| The Office               | 188      | 71:45    | 6        | 1495      | 188      | 30:15    | 188      | 30:15    |
| The Walking Dead         | 89       | 72:09    | 19       | 5363      | 89       | 08:32    | 25       | 02:46    |
| *TOTAL*                  | 1747     | 1163:29  | \-       | \-        | 1747     | 305:25   | 1058     | 169:19   |


Speaker annotations come from forced-alignment on series transcripts except for Breaking Bad and Game Of Thrones which were manually annotated by Bost et al.

Face recognition annotations consists of a dataset of images labeled with the featured characters, scrapped from [IMDb](https://www.imdb.com/). No bounding box nor video identification annotations are provided (for now).

In addition, this repository provides a Python API to access the corpus programmatically.

## Installation

Until the package has been published on PyPI, one has to run the following commands:

```bash
$ git clone https://github.com/PaulLerner/pyannote-db-plumcot.git
$ pip install pyannote-db-plumcot
```

## Usage

Please refer to [pyannote.database](https://github.com/pyannote/pyannote-database#custom-protocols) for a complete documentation.

```bash
export PYANNOTE_DATABASE_CONFIG=$PWD/pyannote-db-plumcot/Plumcot/data/database.yml
python
```

### Speaker Diarization / Identification and Entity Linking

```python
>>> from pyannote.database import get_protocol

# you can access the whole dataset using the meta-protocol 'X'
>>> plumcot = get_protocol('X.SpeakerDiarization.Plumcot')
# Note : this might take a while...
>>> plumcot.stats('train')
{'annotated': 710303.0550000002, 'annotation': 383730.8849999984, 'n_files': 681, 'labels': {...}}

# or access each serie individually, e.g. 'HarryPotter'
>>> from pyannote.database import get_protocol
>>> harry = get_protocol('HarryPotter.SpeakerDiarization.0')
>>> harry.stats('train')
{'annotated': 5281.429999999969, 'annotation': 2836.8099999998867, 'n_files': 2, 'labels': {...}}
# get the first file of HarryPotter.SpeakerDiarization.0's test set
>>> first_file = next(harry.test()) 
>>> first_file['uri']                                                                                                                                                                                   
'HarryPotter.Episode01'
# top 5 speakers of HarryPotter.Episode01
>>> first_file['annotation'].chart()[:5]                                                                                                                                                                
[('harry_potter', 417.1699999999951),
 ('rubeus_hagrid', 321.49000000000785),
 ('ron_weasley', 259.1599999999926),
 ('hermione_granger', 217.5499999999979),
 ('albus_dumbledore', 186.04999999999941)]
# On some files we provide entity linking annotation in a SpaCy Doc
# Beware, this might lead to a KeyError
>>> entity = first_file['entity'] 
>>> from pyannote.core import Segment 
>>> for token in entity[:11]: 
>>>     segment = Segment(token._.time_start, token._.time_end) 
>>>     print(f'{segment} {token._.speaker}: {token.text} -> {token.ent_kb_id_}')                                                                                                                        
[ 00:01:18.740 -->  00:01:18.790] albus_dumbledore: I -> albus_dumbledore
[ 00:01:18.830 -->  00:01:18.980] albus_dumbledore: should -> 
[ 00:01:18.980 -->  00:01:19.100] albus_dumbledore: have -> 
[ 00:01:19.160 -->  00:01:19.430] albus_dumbledore: known -> 
[ 00:01:19.460 -->  00:01:19.580] albus_dumbledore: that -> 
[ 00:01:19.600 -->  00:01:19.700] albus_dumbledore: you -> professor_mcgonagall
[ 00:01:19.700 -->  00:01:19.820] albus_dumbledore: would -> 
[ 00:01:19.820 -->  00:01:19.940] albus_dumbledore: be -> 
[ 00:01:19.940 -->  00:01:20.380] albus_dumbledore: here -> 
[ 00:01:21.660 -->  00:01:22.130] albus_dumbledore: ...Professor -> 
[ 00:01:22.380 -->  00:01:22.600] albus_dumbledore: mcgonagall -> professor_mcgonagall
```

### Speech Activity Detection and transcription

Note that the previous dataset is also suitable for Speech Activity Detection but is smaller.

```python
>>> from pyannote.database import get_protocol

# you can access the whole dataset using the meta-protocol 'X'
>>> plumcot = get_protocol('X.SpeakerDiarization.SAD')
# Note : this might take a while...
>>> plumcot.stats('train')
{'annotated': 1286065.3450000014, 'annotation': 716507.5149999945, 'n_files': 1144, 'labels': {...}}

# or access each serie individually, e.g. 'HarryPotter'
>>> harry = get_protocol('HarryPotter.SpeakerDiarization.SAD')
>>> harry.stats('train')
{'annotated': 12864.489999999932, 'annotation': 5853.799999999804, 'n_files': 5, 'labels': {...}}
# get the first file of HarryPotter.SpeakerDiarization.0's test set
>>> first_file = next(harry.test()) 
>>> first_file['uri']                                                                                                                                                                                   
'HarryPotter.Episode01'
# The 'transcription' key should *always* be available, even when speaker identity is not
>>> transcription = first_file['transcription']
>>> from pyannote.core import Segment 
>>> for token in transcription[:11]: 
>>>     s = Segment(token._.time_start, token._.time_end) 
>>>     print(f'{s}: {token.text}') 
[ 00:01:18.740 -->  00:01:18.790]: I
[ 00:01:18.830 -->  00:01:18.980]: should
[ 00:01:18.980 -->  00:01:19.100]: have
[ 00:01:19.160 -->  00:01:19.430]: known
[ 00:01:19.460 -->  00:01:19.580]: that
[ 00:01:19.600 -->  00:01:19.700]: you
[ 00:01:19.700 -->  00:01:19.820]: would
[ 00:01:19.820 -->  00:01:19.940]: be
[ 00:01:19.940 -->  00:01:20.380]: here
[ 00:01:21.660 -->  00:01:22.130]: ...Professor
[ 00:01:22.380 -->  00:01:22.600]: mcgonagall
```
> Note: we don't provide for the series audio or video files! You'll need to acquire them yourself then place them in the relevant serie directory (e.g. `HarryPotter/wavs`) with file name formatted as `<file_uri>.en16kHz.wav`. See also [DVD section](#DVDs).

## Raw data

Transcripts, diarization and entities annotation can be found as text file in `Plumcot/data` sub-directory. Formats etc. are described in [`CONTRIBUTING.md`](CONTRIBUTING.md).

The face recognition dataset is provided from an external link : **[TODO](TODO)**. Alternatively, you can scrap the images yourself using [`scripts/images_scraping.py`](./scripts/image_scraping.py) (see [`CONTRIBUTING.md`](CONTRIBUTING.md)).

### DVDs

Episode numbering relies on [IMDb](https://www.imdb.com/).

We acquired zone 2 (i.e. Europe) DVDs. DVDs were converted to mkv and wav using [dvd_extraction](https://github.com/PaulLerner/dvd_extraction).

[`durations.csv`](Plumcot/data/durations.csv) provides the audio duration of the resulting wav files.

Some (double) episodes are numbered as two different episodes in the DVDs although they're numbered as one in IMDb. These are listed in the `double_episodes/` folder of the relevant serie, if needed.

> TODO: automate the creation of `double_episodes/` files so that the user doesn't have to replace `/vol/work3/lefevre/dvd_extracted/` manually.

The episodes are then concatenated using ffmpeg:
```bash
cd pyannote-db-plumcot/
bash scripts/concat_double_episodes.sh <serie_uri> </path/to/wavs>
```

Note that this will only create a new wav file resulting of the concatenation of `<episode.i>` and `<episode.j>` named like `<episode.i.j>` but it will not fix the numbering of the others episodes (TODO: add code to do it ?)

## Ambiguous labels

Some labels are ambiguous depending on whether we focus on the speaker or on the entity.

We decided to focus on the entity as much as possible, e.g. 'Obiwan Kenobi' has the same label in the old and the new Star Wars movies, although it is not the same actor (i.e. speaker).

However, we annotated following the IMDb credits which are not always consistent, e.g. the emperor in Star Wars doesn't have the same label in the old and the new episodes.

> Disclaimer : we do not intend to use the whole `X.SpeakerDiarization.Plumcot` corpus
> to train or evaluate speaker diarization systems! Indeed, the classes are largely
> imbalanced, a lot of actors (i.e. speakers) play in multiple series and a lot of
> characters share labels across series (see [`actor_counter`](Plumcot/data/actor_counter.json) and [`counter
>`](Plumcot/data/counter.json), respectively).

Moreover, some secondary characters (most don't have proper names) are played by several different actors through the same serie. These are listed in [`not_unique.json`](./Plumcot/data/TheOffice/not_unique.json) and should be removed from the evaluation (TODO).

> IMDb credits were updated [on 17/03/2020 in 123e37cb](https://github.com/PaulLerner/pyannote-db-plumcot/commit/123e37cb8b64bb6a9bdd89ed665a2769d992569f), therefore some annotated labels are inconsistent with these new IMDb credits and should be updated (TODO).

## LICENSE

### Source code

The source code (or "Software") if freely available under the [MIT License](./LICENSE)

### Speech annotations

All speech annotations, regarding speaker identity or speech regions are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

### Textual content

All textual content, dialogues and derived annotations are held by their respective owners and their use is allowed under the Fair Use Clause of the Copyright Law.
We only share them for research purposes.

They were scraped from various fan websites:
- https://www.fandom.com/
- http://transcripts.foreverdreaming.org/
- https://www.springfieldspringfield.co.uk/
- http://www.ageofthering.com/
- https://bsg.hypnoweb.net/

## References

Bost, X., Labatut, V., Linares, G., 2020. Serial speakers: a dataset of tv series. arXiv preprint arXiv:2002.06923.
