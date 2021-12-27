import os
import time
from typing import Dict, Union

import requests


class ModuleSession(requests.Session):
    def __init__(self) -> None:
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
        self.default_query = {
            "context": "global",
            "language": "Python",
            "count": "all",
            "timeout": "1m",
            "patterntype": "regexp",
        }

        # Format of the search content, either ``import module`` or ``from module``.
        # Note that this format is only used if ``module`` does not contain any dots.
        # After all, ``nltk.tokenize`` might be imported like ``from nltk import tokenize``,
        # and then this format would not catch this.
        self.base_import_format = r'"^\\s*(import|from) +{module}[\\s\\.,$]"'
        # self.base_import_format = r'"{module}"'
        self.subpackage_import_format = r'"{module}[\\s\\.,$]"'  # TODO: Check performance of this vs using base_import_format with left-most module

    def construct_payload(
        self,
        module: str,
        count: Union[int, str] = "all",
        timeout: Union[int, str] = "10s",
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
        query = self.default_query.copy()
        if "." in module:
            query["content"] = self.subpackage_import_format.format(module=module)
        else:
            query["content"] = self.base_import_format.format(module=module)

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
    ) -> requests.Response:
        payload = self.construct_payload(module, count=count, timeout=timeout)
        return super().post(self.url, json=payload)
