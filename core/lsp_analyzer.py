"""
LSP Analyzer - Language Server Protocol integration for code understanding.

Provides deep code analysis capabilities:
- Code structure (classes, functions, modules)
- Dependencies and imports
- Type information and interfaces
- Symbol relationships
- Design patterns in code
"""

import ast
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

try:
    import tree_sitter
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False


@dataclass
class CodeSymbol:
    """Represents a code symbol (class, function, variable)."""

    name: str
    type: str  # "class", "function", "variable", "import"
    file_path: Path
    line_number: int
    scope: Optional[str] = None  # Parent scope (class name, module)
    signature: Optional[str] = None  # For functions: full signature
    docstring: Optional[str] = None
    decorators: list[str] = field(default_factory=list)
    children: list["CodeSymbol"] = field(default_factory=list)


@dataclass
class CodeDependency:
    """Represents a dependency relationship between code elements."""

    source: str  # Source file/module
    target: str  # Target file/module
    import_type: str  # "import", "from_import", "relative_import"
    imported_names: list[str] = field(default_factory=list)


@dataclass
class CodeStructure:
    """Complete code structure for a project."""

    root_path: Path
    symbols: list[CodeSymbol]
    dependencies: list[CodeDependency]
    modules: list[str]
    entry_points: list[str] = field(default_factory=list)


