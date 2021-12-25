import json
from collections import Counter
from functools import cached_property, lru_cache
from typing import Dict, Union

from tqdm import tqdm

from module_dependencies.module.session import ModuleSession
from module_dependencies.source import Source
from module_dependencies.util.tokenize import detokenize, tokenize


class Module:
    def __init__(
        self,
        module: str,
        count: Union[int, str] = "all",
        timeout: Union[int, str] = "10s",
    ) -> None:
        self.module = module
        self.count = count
        self.timeout = timeout

    @cached_property
    def data(self):
        """
        {
            "data": {
                "search": {
                    {'alert': None,
                    'cloning': [], # Repositories that are busy cloning onto gitserver. In paginated search requests, some repositories may be cloning. These are reported here and you may choose to retry the paginated request with the same cursor after they have cloned OR you may simply continue making further paginated requests and choose to skip
                    'elapsedMilliseconds': 963,
                    'limitHit': False, # Are there more matches that we did not encounter?
                    'matchCount': 25757,
                    'missing': [], # Repositories or commits that do not exist. In paginated search requests, some repositories may be missing (e.g. if Sourcegraph is aware of them but is temporarily unable to serve them). These are reported here and you may choose to retry the paginated request with the same cursor and they may no longer be missing OR you
                    'results': [...],
                    'timedout': []} # Repositories or commits which we did not manage to search in time. Trying again usually will work. In paginated search requests, this field is not relevant.
                }
            }
        }
        TODO: Export repository and file count
        TODO: Alert users of `alert`, output `limitHit`
        """
        with ModuleSession() as session:
            response = session.post(self.module, count=self.count, timeout=self.timeout)
            response.raise_for_status()
            # print(response.elapsed.total_seconds())
            # t = time.time()
            data = json.loads(response.content)
            # print(time.time() - t)
        # pprint(data["data"]["search"]["results"], depth=1)
        return Module._parse_raw_response(
            data["data"]["search"]["results"], self.module
        )

    @staticmethod
    def _parse_raw_response(results: Dict, module: str):
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
        for result in tqdm(results["results"], desc="Parsing Files", unit="file"):
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
        return results

    @lru_cache(maxsize=1)
    def usage(self):
        # uses
        # frequency
        counter = Counter(
            use
            for i, result in enumerate(self.data["results"])
            for use in result["file"]["dependencies"]
        )
        return counter.most_common()

    def nested_usage(self, full_name=True):
        # nested_uses
        # nested_frequency
        # Maybe use NLTK Tree objects?
        """
        output = defaultdict()
        usages = self.usage()
        for variable, occurrence in usages:
            var_tup = tokenize(variable)
            # for i in range(1, len(var_tup) + 1):
                # partial_var_tup = var_tup[:i]
                # partial_var = detokenize(partial_var_tup)
            for var in var_tup:
                output[partial_var]["occurrences"] += occurrence
        """
        pass

    @lru_cache(maxsize=1)
    def projects(self):
        """
        {
            "github.com/Ciphey/Ciphey": {
                "description": "\u26a1 Automatically decrypt encryptions without knowing the key or cipher, decode encodings, and crack hashes \u26a1",
                "stars": 8078,
                "isFork": false,
                "files": [
                    {
                        "name": "enciphey.py",
                        "path": "tests/enciphey.py",
                        "url": "/github.com/Ciphey/Ciphey/-/blob/tests/enciphey.py",
                        "dependencies": [
                            "nltk.tokenize.sent_tokenize",
                            "nltk.tokenize.treebank.TreebankWordDetokenizer"
                        ],
                        "parse_error": null
                    },
                    ...
                ]
            },
            ...
        }
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

    def n_files(self):
        pass

    def n_projects(self):
        pass
