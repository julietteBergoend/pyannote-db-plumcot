# PLUMCOT corpus (not ready for prime time)

This repository provides a Python API to access the PLUMCOT corpus programmatically.

## Installation

Until the package has been published on PyPI, one has to run the following commands:

```bash
$ git clone https://github.com/hbredin/pyannote-db-plumcot.git
$ pip install pyannote-db-plumcot
```

## API

```python
>>> from pyannote.database import get_protocol
>>> buffy = get_protocol('Plumcot.Collection.BuffyTheVampireSlayer')
>>> for episode in buffy.files():
...     print(episode)
```

## Raw data
>>>>>>> 150c0df7e7192c3ac2dd09a742ef58edbb3efb11

If needs be, one can also find the raw data as text file in `Plumcot/data` sub-directory.