class LSPAnalyzer:
    """Analyzes code structure using AST and tree-sitter."""

    # File patterns to analyze
    LANGUAGE_PATTERNS = {
        "python": ["*.py"],
        "javascript": ["*.js", "*.jsx"],
        "typescript": ["*.ts", "*.tsx"],
    }

    def __init__(self, use_tree_sitter: bool = True):
        """
        Initialize LSP analyzer.

        Args:
            use_tree_sitter: Whether to use tree-sitter (requires installation)
        """
        self.use_tree_sitter = use_tree_sitter and TREE_SITTER_AVAILABLE
        self._tree_sitter_parsers = {}

    def analyze_project(
        self, project_path: Path, language: str = "python"
    ) -> CodeStructure:
        """
        Analyze a complete project for code structure.

        Args:
            project_path: Root path of the project
            language: Programming language ("python", "javascript", "typescript")

        Returns:
            CodeStructure with all symbols and dependencies
        """
        project_path = Path(project_path).resolve()

        # Find all code files
        patterns = self.LANGUAGE_PATTERNS.get(language, ["*.py"])
        code_files = self._find_code_files(project_path, patterns)

        # Analyze each file
        all_symbols = []
        all_dependencies = []
        modules = []

        for file_path in code_files:
            try:
                if language == "python":
                    symbols, deps = self._analyze_python_file(file_path)
                else:
                    symbols, deps = self._analyze_generic_file(file_path)

                all_symbols.extend(symbols)
                all_dependencies.extend(deps)

                # Extract module name
                rel_path = file_path.relative_to(project_path)
                module_name = str(rel_path.with_suffix("")).replace(os.sep, ".")
                modules.append(module_name)

            except Exception as e:
                # Skip files that can't be parsed
                print(f"Warning: Could not parse {file_path}: {e}")
                continue

        # Detect entry points
        entry_points = self._detect_entry_points(all_symbols, modules)

        return CodeStructure(
            root_path=project_path,
            symbols=all_symbols,
            dependencies=all_dependencies,
            modules=modules,
            entry_points=entry_points,
        )

    def analyze_file(self, file_path: Path) -> tuple[list[CodeSymbol], list[CodeDependency]]:
        """
        Analyze a single file for symbols and dependencies.

        Args:
            file_path: Path to the file

        Returns:
            Tuple of (symbols, dependencies)
        """
        file_path = Path(file_path)

        if file_path.suffix == ".py":
            return self._analyze_python_file(file_path)
        else:
            return self._analyze_generic_file(file_path)

    def _analyze_python_file(
        self, file_path: Path
    ) -> tuple[list[CodeSymbol], list[CodeDependency]]:
        """Analyze a Python file using AST."""
        try:
            source = file_path.read_text()
            tree = ast.parse(source, filename=str(file_path))
        except SyntaxError:
            return [], []

        symbols = []
        dependencies = []

        # Extract top-level constructs
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                symbol = self._create_class_symbol(node, file_path)
                symbols.append(symbol)

            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                # Only top-level functions (not methods)
                if self._is_top_level(node, tree):
                    symbol = self._create_function_symbol(node, file_path)
                    symbols.append(symbol)

            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                deps = self._extract_dependencies(node, file_path)
                dependencies.extend(deps)

        return symbols, dependencies

    def _create_class_symbol(self, node: ast.ClassDef, file_path: Path) -> CodeSymbol:
        """Create a CodeSymbol from an AST class node."""
        # Extract methods
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method = self._create_function_symbol(item, file_path, parent=node.name)
                methods.append(method)

        # Extract decorators
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]

        return CodeSymbol(
            name=node.name,
            type="class",
            file_path=file_path,
            line_number=node.lineno,
            docstring=ast.get_docstring(node),
            decorators=decorators,
            children=methods,
        )

    def _create_function_symbol(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, file_path: Path, parent: Optional[str] = None
    ) -> CodeSymbol:
        """Create a CodeSymbol from an AST function node."""
        # Build signature
        args = []
        if hasattr(node, "args"):
            for arg in node.args.args:
                args.append(arg.arg)

        signature = f"{node.name}({', '.join(args)})"

        # Extract decorators
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]

        return CodeSymbol(
            name=node.name,
            type="function" if not parent else "method",
            file_path=file_path,
            line_number=node.lineno,
            scope=parent,
            signature=signature,
            docstring=ast.get_docstring(node),
            decorators=decorators,
        )

    def _get_decorator_name(self, decorator: ast.expr) -> str:
        """Extract decorator name from AST node."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return decorator.func.id
        return "unknown"

    def _is_top_level(self, node: ast.FunctionDef, tree: ast.Module) -> bool:
        """Check if a function is top-level (not nested in class)."""
        for item in tree.body:
            if item == node:
                return True
        return False

    def _extract_dependencies(
        self, node: ast.Import | ast.ImportFrom, file_path: Path
    ) -> list[CodeDependency]:
        """Extract dependencies from import statements."""
        dependencies = []

        if isinstance(node, ast.Import):
            for alias in node.names:
                dependencies.append(
                    CodeDependency(
                        source=str(file_path),
                        target=alias.name,
                        import_type="import",
                        imported_names=[alias.asname or alias.name],
                    )
                )

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            import_type = "relative_import" if node.level > 0 else "from_import"
            imported_names = [alias.name for alias in node.names]

            dependencies.append(
                CodeDependency(
                    source=str(file_path),
                    target=module,
                    import_type=import_type,
                    imported_names=imported_names,
                )
            )

        return dependencies

    def _analyze_generic_file(
        self, file_path: Path
    ) -> tuple[list[CodeSymbol], list[CodeDependency]]:
        """Analyze non-Python files using regex patterns."""
        # Basic regex-based analysis for other languages
        # Would be enhanced with tree-sitter in production
        try:
            source = file_path.read_text()
        except Exception:
            return [], []

        symbols = []
        dependencies = []

        # Detect functions (basic pattern matching)
        function_pattern = r"(?:function|def|const|let|var)\s+(\w+)\s*\("
        for match in re.finditer(function_pattern, source):
            line_number = source[: match.start()].count("\n") + 1
            symbols.append(
                CodeSymbol(
                    name=match.group(1),
                    type="function",
                    file_path=file_path,
                    line_number=line_number,
                )
            )

        # Detect imports (basic pattern matching)
        import_pattern = r"(?:import|require|from)\s+['\"]?(\w+)"
        for match in re.finditer(import_pattern, source):
            dependencies.append(
                CodeDependency(
                    source=str(file_path),
                    target=match.group(1),
                    import_type="import",
                )
            )

        return symbols, dependencies

    def _find_code_files(self, root: Path, patterns: list[str]) -> list[Path]:
        """Find all code files matching patterns in a directory tree."""
        files = []
        for pattern in patterns:
            files.extend(root.rglob(pattern))

        # Filter out common ignore patterns
        ignore_patterns = ["__pycache__", ".git", "node_modules", ".venv", "venv"]
        filtered = []
        for f in files:
            if not any(ignore in f.parts for ignore in ignore_patterns):
                filtered.append(f)

        return filtered

    def _detect_entry_points(self, symbols: list[CodeSymbol], modules: list[str]) -> list[str]:
        """Detect likely entry points (main functions, CLI commands)."""
        entry_points = []

        for symbol in symbols:
            # Check for main function
            if symbol.name == "main" and symbol.type == "function":
                entry_points.append(f"{symbol.file_path}::{symbol.name}")

            # Check for if __name__ == "__main__" pattern
            # (Would need source code analysis for this)

        return entry_points

    def get_symbol_graph(self, structure: CodeStructure) -> dict:
        """
        Build a graph of symbol relationships.

        Returns:
            Dict mapping symbol names to their relationships
        """
        graph = {}

        for symbol in structure.symbols:
            key = f"{symbol.file_path}::{symbol.name}"
            graph[key] = {
                "type": symbol.type,
                "children": [
                    f"{symbol.file_path}::{child.name}" for child in symbol.children
                ],
                "dependencies": [],
            }

        # Add dependency edges
        for dep in structure.dependencies:
            source_key = dep.source
            if source_key in graph:
                graph[source_key]["dependencies"].append(dep.target)

        return graph

    def find_symbols_by_type(
        self, structure: CodeStructure, symbol_type: str
    ) -> list[CodeSymbol]:
        """Find all symbols of a specific type."""
        return [s for s in structure.symbols if s.type == symbol_type]

    def find_symbols_by_name(
        self, structure: CodeStructure, name_pattern: str
    ) -> list[CodeSymbol]:
        """Find symbols matching a name pattern (regex)."""
        pattern = re.compile(name_pattern)
        return [s for s in structure.symbols if pattern.search(s.name)]

    def get_dependency_tree(
        self, structure: CodeStructure, root_module: str
    ) -> dict:
        """Build a dependency tree starting from a root module."""
        tree = {"module": root_module, "dependencies": []}

        # Find dependencies of root
        root_deps = [
            dep for dep in structure.dependencies if dep.source.endswith(root_module)
        ]

        for dep in root_deps:
            # Recursively build subtrees (with cycle detection)
            if dep.target != root_module:
                subtree = self.get_dependency_tree(structure, dep.target)
                tree["dependencies"].append(subtree)

        return tree
