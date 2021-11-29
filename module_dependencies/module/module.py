import json
from collections import Counter
from functools import cached_property, lru_cache

from module_dependencies.module.session import ModuleSession
from module_dependencies.source import Source
from module_dependencies.util.tokenize import detokenize, tokenize


class Module:
    def __init__(self, module: str) -> None:
        self.module = module

    @cached_property
    def data(self):
        def parse_data(data, module: str):
            for i, result in enumerate(data["data"]["search"]["results"]["results"]):
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
            return data

        with ModuleSession() as session:
            response = session.post(self.module)
            response.raise_for_status()
            data = json.loads(response.content)
        return parse_data(data, self.module)

    @lru_cache(maxsize=1)
    def usage(self):
        # uses
        # frequency
        counter = Counter(
            use
            for i, result in enumerate(
                self.data["data"]["search"]["results"]["results"]
            )
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
        # projects = defaultdict()
        projects = {}
        for result in self.data["data"]["search"]["results"]["results"]:
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
