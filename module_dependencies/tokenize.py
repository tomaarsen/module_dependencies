
from typing import Tuple

Variable = Tuple[str, ...]

def tokenize(tokens: str) -> Variable:
    """Convert e.g. `"nltk.tokenize"` into `('nltk', 'tokenize')`.

    :param str tokens: Dot-separated tokens in a string.
    :return Variable: Tuple of tokens.
    """
    return tuple(tokens.split("."))

def detokenize(variable: Variable) -> str:
    """Convert e.g. `('nltk', 'tokenize')` into `"nltk.tokenize"`.

    :param Variable variable: Tuple of tokens.
    :return Variable: Dot-separated tokens in a string.
    """
    return ".".join(variable)