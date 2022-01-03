# Source code inspired by Dockerizeme: https://github.com/dockerizeme/dockerizeme

import ast
from typing import Iterable, Iterator, Set, Tuple, Union

from module_dependencies.util.tokenize import tokenize

Variable = Tuple[str, ...]


class ParentedNodeVisitor(ast.NodeVisitor):
    """Subclass of NodeVisitor which adds the ``parent`` attribute
    to every node traversed via ``generic_visit``. This attribute
    points to the parent node in the AST."""

    def __init__(self) -> None:
        super().__init__()
        # Track the depth of recursion
        self.depth = 0

    def generic_visit(self, node: ast.AST):
        """Called if no explicit visitor function exists for a node.
        Places ``parent`` attribute on the child node.

        :param ast.AST node: Node in an AST.
        """
        self.depth += 1

        if self.depth > 800:
            # At a depth of 1000, this will cause a program crash on Windows.
            raise RecursionError

        try:
            for _field, value in ast.iter_fields(node):
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, ast.AST):
                            item.parent = node
                            self.visit(item)
                else:
                    if isinstance(value, ast.AST):
                        value.parent = node
                        self.visit(value)
        finally:
            self.depth = 0


class ParserVisitor(ParentedNodeVisitor):
    """An AST NodeVisitor for determining usage of a module."""

    def __init__(self, tree: ast.AST):
        """
        Initialize a ParserVisitor responsible for determining usage of
        the ``module`` module in an AST.

        :param str module: The name of the module to determine the usage of, e.g.
            ``"nltk"`` or ``"nltk.tokenize"``, optional.
            If None, then the usage of all imported modules is gathered.
        :var Set[Variable] import_names:
            Set of names of imported objects, e.g.::

            {('product',), ('chain',), ('groupby',), ('np',), ('word_tokenize',)}

            when the file used to create the AST contains::

                from itertools import chain, groupby, product
                from nltk.tokenize import word_tokenize
                import numpy as np
        :var Set[Variable] import_modules:
            Set of names of modules from which objects are imported, e.g.::

            {('itertools',), ('nltk', 'tokenize'), ('numpy',)}

            when the file used to create the AST contains::

                from itertools import chain, groupby, product
                from nltk.tokenize import word_tokenize
                import numpy as np
        :var Dict[Variable, Variable] prefixes:
            Dictionary as mapping from imported object to imported module, e.g.::

            {('chain',): ('itertools',), ('groupby',): ('itertools',), ('product',): ('itertools',), ('word_tokenize',): ('nltk', 'tokenize')}

            when the file used to create the AST contains::

                from itertools import chain, groupby, product
                from nltk.tokenize import word_tokenize
                import numpy as np
        :var Dict[Variable, Variable] aliases:
            Dictionary as mapping from module alias to original module name, e.g.::

            {('np',): ('numpy',)}

            when the file used to create the AST contains::

                from itertools import chain, groupby, product
                from nltk.tokenize import word_tokenize
                import numpy as np
        :var Set[Variable] uses:
            Set of objects from ``module`` used in an AST.

        TODO: Some kind of warning when ``from nltk import *`` is used
        TODO: Tests for ``from .mongo import db`` and ``from .. import mongo``
        TODO: value[0] = ...
        TODO: value["hello"] = ...
        TODO: a, b = ...
        TODO: What if a user does:
        import module
        ...
        module = ...
        Solution: Maybe add to ``self.uses`` sometimes?
        This might happen in practice with:
        ```
        def ...():
            from nltk.corpus import words
            ...

        def ...():
            words = ...
            words.split()
        ```
        Solution: Maybe add and then remove when we leave the recursion
        Maybe clear everything when leaving a ClassDef or FuncDef
        Solution: Map all variables to types, which are appropriately scoped
        """
        super().__init__()
        self.import_names: Set[Variable] = set()
        self.import_modules = set()
        self.prefixes = {}
        self.aliases = {}
        self.uses = set()

        self.visit(tree)

    def propagate_attributes(self, node: ast.AST) -> Variable:
        """Recursively propagate upwards through the AST starting from ``node``,
        gathering the full name of the variable. This method is meant to be called
        from the parent of an ``ast.Name`` node, which helps produce e.g.
        ``('nltk', 'tokenize', 'PunktSentenceTokenizer')`` when the ``ast.Name`` only
        contained ``'PunktSentenceTokenizer'``.

        :param ast.AST node: The node where we start propogating upwards.
        :return Variable: The names of the tokens that occur before ``node``,
            if any.
        """
        if isinstance(node, ast.Attribute):
            return (node.attr,) + self.propagate_attributes(node.parent)
        return ()

    def visit_Import(self, node: ast.Import):
        """Called when encountering an Import node, e.g.::

            import numpy as np

        In this example, ``('numpy',)`` is added to ``self.import_modules``,
        ``('np',)`` is added to ``self.import_names``, and the mapping of
        ``('numpy',)`` to ``('np',)`` is added to ``self.aliases``.

        :param ast.Import node: The node with the import information.
        """
        for name_obj in node.names:
            name = tokenize(name_obj.name)
            self.import_modules.add(name)

            if name_obj.asname is not None:
                alias = tokenize(name_obj.asname)
                self.aliases[alias] = name
                self.import_names.add(alias)
            else:
                self.import_names.add(name)

        # Call generic visit to visit all child nodes
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Called when encountering an ImportFrom node, e.g.::

            from nltk.corpus import wordnet as wn

        In this example, ``('nltk', 'corpus')`` is added to ``self.import_modules``,
        ('wn',) is added to ``self.import_names``, the mapping of ``('wn',)``
        to ``('wordnet',)`` is added to ``self.aliases``, and the mapping of
        ``('wordnet',)`` to ``('nltk', 'corpus')`` is added to ``self.prefixes``.

        :param ast.ImportFrom node: The node with the import-from information.
        """
        module = ("",) * node.level
        if node.module:
            module += tokenize(node.module)

        self.import_modules.add(module)

        for name_obj in node.names:
            name = tokenize(name_obj.name)
            self.prefixes[name] = module

            if name_obj.asname is not None:
                alias = tokenize(name_obj.asname)
                self.aliases[alias] = name
                self.import_names.add(alias)
            else:
                self.import_names.add(name)

        # Call generic visit to visit all child nodes
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        """Called when encountering a Name node, which exists whenever
        a variable is used in some capacity. This Name node consists
        only of the most left-most part of a variable, e.g. ``'nltk'``
        when the variable was ``nltk.tokenize.TweetTokenizer``.

        This method extracts the full Variable, e.g.
        ``('nltk', 'tokenize', 'TweetTokenizer')``. It uses ``self.aliases``
        and ``self.prefixes`` from ``visit_Import`` and ``visit_ImportFrom`` to
        deal with aliases (e.g. ``('np',)`` to ``('numpy',)``) and extending
        prefixes, e.g. ``('word_tokenize',)`` to
        ``('nltk', 'tokenize', 'word_tokenize')``.

        :param ast.Name node: The Name node representing the use of a
            variable in an AST.
        """
        # TODO: There's potential here to add variables
        # TODO: There's options for faster pruning here too.
        head_token = (node.id,)
        variable = head_token + self.propagate_attributes(node.parent)
        # e.g. for fixing ``import numpy as np``
        # TODO: Check whether there is a need for having these keys be tuples
        # TODO: Can this be multiple tokens? e.g. ``import numpy as num.py``?
        if variable[:1] in self.aliases:
            variable = self.aliases[variable[:1]] + variable[1:]

        # e.g. for fixing ``from nltk import word_tokenize``
        # TODO: Check whether there is a need for having these keys be tuples
        # TODO: Can this be multiple tokens? e.g. ``from nltk import tokenize.TweetTokenizer``?
        if variable[:1] in self.prefixes:
            variable = self.prefixes[variable[:1]] + variable

        self.uses.add(variable)

        self.generic_visit(node)

    def get_imports(self) -> Set[Variable]:
        """Return the set of names of modules from which objects are imported, e.g.::

            {('itertools',), ('nltk', 'tokenize'), ('numpy',)}

            when the file used to create the AST contains::

                from itertools import chain, groupby, product
                from nltk.tokenize import word_tokenize
                import numpy as np

        :return: Set of names of modules from which objects are imported.
        :rtype: Set[Variable]
        """
        return self.import_modules

    def get_uses(self, modules: Union[Iterable[str], str] = None) -> Iterator[Variable]:
        """Generate the reported uses of objects imported from modules in ``modules``.
        If ``modules`` is None, then all uses of objects that were imported are yielded.

        For example::

            >>> tree = ast.parse("from nltk.tokenize import word_tokenize\nword_tokenize('Hello there!')")
            >>> visitor = ParserVisitor(tree)
            >>> list(visitor.get_uses("nltk"))
            [('nltk', 'tokenize', 'word_tokenize')]

        :param module: Module string or list of module strings.
            For example: ``'nltk'``, ``'nltk.parse'`` or ``['nltk.parse', 'nltk.stem']``.
            If ``module`` is None, then all uses of imported variables, functions and classes
            are returned. Defaults to None.
        :type module: Union[Iterable[str], str], optional
        :yield: A tuple of tokens representing the use of an imported object.
        :rtype: Iterator[Variable]
        """
        if modules is None:
            modules = self.import_modules
        else:
            if isinstance(modules, str):
                modules = [modules]
            modules = [tokenize(module) for module in modules]
            modules = [
                module
                for module in modules
                if any(
                    module == variable[: len(module)]
                    for variable in self.import_modules
                )
            ]

        for variable in self.uses:
            for module in modules:
                if variable[: len(module)] == module:
                    yield variable
                    break
