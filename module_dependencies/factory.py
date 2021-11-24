import os

from module_dependencies.api import SourceI

from module_dependencies.source import (  # isort:skip
    SourceBase64,
    SourceFile,
    SourceFolder,
    SourceString,
)


class Source(SourceI):
    """Factory class for instances of the ``SourceI`` interface.
    The specific subclass of ``SourceI`` is chosen based on the
    contents of the ``source`` input parameter.

    Example usage::

        >>> from module_dependencies import Source
        >>> src = Source(r"from nltk import word_tokenize\\nword_tokenize('Hello there!')")
        >>> src
        <module_dependencies.source.SourceString object at 0x...>
        >>> src = Source("my_file.py")
        >>> src
        <module_dependencies.source.SourceFile object at 0x...>
        >>> src = Source("data/real/models")
        >>> src
        <module_dependencies.source.SourceFolder object at 0x...>
        >>> src = Source("ZnJvbSBubHRrIGltcG9ydCB3b3JkX3Rva2VuaXplCndvcmRfdG9rZW5pemUoJ0hlbGxvIHRoZXJlIScp")
        >>> src
        <module_dependencies.source.SourceBase64 object at 0x...>

    The class methods ``Source.from_...`` can also be used to initialize
    specific subclasses of the ``SourceI`` interface.
    """

    def __new__(cls, source: str) -> None:
        if os.path.isfile(source):
            return cls.from_file(source)
        elif os.path.isdir(source):
            return cls.from_folder(source)
        try:
            return cls.from_base64(source)
        except UnicodeDecodeError as e:
            try:
                return cls.from_string(source)
            except SyntaxError as e:
                raise Exception("Input parameter `source` was invalid.") from e

    @classmethod
    def from_string(cls, source: str) -> SourceString:
        return SourceString(source)

    @classmethod
    def from_base64(cls, encoded: str) -> SourceBase64:
        return SourceBase64(encoded)

    @classmethod
    def from_file(cls, filename: str) -> SourceFile:
        return SourceFile(filename)

    @classmethod
    def from_folder(cls, path: str) -> SourceFolder:
        return SourceFolder(path)
