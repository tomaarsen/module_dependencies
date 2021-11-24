from typing import Dict, Iterable, List, Union


class SourceI:
    """Interface for `Source` classes.
    Provides the following methods:

    - `imports()`
    - `imports_mapping()`
    - `dependencies(module)`
    - `dependencies_mapping(module)`
    """

    def imports_mapping(self) -> Dict[str, List[str]]:
        """Return a mapping from filenames to a list of modules that were imported from in `source`.

        Only defined for `SourceFolder`, i.e. instances returned from `Source.from_folder()`.

        Example usage::

            >>> src = Source("module_dependencies")
            >>> pprint(src.imports_mapping())
            {'module_dependencies/__init__.py': ['module_dependencies.factory',
                                                 'module_dependencies.source'],
            'module_dependencies/api.py': ['typing'],
            'module_dependencies/factory.py': ['module_dependencies.api',
                                               'module_dependencies.source',
                                               'os'],
            'module_dependencies/source.py': ['__future__',
                                              'ast',
                                              'base64',
                                              'glob',
                                              'module_dependencies.api',
                                              'module_dependencies.tokenize',
                                              'module_dependencies.visitor',
                                              'os',
                                              'typing'],
            'module_dependencies/tokenize.py': ['typing'],
            'module_dependencies/visitor.py': ['ast',
                                               'module_dependencies.tokenize',
                                               'typing']}

        :return: Mapping of filenames to `Source.from_file(filename).imports()`.
        :rtype: Dict[str, List[str]]
        """
        raise NotImplementedError

    def imports(self) -> List[str]:
        """Return a list of modules that were imported from in `source`.

        Example usage::

            >>> from module_dependencies import Source
            >>> src = Source("from nltk import word_tokenize\nword_tokenize('Hello there!')")
            >>> src.imports()
            ['nltk']

        :return: List of modules
        :rtype: List[str]
        """
        raise NotImplementedError

    def dependencies_mapping(
        self, module: Union[Iterable[str], str] = None
    ) -> Dict[str, List[str]]:
        """Return a mapping from filenames to a list of variables, functions and classes
        originating from `module` that were used in that file.

        Only defined for `SourceFolder`, i.e. instances returned from `Source.from_folder()`.

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

        :param module: Module string or list of module strings.
            For example: `'nltk'`, `'nltk.parse'` or `['nltk.parse', 'nltk.stem']`.
            If `module` is None, then all uses of imported variables, functions and classes
            are returned. Defaults to None.
        :type module: Union[Iterable[str], str], optional
        :return: Mapping of filenames to `Source.from_file(filename).dependencies(module)`.
        :rtype: Dict[str, List[str]]
        """
        raise NotImplementedError

    def dependencies(self, module: Union[Iterable[str], str] = None) -> List[str]:
        """Return a list of variables, functions and classes originating from `module`.

        Example usage::

            >>> src = Source.from_folder("module_dependencies")
            >>> print(src.dependencies("os"))
            ['os.path.isdir', 'os.path.isfile', 'os.path.join']

        :param module: Module string or list of module strings.
            For example: `'nltk'`, `'nltk.parse'` or `['nltk.parse', 'nltk.stem']`.
            If `module` is None, then all uses of imported variables, functions and classes
            are returned. Defaults to None.
        :type module: Union[Iterable[str], str], optional
        :return: List of dot-separated modules, variables, functions and classes.
        :rtype: List[str]
        """
        raise NotImplementedError

    def __str__(self) -> str:
        return f"<{self.__class__.__name__}>"
