from __future__ import annotations

import ast
import base64
import json
import os
from glob import glob
from typing import Dict, Iterable, List, Union

from module_dependencies.source.api import SourceI
from module_dependencies.source.visitor import ParserVisitor
from module_dependencies.util.tokenize import detokenize


class SourceString(SourceI):
    """Implementation of ``SourceI`` interface. Reads a string which
    represents Python source code, and parses it for dependencies
    and import statements."""

    def __init__(self, source: str) -> None:
        """Read a string with Python source code.

        Example usage::

            >>> from module_dependencies import Source
            >>> src = Source("from nltk import word_tokenize\\nword_tokenize('Hello there!')")
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

        :param src filename: File path to a Python file.
        """
        with open(filename, encoding="utf8") as file:
            super().__init__(file.read())


class SourceJupyterNotebook(SourceString):
    """Reads a string which represents a Jupyter Notebook,
    and parses it for dependencies and import statements."""

    def __init__(self, jupyter_source: str) -> None:
        """Read a Jupyter Notebook.

        .. note::
            Cells that contain un-compilable code (e.g. `print 'hello'` from Python 2)
            will be discarded. Cells that do compile will be kept to gather the dependencies
            and imports from.

        Example usage::

            >>> from module_dependencies import Source
            >>> src = Source.from_jupyter(r'''
            ... {
            ...  "cells": [
            ...   {
            ...    "cell_type": "code",
            ...    "execution_count": null,
            ...    "metadata": {},
            ...    "outputs": [],
            ...    "source": [
            ...     "from nltk import word_tokenize\n",
            ...     "word_tokenize('Hello there!')"
            ...    ]
            ...   }
            ...  ],
            ...  "metadata": {
            ...   "language_info": {
            ...    "name": "python"
            ...   },
            ...   "orig_nbformat": 4
            ...  },
            ...  "nbformat": 4,
            ...  "nbformat_minor": 2
            ... }
            ... ''')
            >>> src.dependencies()
            ['nltk.word_tokenize']
            >>> src.imports()
            ['nltk']

        :param str jupyter_source: A Jupyter Notebook as a string,
            to be parsed with `json.loads`.
        :raises SyntaxError: Raised whenever the string is not
            a Jupyter Notebook with major versions 2, 3 or 4.
        """
        try:
            notebook = json.loads(jupyter_source)
            version = notebook["nbformat"]
        except Exception as e:
            raise SyntaxError from e

        try:
            if version == 4:
                cells = [
                    "".join(
                        line
                        for line in cell["source"]
                        if not line.startswith(("%", "!"))
                    )
                    for cell in notebook["cells"]
                    if cell["cell_type"] == "code"
                    and cell["source"]
                    and not cell["source"][0].startswith(
                        (
                            "%%bash",
                            "%%html",
                            "%%javascript",
                            "%%js",
                            "%%latex",
                            "%%markdown",
                            "%%perl",
                            "%%ruby",
                            "%%script",
                            "%%sh",
                            "%%svg",
                        )
                    )
                ]
            elif version in (2, 3):
                line_sep = "" if version == 3 else "\n"
                cells = [
                    line_sep.join(
                        line
                        for line in cell["input"]
                        if not line.startswith(("%", "!"))
                    )
                    for worksheet in notebook["worksheets"]
                    for cell in worksheet["cells"]
                    if cell["cell_type"] == "code"
                    and cell["input"]
                    and not cell["input"][0].startswith(
                        (
                            "%%bash",
                            "%%html",
                            "%%javascript",
                            "%%js",
                            "%%latex",
                            "%%markdown",
                            "%%perl",
                            "%%ruby",
                            "%%script",
                            "%%sh",
                            "%%svg",
                        )
                    )
                ]
            else:
                raise SyntaxError(f"Unsupported Jupyter Notebook version: {version!r}")

        except (KeyError, IndexError) as e:
            raise SyntaxError from e

        def valid_cell(cell: str) -> bool:
            try:
                ast.parse(cell)
            except:
                return False
            return True

        # Merge cells, ignoring cells that don't compile
        source = "\n".join([cell for cell in cells if valid_cell(cell)])
        # https://ipython.readthedocs.io/en/stable/interactive/magics.html#cell-magics
        # This allows "%%pypy", "%%python", "%%python2", "%%python3" and "%%writefile"
        super().__init__(source)


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

        :param str path: String path to a folder containing Python code.
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
