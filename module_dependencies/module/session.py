import os
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
        self.content_format = r'"^\\s*(import|from) +{module}[\\s\\.,$]"'
        # self.content_format = r'"(import|from) +{module}"'

    def construct_payload(self, module: str) -> Dict:
        query = self.default_query.copy()
        if "." in module:
            query["content"] = module
        else:
            query["content"] = self.content_format.format(module=module)
        query_string = " ".join(f"{key}:{value}" for key, value in query.items())
        payload = self.default_payload.copy()
        payload["variables"] = {"query": query_string}
        return payload

    def post(
        self,
        module: str,
        count: Union[int, str] = None,
        timeout: Union[int, str] = None,
    ) -> requests.Response:
        payload = self.construct_payload(module)
        return super().post(self.url, json=payload)
