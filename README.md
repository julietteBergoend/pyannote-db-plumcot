# PLUMCOT corpus (not ready for prime time)

This repository provides a Python API to access the PLUMCOT corpus programmatically.

## Installation

Until the package has been published on PyPI, one has to run the following commands:

```bash
$ git clone https://github.com/PaulLerner/pyannote-db-plumcot.git
$ pip install pyannote-db-plumcot
```

## Usage

See [pyannote.database](https://github.com/pyannote/pyannote-database#custom-protocols)

```bash
#TODO implement relative path in pyannote.database
#until then, launch stuff from pyannote-db-plumcot/Plumcot/data/
cd pyannote-db-plumcot/Plumcot/data/
export PYANNOTE_DATABASE_CONFIG=pyannote-db-plumcot/Plumcot/data/database.yml
python
```

```python
from pyannote.database import get_protocol
buffy = get_protocol('BuffyTheVampireSlayer.SpeakerDiarization.0')
print(buffy.stats('train'))
```

Note: we don't provide for the series audio or video files! You'll need to acquire them yourself then set the path to the wav files in `pyannote-db-plumcot/Plumcot/data/database.yml` ('Databases' field).


See also `CONTRIBUTING.md` for technical details.

## Raw data

Transcripts, diarization and entities annotation can be found as text file in `Plumcot/data` sub-directory.

The IMDb images dataset is provided from an external link : **[TODO](TODO)**. Alternatively, you can scrap the images yourself using `scripts/images_scraping.py` (see `CONTRIBUTING.md`).

### DVDs

Episode numbering relies on [IMDb](https://www.imdb.com/).

We acquired zone 2 (i.e. Europe) DVDs. DVDs were converted to mkv and wav using [dvd_extraction](https://github.com/PaulLerner/dvd_extraction).

`durations.csv` provides the audio duration of the resulting wav files.

Some (double) episodes are numbered as two different episodes in the DVDs although they're numbered as one in IMDb. These are listed in the `double_episodes/` folder of the relevant serie, if needed.

TODO: automate the creation of `double_episodes/` files so that the user doesn't have to replace `/vol/work3/lefevre/dvd_extracted/` manually.

The episodes are then concatenated using ffmpeg:
```bash
cd pyannote-db-plumcot/
bash scripts/concat_double_episodes.sh <serie_uri> </path/to/wavs>
```

Note that this will only create a new wav file resulting of the concatenation of `<episode.i>` and `<episode.j>` named like `<episode.i.j>` but it will not fix the numbering of the others episodes (TODO: add code to do it ?)
