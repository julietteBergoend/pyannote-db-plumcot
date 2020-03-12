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
export PYANNOTE_DATABASE_CONFIG=pyannote-db-plumcot/Plumcot/data/database.yml
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
