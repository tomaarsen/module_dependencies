"""
Expected usage of module_dependencies::

    >>> from module_dependencies import Source
    >>> src = Source.from_folder("my_folder")
    >>> src.dependencies("ast")
    ['ast.AST', 'ast.Attribute', 'ast.Import', 'ast.ImportFrom', 'ast.Name', 'ast.NodeVisitor', 'ast.iter_fields', 'ast.parse']

Now we know which objects from the "ast" module are used in all code from ``"my_folder"``.

How to initialize a Source instance:

    >>> src = Source.from_string(...)
    >>> src = Source.from_base64(...)
    >>> src = Source.from_file(...)
    >>> src = Source.from_folder(...)

Alternatively, the following can be used, and module_dependencies will try to
understand what input is used (e.g. whether an encoded string, a source code string,
a filename, a folder name)

    >>> src = Source(...)

The following methods are always defined:

    >>> src.dependencies(module)
    >>> src.imports()

If the input was a folder, then the following methods are also defined:

    >>> src.dependencies_mapping(module)
    >>> src.imports_mapping()
"""

from module_dependencies.source.factory import Source

from module_dependencies.source.source import (  # isort:skip
    SourceBase64,
    SourceFile,
    SourceFolder,
    SourceString,
)

__all__ = [
    "Source",
    "SourceFile",
    "SourceBase64",
    "SourceFolder",
    "SourceString",
]
