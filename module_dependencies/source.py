from typing import Dict, Iterable, List, Union
import os
import ast
from glob import glob
from module_dependencies.visitor import ParserVisitor
from module_dependencies.tokenize import detokenize


class Source:
    def __init__(self, path: str) -> None:
        if os.path.isfile(path):
            filenames = [path]
        elif os.path.isdir(path):
            filenames = glob(os.path.join(path, "**", "*.py"), recursive=True)

        self.visitors = self.visit_all_files(filenames)

    def visit_all_files(self, filenames: List[str]):
        return {filename: self.visit_file(filename) for filename in filenames}

    def visit_file(self, filename: str, module: str = None):
        with open(filename, "r", encoding="utf8") as file:
            return self.visit_code(file.read())

    def visit_code(self, code: str):
        tree = ast.parse(code)
        visitor = ParserVisitor(tree)
        return visitor

    def dependencies(self, module: Union[Iterable[str], str] = None) -> List[str]:
        return list({
            use
            for uses in self.dependencies_mapping(module).values()
            for use in uses
        })

    def dependencies_mapping(
        self, module: Union[Iterable[str], str] = None
    ) -> Dict[str, List[str]]:
        return {
            filename: [detokenize(usage) for usage in visitor.get_uses(module)]
            for filename, visitor in self.visitors.items()
        }

    def imports(self) -> List[str]:
        return list({
            importname
            for imports in self.imports_mapping().values()
            for importname in imports
        })

    def imports_mapping(self) -> Dict[str, List[str]]:
        return {
            filename: [detokenize(importname) for importname in visitor.get_imports()]
            for filename, visitor in self.visitors.items()
        }
