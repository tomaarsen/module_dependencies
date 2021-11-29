import glob
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(__file__, "../../.."))

from module_dependencies import Source


def load_input_expected():
    dir = os.path.dirname(__file__)
    path = os.path.join(dir, "input", "*.py")
    for filepath in glob.glob(path):
        filename, _ext = os.path.splitext(os.path.basename(filepath))
        expected_filepath = os.path.join(dir, "expected", filename) + ".json"

        with open(filepath, "r", encoding="utf8") as f:
            source_code = f.read()
        with open(expected_filepath, "r", encoding="utf8") as f:
            expected = json.load(f)
        yield filename, source_code, expected["dependencies"], expected["imports"]


@pytest.mark.parametrize(
    "filename, source_code, dependencies, imports", load_input_expected()
)
def test_source(filename, source_code, dependencies, imports):
    source = Source.from_string(source_code)
    assert (
        source.dependencies("nltk") == dependencies
    ), f'Source("{filename}").dependencies()'
    assert source.imports() == imports, f'Source("{filename}").imports()'
