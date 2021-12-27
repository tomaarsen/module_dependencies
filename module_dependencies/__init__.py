import logging
import os

logging.basicConfig(
    level=os.environ.get("LOGLEVEL", logging.INFO),
    format="[%(asctime)s] [%(name)-12s] [%(levelname)-8s] - %(message)s",
)

from module_dependencies.source import (  # isort:skip
    Source,
    SourceBase64,
    SourceFile,
    SourceFolder,
    SourceString,
)
from module_dependencies.module import Module

__all__ = [
    "Module",
    "Source",
    "SourceFile",
    "SourceBase64",
    "SourceFolder",
    "SourceString",
]
