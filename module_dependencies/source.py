from __future__ import annotations

import ast
import base64
import os
from glob import glob
from typing import Dict, Iterable, List, Union

from module_dependencies.api import SourceI
from module_dependencies.tokenize import detokenize
from module_dependencies.visitor import ParserVisitor


class SourceString(SourceI):
    """Implementation of `SourceI` interface. Reads a string which
    represents Python source code, and parses it for dependencies
    and import statements."""

    def __init__(self, source: str) -> None:
        """Read a string with Python source code.

        Example usage::

            >>> from module_dependencies import Source
            >>> src = Source("from nltk import word_tokenize\nword_tokenize('Hello there!')")
            >>> src.dependencies()
            ['nltk.word_tokenize']
            >>> src.imports()
            ['nltk']

        :param src source: String with Python source code.
        """
        tree = ast.parse(source)
        self.visitor = ParserVisitor(tree)

    def imports(self) -> List[str]:
        return sorted(
            detokenize(importname) for importname in self.visitor.get_imports()
        )

    def dependencies(
        self, module: Union[Iterable[str], str] = None
    ) -> Dict[str, List[str]]:
        return sorted(detokenize(usage) for usage in self.visitor.get_uses(module))


class SourceBase64(SourceString):
    """Reads a base64 encoded string which represents Python source code,
    and parses it for dependencies and import statements."""

    def __init__(self, encoded: str) -> None:
        """Read a string with base64 encoded Python source code.

        Example usage::

            >>> from module_dependencies import Source
            >>> src = Source("ZnJvbSBubHRrIGltcG9ydCB3b3JkX3Rva2VuaXplCndvcmRfdG9rZW5pemUoJ0hlbGxvIHRoZXJlIScp")
            >>> src.dependencies()
            ['nltk.word_tokenize']
            >>> src.imports()
            ['nltk']

        :param src encoded: String with base64 encoded Python source code.
        """
        source = base64.b64decode(encoded).decode("ascii")
        super().__init__(source)


class SourceFile(SourceString):
    """Reads a path to a Python file, and parses it for dependencies
    and import statements."""

    def __init__(self, filename: str) -> None:
        """Read a file path to a Python file.

        Example usage::

            >>> from module_dependencies import Source
            >>> src = Source("my_file.py")
            >>> src.dependencies()
            ['nltk.word_tokenize']
            >>> src.imports()
            ['nltk']

        :param src encoded: String with base64 encoded Python source code.
        """
        with open(filename, encoding="utf8") as file:
            super().__init__(file.read())


class SourceFolder(SourceI):
    """Reads a path to a folder, and parses each Python file for dependencies
    and import statements."""

    def __init__(self, path: str) -> None:
        """Read a path to a folder containing Python file.
        The Python files will be looked for recursively,
        and the folder may contain non-Python files.

        Example usage::

            >>> src = Source("module_dependencies")
            >>> pprint(src.dependencies_mapping("ast"))
            {'module_dependencies/__init__.py': [],
            'module_dependencies/api.py': [],
            'module_dependencies/factory.py': [],
            'module_dependencies/source.py': ['ast.parse'],
            'module_dependencies/tokenize.py': [],
            'module_dependencies/visitor.py': ['ast.AST',
                                               'ast.Attribute',
                                               'ast.Import',
                                               'ast.ImportFrom',
                                               'ast.Name',
                                               'ast.NodeVisitor',
                                               'ast.iter_fields']}

        :param path: [description]
        :type path: str
        """
        self.files = {
            filename: SourceFile(filename)
            for filename in glob(os.path.join(path, "**", "*.py"), recursive=True)
        }

    def imports_mapping(self) -> Dict[str, List[str]]:
        return {filename: source.imports() for filename, source in self.files.items()}

    def imports(self) -> List[str]:
        return sorted(
            {
                importname
                for imports in self.imports_mapping().values()
                for importname in imports
            }
        )

    def dependencies_mapping(
        self, module: Union[Iterable[str], str] = None
    ) -> Dict[str, List[str]]:
        return {
            filename: source.dependencies(module)
            for filename, source in self.files.items()
        }

    def dependencies(self, module: Union[Iterable[str], str] = None) -> List[str]:
        return sorted(
            {
                importname
                for imports in self.dependencies_mapping(module).values()
                for importname in imports
            }
        )
