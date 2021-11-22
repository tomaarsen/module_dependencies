import ast
import os
from glob import glob
from typing import Dict, Iterable, List, Union

from module_dependencies.tokenize import detokenize
from module_dependencies.visitor import ParserVisitor


class Source:
    # TODO: Normalize outputs in some way. Perhaps sorting.
    def __init__(self, source: str) -> None:
        tree = ast.parse(source)
        self.visitor = ParserVisitor(tree)

    def imports(self) -> List[str]:
        return sorted(
            detokenize(importname) for importname in self.visitor.get_imports()
        )

    def dependencies(
        self, module: Union[Iterable[str], str] = None
    ) -> Dict[str, List[str]]:
        return sorted(detokenize(usage) for usage in self.visitor.get_uses(module))


class SourceBase64(Source):
    def __init__(self, encoded: str) -> None:
        import base64

        source = base64.b64decode(encoded).decode("ascii")
        super().__init__(source)


class SourceFile(Source):
    def __init__(self, filename: str) -> None:
        with open(filename, encoding="utf8") as file:
            super().__init__(file.read())


class SourceFolder:
    def __init__(self, path: str) -> None:
        self.files = {
            filename: SourceFile(filename)
            for filename in glob(os.path.join(path, "**", "*.py"), recursive=True)
        }

    def imports_mapping(self) -> Dict[str, List[str]]:
        return {filename: source.imports() for filename, source in self.files.items()}

    def imports(self) -> List[str]:
        return sorted(
            {
                importname
                for imports in self.imports_mapping().values()
                for importname in imports
            }
        )

    def dependencies_mapping(
        self, module: Union[Iterable[str], str] = None
    ) -> Dict[str, List[str]]:
        return {
            filename: source.dependencies() for filename, source in self.files.items()
        }

    def dependencies(self, module: Union[Iterable[str], str] = None) -> List[str]:
        return sorted(
            {
                importname
                for imports in self.dependencies_mapping(module).values()
                for importname in imports
            }
        )
