from pyannote.database import ProtocolFile
from pathlib import Path
from warnings import warn

from spacy.gold import align
from spacy.vocab import Vocab
from spacy.tokens import Doc, Token

# add custom attributes to Token if they have not already been registered
# (e.g. in pyannote.database.loader)
for attribute, default in [("speaker", "unavailable"),
                           ("time_start", None),
                           ("time_end", None),
                           ("confidence", None)]:
    if not Token.has_extension(attribute):
        Token.set_extension(attribute, default=default)


class BaseLoader:
    """Base class for pyannote.db.plumcot loaders"""

    def __init__(self, path: Path):
        self.path = path

    def __call__(self, current_file: ProtocolFile) -> Doc:
        msg = (f'subclasses of {self.__class__.__name__} should implement their own '
               f'__call__ method, loading {self.path} in a '
               f'{Doc.__name__} ')
        raise NotImplementedError(msg)


class AlignedLoader(BaseLoader):
    """Loads forced-alignment (i.e. timestamped transcripts) in the .aligned format
    described in pyannote.db.plumcot in a spaCy Doc
    """

    def __call__(self, current_file: ProtocolFile) -> Doc:

        with open(self.path) as file:
            current_transcription = file.read().split('\n')

        tokens, attributes = [], []
        for line in current_transcription:
            if line == '':
                continue
            _, speaker, start, end, text, confidence = line.split()
            start, end, confidence = map(float, (start, end, confidence))
            tokens.append(text)
            attributes.append((speaker, start, end, confidence))

        current_transcription = Doc(Vocab(), tokens)
        for token, (speaker, time_start, time_end, confidence) in zip(
                current_transcription, attributes):
            token._.speaker, token._.time_start, token._.time_end, token._.confidence = speaker, time_start, time_end, confidence

        return current_transcription


class TxtLoader(BaseLoader):
    """Loads transcripts in the .txt format described in pyannote.db.plumcot
    in a spaCy Doc
    """

    def __call__(self, current_file: ProtocolFile) -> Doc:

        with open(self.path) as file:
            current_transcription = file.read().split('\n')

        tokens, speakers = [], []
        for line in current_transcription:
            # line should not be empty
            if line == '':
                continue
            line = line.split()
            # there should be at least one speaker and one token per line
            if len(line) < 2:
                continue
            speaker = line[0]
            for token in line[1:]:
                speakers.append(speaker)
                tokens.append(token)

        current_transcription = Doc(Vocab(), tokens)
        for token, speaker in zip(current_transcription, speakers):
            token._.speaker = speaker

        return current_transcription


class CsvLoader(BaseLoader):
    """Loads named entities annotations in the .csv format
    described in pyannote.db.plumcot in a spaCy Doc

    Since we assume that we only annotate person-named entities, the entity type is always
    set to "PERSON" when entity label is not empty and to "" otherwise.

    Also merges named entities annotations with forced-alignment when available
    (see AlignedLoader). Note that some attributes may be lost in the process as the
    output will follow the tokenization of forced-alignment.
    Do not set the "transcription" key in database.yml if you want to avoid that.
    """

    def __call__(self, current_file: ProtocolFile) -> Doc:

        with open(self.path) as file:
            current_entities = file.read().split('\n')

        tokens, attributes = [], []
        for line in current_entities[1:]:
            if line == '':
                continue
            # HACK: using ';' as csv delimiter was a bad idea :)
            if len(line.split(';')) == 16:
                _, _, token, _, pos_, tag_, dep_, _, lemma_, speaker, ent_type_, _, _, _, _, ent_kb_id_ = line.split(
                    ';')
            elif len(line.split(';')) == 18:
                _, _, token, _, _, pos_, tag_, dep_, _, lemma_, _, speaker, ent_type_, _, _, _, _, ent_kb_id_ = line.split(
                    ';')
                token, lemma_ = ';', ';'
            else:
                msg = (
                    f'The following line of {self.path} has an incorrect number of fields '
                    f'(expected 16, got {len(line.split(";"))}):\n{line}')
                raise ValueError(msg)
            # remove empty lines
            if token == '':
                continue
            # first token of each line includes speaker names
            token = token[token.find(' ') + 1:]
            tokens.append(token)

            # HACK: we only annotated person-named entities
            # but ent_type was set automatically, so we always set it to 'PERSON'
            # when the entity was labeled
            if ent_kb_id_ != '':
                ent_type_ = 'PERSON'
            # and reset it to '' otherwise
            else:
                ent_type_ = ''
            attributes.append((pos_, tag_, dep_, lemma_, ent_type_, ent_kb_id_, speaker))

        # if forced-alignment annotation is available in current_file
        # then add named-entities attributes to current_transcription
        current_transcription = current_file.get('transcription')
        if current_transcription:
            return merge_transcriptions_entities(current_transcription,
                                                 tokens,
                                                 attributes)
        # else return named-entities without forced-alignment annotation
        current_transcription = Doc(Vocab(), tokens)
        for token, (pos_, tag_, dep_, lemma_, ent_type_, ent_kb_id_, speaker) in zip(
                current_transcription, attributes):
            token.pos_, token.tag_, token.dep_, token.lemma_, token.ent_type_, token.ent_kb_id_, token._.speaker = \
                pos_, tag_, dep_, lemma_, ent_type_, ent_kb_id_, speaker

        return current_transcription


def merge_transcriptions_entities(current_transcription, e_tokens, e_attributes):
    """Add named-entities attributes to current_transcription

    Parameters
    ----------
    current_transcription: Doc,
        loaded in AlignedLoader, contains timestamps and alignment-confidence
    e_tokens: list
        list of (weirdly tokenized) tokens, loaded in CsvLoader
    e_attributes: list
        aligned list with `e_tokens`
        Contains named-entities attributes, e.g. entity identifier, entity type

    Returns
    -------
    current_transcription: Doc
        same as input `current_transcription` with extra attributes
    """

    tokens = [token.text for token in current_transcription]

    # 1. align weirdly tokenized e_tokens with current_transcription
    _, one2one, _, _, one2multi = align(tokens, e_tokens)

    # 2. add named-entity to perfectly mapped tokens
    # and try to map with surrounding tokens for the unmatched as spacy.gold.align
    # doesn't handle insertions
    previous = 0
    for i, j in enumerate(one2one):
        if j < 0:
            # HACK if not matched then should be previous+1
            # Note: if at some point spacy.gold.align handles insertions their implementation
            # will probably be better than this ;)
            pos_, tag_, dep_, lemma_, ent_type_, ent_kb_id_, _ = e_attributes[
                previous + 1]
            current_transcription[i].pos_, current_transcription[i].tag_, \
            current_transcription[i].dep_, \
            current_transcription[i].lemma_, current_transcription[i].ent_type_, \
            current_transcription[i].ent_kb_id_ = \
                pos_, tag_, dep_, lemma_, ent_type_, ent_kb_id_
            continue
        previous = j
        pos_, tag_, dep_, lemma_, ent_type_, ent_kb_id_, _ = e_attributes[j]
        current_transcription[i].pos_, current_transcription[i].tag_, \
        current_transcription[i].dep_, \
        current_transcription[i].lemma_, current_transcription[i].ent_type_, \
        current_transcription[i].ent_kb_id_ = \
            pos_, tag_, dep_, lemma_, ent_type_, ent_kb_id_

    return current_transcription
