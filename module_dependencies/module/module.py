import logging
import warnings
from collections import Counter, defaultdict
from functools import lru_cache

try:
    from functools import cached_property
except ImportError:
    cached_property = lambda f: property(lru_cache()(f))
from typing import Any, Dict, List, Tuple, Union

from module_dependencies.module.session import ModuleSession
from module_dependencies.util.tokenize import detokenize, tokenize

logger = logging.getLogger(__name__)


class Module:
    def __init__(
        self,
        module: str,
        count: Union[int, str] = "25000",
        verbose: bool = True,
        lazy: bool = True,
        python: bool = True,
        jupyter: bool = True,
    ) -> None:
        """Create a Module instance that can be used to find
        which sections of a Python module are most frequently used.

        This class exposes the following methods::

            usage()
            nested_usage()
            repositories()
            plot()
            n_uses()
            n_files()
            n_repositories()

        ..
            TODO: Alert users of `alert`, output `limitHit`
            TODO: Something with percentages?
            TODO: Info on just one object, e.g.
            >>> module.use("nltk.tokenize")
            "802 occurrences out of 83530 (0.96%)"
            TODO: Biggest repositories relying on some subsection.
                Perhaps an extension to `repositories()`?
                Add this to n_uses, n_files and n_repositories, too

        :param module: The name of a Python module of which to find
            the frequently used objects, e.g. `"nltk"`.
        :type module: str
        :param count: The maximum number of times an import of `module`
            should be fetched. Roughly equivalent to the number of fetched
            files. Either an integer, a string representing an integer,
            or "all", defaults to "25000".
        :type count: Union[int, str], optional
        :param verbose: If True, set the logging level to INFO, otherwise to
            WARNING. True implies that there is some data printed to sys.out,
            while False makes the class quiet. Defaults to True.
        :type verbose: bool, optional
        :param lazy: If True, waits with fetching and parsing the data to when
            the data is required. Defaults to True.
        :type lazy: bool, optional
        """
        self.module = module
        self.count = count
        self.timeout = "10s"
        self.verbose = verbose

        languages = []
        if python:
            languages.append("Python")
        if jupyter:
            languages.append("Jupyter Notebook")
        self.languages = tuple(languages)

        if verbose:
            logger.setLevel(logging.INFO)
        else:
            logger.setLevel(logging.WARNING)

        if not lazy:
            self.data

    @cached_property
    def data(self) -> Dict:
        """Cached property of a Module, containing the parsed data from
        the SourceGraph API. This property lazily loads the data once upon request,
        and then parses it using `Source(...).dependencies()`.

        Example usage::

            >>> from module_dependencies import Module
            >>> module = Module("nltk", count=3)
            >>> pprint(module.data, depth=1)
            {
                'alert': None,
                'cloning': [],
                'elapsedMilliseconds': 573,
                'limitHit': True,
                'matchCount': 3,
                'missing': [],
                'repositoriesCount': 1,
                'results': [...],
                'timedout': []
            }

        :return: The cached, parsed SourceGraph API data.
        :rtype: Dict
        """
        return ModuleSession().fetch_and_parse(
            self.module, self.count, self.timeout, self.verbose, self.languages
        )

    @staticmethod
    def is_subsection_of(var_one: Tuple[str], var_two: Tuple[str]) -> bool:
        """Check whether `var_one` is a subsection of `var_two`. This means
        that `var_two` can be created by inserting strings into the tuple of
        `var_one`. For example, `var_two` as `('nltk', 'tokenize', 'word_tokenize')`
        can be created by inserting `'tokenize'` into a `var_one` as
        `('nltk', 'word_tokenize')`, so this function returns True.

        :param var_one: Tuple of strings representing the path to a Python
            object, e.g. `('nltk', 'word_tokenize')`.
        :type var_one: Tuple[str]
        :param var_two: Tuple of strings representing the path to a Python
            object, e.g. `('nltk', 'tokenize', 'word_tokenize')`.
        :type var_two: Tuple[str]
        :return: True if `var_one` is a subsection of `var_two`.
        :rtype: bool
        """
        try:
            i = 0
            for section in var_two:
                if section == var_one[i]:
                    i += 1
        except IndexError:
            # e.g. with ('nltk', 'corpus', 'words') and ('nltk', 'corpus', 'words', 'words'),
            # TODO: False isnt really appropriate. This algorithm simply doesn't
            # work well with repeat words.
            return True
        return i == len(var_one)

    @lru_cache(maxsize=1)
    def usage(
        self, merge: bool = True, cumulative: bool = False
    ) -> List[Tuple[str, int]]:
        """Get a list of object-occurrence tuples, sorted by most to least frequent.

        Example usage::

            >>> from module_dependencies import Module
            >>> module = Module("nltk", count="3")
            >>> module.usage()
            [('nltk.metrics.distance.edit_distance', 2),
            ('nltk.tokenize.sent_tokenize', 1),
            ('nltk.tokenize.treebank.TreebankWordDetokenizer', 1)]

        :param merge: Whether to attempt to merge e.g. `"nltk.word_tokenize"`
            into `"nltk.tokenize.word_tokenize"`. May give incorrect results
            for projects with "compat" folders, as the merging tends to prefer
            longer paths, e.g. `"tensorflow.float32"` will become
            `"tensorflow.compat.v1.dtypes.float32"` as opposed to just
            `"tensorflow.dtypes.float32"`. Defaults to True.
        :type merge: bool
        :return: A list of object-occurrence tuples, sorted by most to least frequent.
        :rtype: List[Tuple[str, int]]
        """
        # uses
        # frequency

        def merge_one(usage: List[Tuple[Tuple[str], int]]) -> List[Tuple[str, int]]:
            """Merge a list of similar tuples, combining on "paths" that likely
            refer to the same object, e.g. `"nltk.word_tokenize"` and
            `"nltk.tokenize.word_tokenize"`. `usage` is a list of potentially
            combinable objects.

            :param usage: A list of tuples, where the first element is a tuple
                of strings that represent a path to a Python object, e.g.
                `('nltk', 'word_tokenize')`, and the second element is how
                often that Python object occurs in a large collection of code.
                Each path in the tuple ends in the same token, and thus could
                refer to the same object.
            :type usage: List[Tuple[Tuple[str], int]]
            :return: `usage`, but the first element of each tuple is detokenized,
                i.e. converted back to a string, and paths that refer to the
                same element are merged.
            :rtype: List[Tuple[str, int]]
            """
            merged = {}
            # Sort `usage` on longest to shortest paths
            for obj, occ in sorted(usage, key=lambda x: len(x[0]), reverse=True):
                # Get the list of object/occurrence tuples that `obj` can expand to become
                # Note that in order to expand to something, it must have occurred more than once
                options = [
                    (o_key, o_occ)
                    for o_key, o_occ in merged.items()
                    if Module.is_subsection_of(obj, o_key) and o_occ > 1
                ]
                if options:
                    # Get the most likely expansion, e.g.
                    # "nltk.load" can expand to "nltk.data.load"
                    # and "nltk.parse.dependencygraph.DependencyGraph.load"
                    # Then, we pick the one with the highest occurrence,
                    # which is likely "nltk.data.load"
                    key = max(options, key=lambda x: x[1])[0]
                    merged[key] += occ
                else:
                    merged[obj] = occ
            return [(detokenize(obj), occ) for obj, occ in merged.items()]

        def merge_all(usage: List[Tuple[str, int]]) -> List[Tuple[str, int]]:
            """Merge a list of tuples, combining on "paths" that likely
            refer to the same object, e.g. `"nltk.word_tokenize"` and
            `"nltk.tokenize.word_tokenize"`.

            :param usage: A list of tuples, where the first element of
                each tuple is a string representing a path to a Python object,
                e.g. `"nltk.word_tokenize"`, and the second element of each
                tuple is the occurrence of that object in a large collection
                of code.
            :type usage: List[Tuple[str, int]]
            :return: `usage`, but with some merged tuples.
            :rtype: List[Tuple[str, int]]
            """
            # Group usage data together, based on the last token in each object path
            # Merging can only occur within these groups.
            grouped = defaultdict(list)
            for obj, occ in usage:
                obj_tok = tokenize(obj)
                grouped[obj_tok[-1]].append((obj_tok, occ))

            # Attempt to merge within a group
            merged = []
            for group in grouped.values():
                merged.extend(merge_one(group))
            # Sort the usage data from most to least occurring
            return sorted(merged, key=lambda x: x[1], reverse=True)

        def cumulate(usage: List[Tuple[str, int]]) -> List[Tuple[str, int]]:
            usage = defaultdict(lambda: 0, {tokenize(obj): occ for obj, occ in usage})
            for tok_obj, occ in usage.copy().items():
                for i in range(1, len(tok_obj)):
                    usage[tok_obj[:i]] += occ
            usage = [(detokenize(tok_obj), occ) for tok_obj, occ in usage.items()]
            return sorted(usage, key=lambda x: x[1], reverse=True)

        counter = Counter(
            use
            for result in self.data["results"]
            for use in result["file"]["dependencies"]
        )
        usage = counter.most_common()
        if merge:
            usage = merge_all(usage)
        if cumulative:
            usage = cumulate(usage)
        return usage

    @lru_cache(maxsize=1)
    def nested_usage(
        self, full_name: bool = False, merge: bool = True, cumulative: bool = True
    ) -> Dict[str, Union[Dict, int]]:
        """Get a (recursive) dictionary of objects mapped to occurrence of that object,
        and the object's children.

        Example usage::

            >>> from module_dependencies import Module
            >>> module = Module("nltk", count="3")
            >>> module.nested_usage()
            {
                "nltk": {
                    "occurrences": 4,
                    "corpus": {
                        "occurrences": 2,
                        "stopwords": {
                            "occurrences": 2,
                            "words": {
                                "occurrences": 2
                            }
                        }
                    },
                    "tokenize": {
                        "occurrences": 2,
                        "sent_tokenize": {
                            "occurrences": 1
                        },
                        "treebank": {
                            "occurrences": 1,
                            "TreebankWordDetokenizer": {
                                "occurrences": 1
                            }
                        }
                    }
                }
            }

        TODO: Optimize this by relying on usage() better for cumulative

        :param full_name: Whether each dictionary key should be the full path,
            e.g. `"nltk.tokenize"`, rather than just the right-most section.
            Defaults to False.
        :type full_name: bool
        :param merge: Whether to attempt to merge e.g. `"nltk.word_tokenize"`
            into `"nltk.tokenize.word_tokenize"`. May give incorrect results
            for projects with "compat" folders, as the merging tends to prefer
            longer paths, e.g. `"tensorflow.float32"` will become
            `"tensorflow.compat.v1.dtypes.float32"` as opposed to just
            `"tensorflow.dtypes.float32"`. Defaults to True.
        :type merge: bool
        :param cumulative: Whether to include usage counts of e.g.
            `"nltk.tokenize.word_tokenize"` into `"nltk.tokenize"` and
            `"nltk"` as well. Defaults to True.
        :param cumulative: bool
        :return: A dictionary mapping objects to how often that object occurred
            in the parsed source code.
        :rtype: Dict[str, Union[Dict, int]]
        """
        # nested_uses
        # nested_frequency
        def recursive_add(
            nested: Dict, obj_tup: List[str], occurrence: int, prefix: str = ""
        ):
            if not obj_tup:
                return
            head = obj_tup[0]
            if full_name and prefix:
                head = prefix + "." + head
            if head not in nested:
                nested[head] = {
                    "occurrences": occurrence if cumulative or len(obj_tup) == 1 else 0
                }
            else:
                if cumulative or len(obj_tup) == 1:
                    nested[head]["occurrences"] += occurrence
            recursive_add(nested[head], obj_tup[1:], occurrence, prefix=head)

        nested = {}
        for obj, occurrence in self.usage(merge=merge):
            obj_tup = tokenize(obj)
            recursive_add(nested, obj_tup, occurrence)
        return nested

    @lru_cache(maxsize=1)
    def repositories(self, obj: str = "") -> Dict[str, Dict[str, Any]]:
        """Return a mapping of repository names to repository information
        that were fetched and parsed. Contains "description", "stars", "isFork" keys,
        plus a list of "files" with "name", "path", "url", "dependencies" and
        "parse_error" fields. The "parse_error" field lists the error that was
        encountered when attempting to parse the file, e.g. "SyntaxError".
        This might happen when a Python 2 file was fetched.

        Example usage::

            >>> from module_dependencies import Module
            >>> module = Module("nltk", count="3")
            >>> module.repositories()
            {
                "github.com/codelucas/newspaper": {
                    "description": "News, full-text, and article metadata extraction in Python 3. Advanced docs:",
                    "stars": 11224,
                    "isFork": false,
                    "files": [
                        {
                            "name": "download_corpora.py",
                            "path": "download_corpora.py",
                            "url": "/github.com/codelucas/newspaper/-/blob/download_corpora.py",
                            "dependencies": [
                                "nltk.download"
                            ],
                            "parse_error": null
                        },
                        {
                            "name": "nlp.py",
                            "path": "newspaper/nlp.py",
                            "url": "/github.com/codelucas/newspaper/-/blob/newspaper/nlp.py",
                            "dependencies": [
                                "nltk.data.load"
                            ],
                            "parse_error": null
                        },
                        {
                            "name": "text.py",
                            "path": "newspaper/text.py",
                            "url": "/github.com/codelucas/newspaper/-/blob/newspaper/text.py",
                            "dependencies": [
                                "nltk.stem.isri.ISRIStemmer",
                                "nltk.tokenize.wordpunct_tokenize"
                            ],
                            "parse_error": null
                        }
                    ]
                }
            }

        :return: A mapping of repositories
        :rtype: Dict[str, Dict[str, Any]]
        """
        if obj:
            tok_obj = tokenize(obj)
            objects = {
                potential_obj
                for potential_obj, _ in self.usage(merge=False, cumulative=True)
                if Module.is_subsection_of(tok_obj, tokenize(potential_obj))
            }
            if not objects:
                warnings.warn(
                    f"No instance of {obj!r} was found in the fetched files!",
                    stacklevel=2,
                )

        projects = {}
        for result in self.data["results"]:
            # Add this result if we want all results,
            # or if this result contains dependencies that match `obj`
            if not obj or set(result["file"]["dependencies"]).intersection(objects):
                name = result["repository"]["name"]
                del result["repository"]["name"]
                if name in projects:
                    projects[name]["files"].append(result["file"])
                else:
                    projects[name] = {**result["repository"], "files": [result["file"]]}
        return dict(
            sorted(
                projects.items(), key=lambda project: project[1]["stars"], reverse=True
            )
        )

    def plot(
        self,
        merge: bool = True,
        threshold: int = 0,
        limit: int = -1,
        max_depth: int = 4,
        transparant: bool = False,
        show: bool = True,
    ) -> None:
        """Display a plotly Sunburst plot showing the frequency of use
        of different sections of this module.

        :param merge: Whether to attempt to merge e.g. `"nltk.word_tokenize"`
            into `"nltk.tokenize.word_tokenize"`. May give incorrect results
            for projects with "compat" folders, as the merging tends to prefer
            longer paths, e.g. `"tensorflow.float32"` will become
            `"tensorflow.compat.v1.dtypes.float32"` as opposed to just
            `"tensorflow.dtypes.float32"`. Defaults to True.
        :type merge: bool
        :rtype: None
        """
        import plotly.graph_objects as go

        def get_value(nested_dict: Dict, tok_obj: Tuple[str]) -> int:
            """Recursively apply elements from `tok_obj` as keys in `nested_dict`,
            and then gather the `occurrences`.

            :param nested_dict: A dictionary with nested usages, generally taken
                from the `nested_usage` method.
            :type nested_dict: Dict
            :param tok_obj: A tuple of strings representing a path to a Python path.
            :type tok_obj: Tuple[str]
            :return: The occurrence of the object represented by `tok_obj`
                in `nested_dict`.
            :rtype: int
            """
            if not tok_obj:
                return nested_dict["occurrences"]
            return get_value(nested_dict[tok_obj[0]], tok_obj[1:])

        usage = self.usage(merge=merge)
        nested_usage = self.nested_usage(merge=merge)

        objects = set()
        for obj, _ in usage:
            tok_obj = tokenize(obj)
            objects |= {
                (detokenize(tok_obj[:i]), tok_obj[:i])
                for i in range(1, len(tok_obj) + 1)
            }

        full_objects = [
            {"obj": obj, "tok": tok_obj, "val": get_value(nested_usage, tok_obj)}
            for obj, tok_obj in objects
        ]
        if threshold:
            full_objects = [fobj for fobj in full_objects if fobj["val"] > threshold]
        if limit > 0:
            sorted_fobjs = sorted(
                full_objects, key=lambda fobj: fobj["val"], reverse=True
            )
            limit_value = sorted_fobjs[limit]["val"]
            full_objects = [fobj for fobj in full_objects if fobj["val"] >= limit_value]

        parameters = {
            "ids": [fobj["obj"] for fobj in full_objects],
            "labels": [fobj["tok"][-1] for fobj in full_objects],
            "parents": [detokenize(fobj["tok"][:-1]) for fobj in full_objects],
            "values": [fobj["val"] for fobj in full_objects],
        }

        if show:
            fig = go.Figure(
                go.Sunburst(
                    **parameters,
                    branchvalues="total",
                    insidetextorientation="radial",
                    maxdepth=max_depth,
                ),
                layout=go.Layout(
                    paper_bgcolor="rgba(0,0,0,0)" if transparant else None,
                    margin={"t": 0, "l": 0, "r": 0, "b": 0},
                ),
            )
            fig.show()
        else:
            return parameters

    def n_uses(self, obj: str = "") -> int:
        """Return the number of uses of the module.

        Example usage::

            >>> from module_dependencies import Module
            >>> module = Module("nltk", count="100")
            >>> module.n_uses()
            137

        :return: The number of uses, i.e. the number of times
            `self.module` was used in the fetched files.
        :rtype: int
        """
        if obj:
            tok_obj = tokenize(obj)
            objects = {
                potential_obj
                for potential_obj, _ in self.usage(merge=False, cumulative=True)
                if Module.is_subsection_of(tok_obj, tokenize(potential_obj))
            }
            # print(objects)
            usages = defaultdict(lambda: 0, self.usage(merge=False, cumulative=False))
            # print([usages[potential_obj] for potential_obj in objects])
            return sum(usages[potential_obj] for potential_obj in objects)
        return sum(occ for _, occ in self.usage(merge=False, cumulative=False))

    def n_files(self) -> int:
        """Return the number of files fetched.

        Example usage::

            >>> from module_dependencies import Module
            >>> module = Module("nltk", count="100")
            >>> module.n_files()
            100

        :return: The number of fetched files in which `self.module` was
            imported. Generally equivalent or similar to `count` if it
            was provided.
        :rtype: int
        """
        return len(self.data["results"])

    def n_repositories(self) -> int:
        """Return the number of repositories fetched.

        Example usage::

            >>> from module_dependencies import Module
            >>> module = Module("nltk", count="100")
            >>> module.n_repositories()
            52

        TODO: Exclude errorred code

        :return: The number of fetched repositories in which `self.module`
            was imported.
        :rtype: int
        """
        return self.data["repositoriesCount"]
