import json
import logging
import os
import time
from typing import Dict, Tuple, Union, Optional

import requests

from module_dependencies.source import Source

logger = logging.getLogger(__name__)


class ModuleSession(requests.Session):
    def __init__(self, token: Optional[str]=None) -> None:
        """
        :param token: Sourcegraph API token to avoid rate-limiting 429 error
        :type token: str, optional
        """
        super().__init__()

        # The API URL to query
        self.url = "https://sourcegraph.com/.api/graphql"

        # The partial payload with the GraphQL query. Used in ``construct_payload``
        self.default_payload = {"variables": {}}
        with open(
            os.path.join(os.path.dirname(__file__), "query.txt"), "r", encoding="utf8"
        ) as f:
            self.default_payload["query"] = f.read()

        # The default query information, only missing the ``content`` key.
        default_query = {
            "context": "global",
            "count": "25000",
            "timeout": "1m",
            "patterntype": "regexp",
        }

        # Format of the search content, either ``import module`` or ``from module``.
        # Note that this format is only used if ``module`` does not contain any dots.
        # After all, ``nltk.tokenize`` might be imported like ``from nltk import tokenize``,
        # and then this format would not catch this.
        # base_import_format = r'"\\s*(import|from) +{module}[\\s\\.,$]"'
        # self.base_import_format = r'"{module}"'
        subpackage_import_format = r'"{module}[\\s\\.,$]"'  # TODO: Check performance of this vs using base_import_format with left-most module

        self.token = token
        
        # The supported languages to fetch
        self.config = {
            "Python": {
                "dependencies": lambda content, module: Source.from_string(
                    content
                ).dependencies(module),
                "base_import_format": r'"^\\s*(import|from) +{module}[\\s\\.,$]"',
                "subpackage_import_format": subpackage_import_format,
                "default_query": {**default_query, "language": '"Python"'},
            },
            "Jupyter Notebook": {
                "dependencies": lambda content, module: Source.from_jupyter(
                    content
                ).dependencies(module),
                "base_import_format": r'"\"\\s*(import|from) +{module}[\\s\\.,$]"',
                "subpackage_import_format": subpackage_import_format,
                "default_query": {**default_query, "language": '"Jupyter Notebook"'},
            },
        }

    def fetch_and_parse(
        self,
        module: str,
        count: Union[int, str] = "all",
        timeout: Union[int, str] = "10s",
        verbose: bool = True,
        languages: Tuple[str] = None,
    ) -> Dict:
        """Return the parsed data from the SourceGraph API.
        This method loads the data once upon request and then parses it
        using `Source(...).dependencies()`.

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
        :param verbose: If True, display a progress bar for parsing files.
            Defaults to True.
        :type verbose: bool, optional

        :return: The parsed SourceGraph API data.
        :rtype: Dict
        """

        def combine_results(results: Dict, new: Dict) -> None:
            """
            {'alert': None,
            'cloning': [],
            'elapsedMilliseconds': 569,
            'limitHit': True,
            'matchCount': 131,
            'missing': [],
            'repositoriesCount': 49,
            'results': [...],
            'timedout': []}
            """
            if not results:
                return new

            if results["alert"] and new["alert"]:
                results["alert"] = results["alert"] + new["alert"]
            else:
                results["alert"] = results["alert"] or new["alert"]
            results["cloning"] += new["cloning"]
            results["elapsedMilliseconds"] += new["elapsedMilliseconds"]
            results["limitHit"] = results["limitHit"] or new["limitHit"]
            results["matchCount"] += new["matchCount"]
            results["missing"] += new["missing"]
            results["repositoriesCount"] += new["repositoriesCount"]
            results["results"] += new["results"]
            results["timedout"] += new["timedout"]
            return results

        if not languages:
            languages = self.config.keys()

        results = {}
        for language in languages:
            with self as session:
                logger.info(
                    f"Fetching {language} source code containing imports of `{module}`..."
                )
                response = session.post(
                    module, count=count, timeout=timeout, language=language
                )
                response.raise_for_status()
                logger.info(
                    f"Fetched {language} source code containing imports of `{module}` "
                    f"(status code {response.status_code})"
                )
                logger.info(
                    f"Parsing {len(response.content):,} bytes of {language} source code as JSON..."
                )
                data = json.loads(response.content)
                logger.info(
                    f"Parsed {len(response.content):,} bytes of {language} source code as JSON..."
                )
            results = combine_results(
                results,
                self.parse_raw_response(
                    data["data"]["search"]["results"],
                    module=module,
                    language=language,
                    verbose=verbose,
                ),
            )
        return results

    def parse_raw_response(
        self, results: Dict, module: str, language: str, verbose: bool = True
    ):
        """Strip `content` from the raw input data, and replace it with
        `dependencies` and `parse_error`.

        :param results: Raw output from `session.post(self.module, ...)`
        :type results: Dict
        :param module: String of the module we are interested in,
            e.g. "nltk" or "nltk.tokenize".
        :type module: str
        :param language: The name of the language that is being parsed,
            e.g. "Python" or "Jupyter Notebook".
        :type language: str
        :return: Modified output of `results`, with file `content` stripped,
            and `dependencies` and `parse_error` added.
        :rtype: Dict
        """
        logger.info(
            f"Extracting dependencies of {len(results['results']):,} files of {language} source code..."
        )
        if verbose:
            from tqdm import tqdm

            iterator = tqdm(results["results"], desc="Parsing Files", unit="files")
        else:
            iterator = results["results"]
        for result in iterator:
            content = result["file"]["content"]
            del result["file"]["content"]

            error_name = None
            try:
                dependencies = self.config[language]["dependencies"](content, module)
            except (SyntaxError, RecursionError) as e:
                dependencies = []
                error_name = e.__class__.__name__

            result["file"]["dependencies"] = dependencies
            result["file"]["parse_error"] = error_name
        logger.info(
            f"Extracted dependencies of {len(results['results']):,} files of {language} source code."
        )
        return results

    def construct_payload(
        self,
        module: str,
        count: Union[int, str] = "all",
        timeout: Union[int, str] = "10s",
        language: str = "Python",
    ) -> Dict:
        """Construct the payload to send to SourceGraph. The payload is a dictionary
        with "variables" and "query" keys.

        :param module: String of the module we are interested in,
            e.g. "nltk" or "nltk.tokenize".
        :type module: str
        :param count: The maximum number of results. Either an integer,
            a string representing an integer, or "all", defaults to "all".
        :type count: Union[int, str], optional
        :param timeout: Timeout as parsed by the Go time package "ParseDuration" function,
            e.g. "10s", "100ms". If an integer instead, then parsed as number of
            milliseconds. Cannot exceed 1 minute. Defaults to "10s".
        :type timeout: Union[int, str], optional
        :return: Mapping of "variable" and "query" to a dictionary and a string,
            respectively.
        :rtype: Dict

        TODO: Verify that `module` is valid
        """
        query = self.config[language]["default_query"].copy()
        if "." in module:
            query["content"] = self.config[language]["subpackage_import_format"].format(
                module=module
            )
        else:
            query["content"] = self.config[language]["base_import_format"].format(
                module=module
            )

        query["count"] = str(count)

        if isinstance(timeout, int):
            timeout = f"{timeout}ms"
        query["timeout"] = timeout

        # TODO: Perhaps just "site-packages"
        module_head = module.split(".")[0]  # e.g. "nltk" from "nltk.tokenize"
        query["-file"] = f"site-packages/{module_head}/"

        query_string = " ".join(f"{key}:{value}" for key, value in query.items())

        payload = self.default_payload.copy()
        payload["variables"] = {"query": query_string}
        return payload

    def post(
        self,
        module: str,
        count: Union[int, str] = "all",
        timeout: Union[int, str] = "10s",
        language: str = "Python",
    ) -> requests.Response:
        payload = self.construct_payload(
            module, count=count, timeout=timeout, language=language
        )
        if self.token is not None:
            logger.info('Using Sourcegraph API token')
            return super().post(self.url, json=payload, headers={"Authorization": f"token {self.token}"})
        return super().post(self.url, json=payload)
