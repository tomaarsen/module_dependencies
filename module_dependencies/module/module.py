import json
import logging
from collections import Counter, defaultdict
from functools import cached_property, lru_cache
from typing import Any, Dict, List, Tuple, Union

from tqdm import tqdm

from module_dependencies.module.session import ModuleSession
from module_dependencies.source import Source
from module_dependencies.util.tokenize import detokenize, tokenize

logger = logging.getLogger(__name__)


class Module:
    def __init__(
        self,
        module: str,
        count: Union[int, str] = "all",
        timeout: Union[int, str] = "10s",
        verbose: bool = True,
        lazy: bool = True,
    ) -> None:
        """Create a Module instance that can be used to find
        which sections of a Python module are most frequently used.

        This class exposes the following methods::

            usage()
            nested_usage()
            repositories
            n_uses()
            n_files()
            n_repositories()

        TODO: Export repository and file count
        TODO: Alert users of `alert`, output `limitHit`

        :param module: The name of a Python module of which to find
            the frequently used objects, e.g. `"nltk"`.
        :type module: str
        :param count: The maximum number of times an import of `module`
            should be fetched. Roughly equivalent to the number of fetched
            files. Either an integer, a string representing an integer,
            or "all", defaults to "all".
        :type count: Union[int, str], optional
        :param timeout: Timeout for the source code API. Does not correspond
            to the timeout for any of the functions as a whole. The timeout
            can be an integer or a string with some digits and then a time
            unit, e.g. "10s", "100ms". If an integer instead, then parsed as
            number of milliseconds. Cannot exceed 1 minute. Defaults to "10s".
        :type timeout: Union[int, str], optional
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
        self.timeout = timeout
        self.verbose = verbose

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

        def parse_raw_response(results: Dict, module: str):
            """Strip `content` from the raw input data, and replace it with
            `dependencies` and `parse_error`.

            :param results: Raw output from `session.post(self.module, ...)`
            :type results: Dict
            :param module: String of the module we are interested in,
                e.g. "nltk" or "nltk.tokenize".
            :type module: str
            :return: Modified output of `results`, with file `content` stripped,
                and `dependencies` and `parse_error` added.
            :rtype: Dict
            """
            logger.info(
                f"Extracting dependencies of {len(results['results']):,} files of source code..."
            )
            if self.verbose:
                iterator = tqdm(results["results"], desc="Parsing Files", unit="file")
            else:
                iterator = results["results"]
            for result in iterator:
                content = result["file"]["content"]
                del result["file"]["content"]
                error_name = None
                try:
                    dependencies = Source.from_string(content).dependencies(module)
                except (SyntaxError, RecursionError) as e:
                    dependencies = []
                    error_name = e.__class__.__name__
                result["file"]["dependencies"] = dependencies
                result["file"]["parse_error"] = error_name
            logger.info(
                f"Extracted dependencies of {len(results['results']):,} files of source code."
            )
            return results

        with ModuleSession() as session:
            logger.info(
                f"Fetching source code containing imports of `{self.module}`..."
            )
            response = session.post(self.module, count=self.count, timeout=self.timeout)
            response.raise_for_status()
            logger.info(
                f"Fetched source code containing imports of `{self.module}` "
                f"(status code {response.status_code})"
            )
            logger.info(
                f"Parsing {len(response.content):,} bytes of source code as JSON..."
            )
            data = json.loads(response.content)
            logger.info(
                f"Parsed {len(response.content):,} bytes of source code as JSON..."
            )
        return parse_raw_response(data["data"]["search"]["results"], self.module)

    @lru_cache(maxsize=1)
    def usage(self) -> List[Tuple[str, int]]:
        """Get a list of object-occurrence tuples, sorted by most to least frequent.

        Example usage::

            >>> from module_dependencies import Module
            >>> module = Module("nltk", count="3")
            >>> module.usage()
            [('nltk.metrics.distance.edit_distance', 2),
            ('nltk.tokenize.sent_tokenize', 1),
            ('nltk.tokenize.treebank.TreebankWordDetokenizer', 1)]

        :return: A list of object-occurrence tuples, sorted by most to least frequent.
        :rtype: List[Tuple[str, int]]
        """
        # uses
        # frequency

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
                return False
            return i == len(var_one)

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
                options = [
                    (o_key, o_occ)
                    for o_key, o_occ in merged.items()
                    if is_subsection_of(obj, o_key)
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

        counter = Counter(
            use
            for result in self.data["results"]
            for use in result["file"]["dependencies"]
        )
        return merge_all(counter.most_common())

    @lru_cache(maxsize=1)
    def nested_usage(self) -> Dict[str, Union[Dict, int]]:
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

        TODO: Consider adding support for a `full_name` parameter

        :return: A dictionary mapping objects to how often that object occurred
            in the parsed source code.
        :rtype: Dict[str, Union[Dict, int]]
        """
        # nested_uses
        # nested_frequency
        def recursive_add(nested, obj_tup: List[str], occurrence):
            if not obj_tup:
                return
            head = obj_tup[0]
            if head not in nested:
                nested[head] = {"occurrences": occurrence}
            else:
                nested[head]["occurrences"] += occurrence
            recursive_add(nested[head], obj_tup[1:], occurrence)

        nested = {}
        for obj, occurrence in self.usage():
            obj_tup = tokenize(obj)
            recursive_add(nested, obj_tup, occurrence)
        return nested

    @lru_cache(maxsize=1)
    def repositories(self) -> Dict[str, Dict[str, Any]]:
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
        projects = {}
        for result in self.data["results"]:
            name = result["repository"]["name"]
            del result["repository"]["name"]
            if name in projects:
                projects[name]["files"].append(result["file"])
            else:
                projects[name] = {**result["repository"], "files": [result["file"]]}
        return projects

    def n_uses(self) -> int:
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
        return sum(occ for _, occ in self.usage())

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

        :return: The number of fetched repositories in which `self.module`
            was imported.
        :rtype: int
        """
        return self.data["repositoriesCount"]
