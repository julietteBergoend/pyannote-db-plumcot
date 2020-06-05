from pyannote.database import ProtocolFile
from pathlib import Path

from spacy.vocab import Vocab
from spacy.tokens import Doc, Token

# add custom attributes to Token
Token.set_extension("speaker", default='unavailable')
Token.set_extension("time_start", default=None)
Token.set_extension("time_end", default=None)
Token.set_extension("alignment_confidence", default=0.0)

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
        for token, (speaker, time_start, time_end, alignment_confidence) in zip(current_transcription, attributes):
            token._.speaker, token._.time_start, token._.time_end, token._.alignment_confidence = speaker, time_start, time_end, alignment_confidence

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

    Also merges named entities annotations with forced-alignment when available
    (see AlignedLoader)
    """

    def __call__(self, current_file: ProtocolFile) -> Doc:

        with open(self.path) as file:
            current_entities = file.read().split('\n')

        tokens, attributes = [], []
        for line in current_entities[1:]:
            if line == '':
                continue
            _, _, token, _, pos_, tag_, dep_, _, lemma_, speaker, ent_type_, _, _, _, _, ent_kb_id_ = line.split(';')
            # remove empty lines
            if token == '':
                continue
            # first token of each line includes speaker names
            token = token[token.find(' ') + 1:]
            tokens.append(token)
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
        for token, (pos_, tag_, dep_, lemma_, ent_type_, ent_kb_id_, speaker) in zip(current_transcription, attributes):
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
    i = 0
    for t_token in current_transcription:
        token = e_tokens[i]
        pos_, tag_, dep_, lemma_, ent_type_, ent_kb_id_, _ = e_attributes[i]

        # handle tokenization
        skip_text = False
        while token != t_token.text and i + 1 < len(e_tokens):
            # handle weird '"' corner-case
            if '"' in token:
                break
            # handle punctuation
            elif token == '.':
                i += 1
                token = e_tokens[i]
                pos_, tag_, dep_, lemma_, ent_type_, ent_kb_id_, _ = e_attributes[i]
            elif token.replace('.','') == t_token.text.replace('.',''):
                break
            elif t_token.text == '.':
                skip_text = True
                break
            # token was split by a tokenizer at some point
            else:
                token += e_tokens[i + 1]
                i += 1
        if skip_text:
            continue
        i += 1

        t_token.pos_, t_token.tag_, t_token.dep_, t_token.lemma_, t_token.ent_type_, t_token.ent_kb_id_ = \
            pos_, tag_, dep_, lemma_, ent_type_, ent_kb_id_

    return current_transcription