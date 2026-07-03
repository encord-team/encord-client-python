#!/usr/bin/env python3
# Spell-check docstrings and validate cross-reference links in Python source files.
#
# Usage:
#   uv run scripts/check_docstring_spelling.py                        # check current dir
#   uv run scripts/check_docstring_spelling.py encord/                # check a directory
#   uv run scripts/check_docstring_spelling.py encord/project.py      # check one file
#   uv run scripts/check_docstring_spelling.py --suggest encord/      # show correction hints
#   uv run scripts/check_docstring_spelling.py --fix encord/          # auto-apply corrections
#   uv run scripts/check_docstring_spelling.py --words extra.txt encord/  # extra allowed words
#   uv run scripts/check_docstring_spelling.py --no-check-links encord/  # spell-check only
#
# Exits 0 when no issues are found, 1 otherwise (CI-friendly).
#
# What is ignored by the spell checker:
#   - Sphinx/RST roles: :meth:`x`, :class:`x`, :param name:, :returns:, etc.
#   - Inline code spans: `x`  or  ``x``
#   - Deeply-indented lines (code examples inside docstrings)
#   - YAML / Docusaurus frontmatter blocks (--- ... ---)
#   - Quoted strings (YAML values, slugs)
#   - URLs, hex literals, bare numbers, version strings (1.2.3)
#   - snake_case, CamelCase, and ALL_CAPS identifiers
#   - Hyphenated tokens (kebab-case slugs)
#   - RST section headers: Args:, Returns:, Raises:, etc.
#
# Link checker validates :meth:, :class:, :func:, :attr:, etc. roles pointing
# to encord.* targets against the actual symbols defined in the encord package.

import argparse
import ast
import re
import sys
from pathlib import Path
from typing import Optional

try:
    from spellchecker import SpellChecker
except ImportError:
    print("ERROR: pyspellchecker not installed. Run: uv add --dev pyspellchecker", file=sys.stderr)
    sys.exit(1)

# Technical terms, abbreviations, and project-specific words that are always correct.
KNOWN_WORDS = {
    # Encord / project
    "encord",
    "coord",
    "coco",
    "pycocotools",
    "bbox",
    "bboxes",
    "ontology",
    "ontologies",
    "dicom",
    "nifti",
    "tiff",
    "pcd",
    "pydicom",
    "deidentify",
    "deidentified",
    "deidentification",
    "geospatial",
    # Common abbreviations
    "uuid",
    "uuids",
    "uid",
    "uids",
    "api",
    "apis",
    "sdk",
    "url",
    "urls",
    "uri",
    "uris",
    "json",
    "yaml",
    "html",
    "xml",
    "csv",
    "pdf",
    "png",
    "jpg",
    "jpeg",
    "webm",
    "id",
    "ids",
    "ie",
    "eg",
    "etc",
    "dto",
    "dtos",
    # Python / programming
    "async",
    "await",
    "bool",
    "int",
    "ints",
    "str",
    "uint",
    "uint8",
    "uint16",
    "args",
    "kwargs",
    "cls",
    "attr",
    "attrs",
    "enum",
    "enums",
    "dict",
    "tuple",
    "isinstance",
    "iterable",
    "iterables",
    "subclass",
    "subclasses",
    "subclassed",
    "dataclass",
    "dataclasses",
    "pydantic",
    "numpy",
    "datetime",
    "timezone",
    "pathlib",
    "stdin",
    "stdout",
    "stderr",
    "dateutil",
    "serialization",
    "deserialization",
    "serialize",
    "deserialize",
    "falsy",
    "truthy",
    "inlined",
    "stringified",
    "pre",
    "init",
    "re",
    "ok",
    "app",
    "apps",
    "accessor",
    "accessors",
    "mutator",
    "mutators",
    "querier",
    "bundler",
    "entrypoint",
    "entrypoints",
    "dtype",
    "utils",
    "params",
    "programmatically",
    "presigned",
    "multiframe",
    "multi",
    "whitespace",
    "xpath",
    # Technical domain
    "timestamp",
    "timestamps",
    "millisecond",
    "milliseconds",
    "keyframe",
    "keyframes",
    "polygon",
    "polygons",
    "polyline",
    "polylines",
    "bitmask",
    "bitmasks",
    "bounding",
    "segmentation",
    "annotation",
    "annotations",
    "annotate",
    "annotated",
    "annotator",
    "annotators",
    "metadata",
    "metadatas",
    "workflow",
    "workflows",
    "webhook",
    "webhooks",
    "dataset",
    "datasets",
    "filepath",
    "filepaths",
    "filename",
    "filenames",
    "backend",
    "backends",
    "frontend",
    "readonly",
    "writeback",
    "paginated",
    "pagination",
    "middleware",
    "namespace",
    "namespaces",
    "config",
    "configs",
    "configurability",
    "parameterize",
    "idx",
    "indices",
    "codec",
    "codecs",
    "interpolation",
    "regex",
    "regexes",
    "checkbox",
    "checkboxes",
    "timelapse",
    "subfolder",
    "subfolders",
    "lifecycle",
    "refetch",
    "refetches",
    "analytics",
    "labeler",
    "labelers",
    "intrinsics",
    "actioned",
    "datastructure",
    "telekom",
    "lidar",
    "x",
    "y",
    "z",
    "w",
    "h",
    "n",  # common single-letter variables in docs
}


def _extract_docstring_nodes(tree: ast.Module) -> list[tuple[int, str]]:
    """Return (line_number, docstring_text) for every docstring in the AST."""
    results = []

    def _visit(node: ast.AST) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                value = body[0].value
                if isinstance(value.value, str):
                    results.append((value.lineno, value.value))
        for child in ast.iter_child_nodes(node):
            _visit(child)

    _visit(tree)
    return results


def _clean(text: str) -> str:
    """Strip docstring markup so only prose words remain."""
    # YAML / Docusaurus frontmatter blocks at the start of module docstrings:
    #   ---\ntitle: "..."\n...\n---
    text = re.sub(r"^---\s*\n.*?\n---\s*\n", " ", text, flags=re.DOTALL)
    # Quoted strings (YAML values, slug fragments, etc.)
    text = re.sub(r'"[^"]*"', " ", text)
    # Sphinx/RST roles with backtick content: :meth:`foo.bar`, :class:`Baz`
    text = re.sub(r":[a-zA-Z_]+:`[^`]*`", " ", text)
    # RST field list markers: :param name:, :type name:, :returns:, :raises ExcType:
    text = re.sub(r":[a-zA-Z_]+(?:\s+\S+)?:", " ", text)
    # Double-backtick inline code: ``something``
    text = re.sub(r"``[^`]*``", " ", text)
    # Single-backtick inline code: `something`
    text = re.sub(r"`[^`]*`", " ", text)
    # URLs
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"www\.\S+", " ", text)
    # RST directives: .. note::, .. code-block:: python
    text = re.sub(r"\.\.\s+\w[^\n]*", " ", text)
    # Lines that are deeply indented (code examples in docstrings)
    lines = []
    for line in text.splitlines():
        indent = len(line) - len(line.lstrip())
        if indent < 8:
            lines.append(line)
    text = "\n".join(lines)
    # Hyphenated tokens (slugs, kebab-case): sdk-ref-foo-bar
    text = re.sub(r"\b\w+(?:-\w+)+\b", " ", text)
    # snake_case identifiers
    text = re.sub(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b", " ", text)
    # CamelCase / PascalCase identifiers
    text = re.sub(r"\b[A-Z][a-z]+(?:[A-Z][a-z0-9]*)+\b", " ", text)
    text = re.sub(r"\b[a-z]+(?:[A-Z][a-z0-9]*)+\b", " ", text)
    # ALL_CAPS acronyms / constants (2+ uppercase letters)
    text = re.sub(r"\b[A-Z]{2,}(?:_[A-Z0-9]+)*\b", " ", text)
    # Version strings: v1.0.0, 1.2.3
    text = re.sub(r"\bv?\d+\.\d+(?:\.\d+)*\b", " ", text)
    # Hex values
    text = re.sub(r"\b0x[0-9a-fA-F]+\b", " ", text)
    # Standalone numbers
    text = re.sub(r"\b\d+\b", " ", text)
    # Section header lines (Google/NumPy style): Args:, Returns:, Raises:, …
    text = re.sub(
        r"^(Args|Attributes|Returns|Return|Raises|Note|Notes|Example|Examples"
        r"|Warning|Warnings|See Also|References|Todo|Yields?)\s*:?\s*$",
        " ",
        text,
        flags=re.MULTILINE | re.IGNORECASE,
    )
    # Parenthesised type hints e.g. (int or None)
    text = re.sub(r"\([^)]{0,60}\)", " ", text)
    return text


def _words(text: str) -> list[str]:
    """Return lower-case words of length >= 3, stripping possessive 's."""
    words = []
    for m in re.findall(r"\b[a-zA-Z]+(?:'[a-zA-Z]+)?\b", text):
        w = m.lower()
        if w.endswith("'s"):
            w = w[:-2]
        if len(w) >= 3:
            words.append(w)
    return words


def check_file(path: Path, spell: SpellChecker) -> list[tuple[int, str, list[str]]]:
    """Return list of (line_no, snippet, misspelled_words) for a file."""
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []

    source_lines = source.splitlines()
    issues: list[tuple[int, str, list[str]]] = []

    for lineno, docstring in _extract_docstring_nodes(tree):
        cleaned = _clean(docstring)
        candidates = [w for w in _words(cleaned) if w not in KNOWN_WORDS]
        misspelled = spell.unknown(candidates)
        if misspelled:
            snippet = source_lines[lineno - 1].strip() if lineno <= len(source_lines) else ""
            issues.append((lineno, snippet, sorted(misspelled)))

    return issues


# ---------------------------------------------------------------------------
# Link checker
# ---------------------------------------------------------------------------

# Matches :meth:`target`, :class:`target`, etc. Captures the raw content.
_SPHINX_LINK_RE = re.compile(r":(?:meth|func|class|attr|mod|data|exc|obj):`([^`]+)`")


def _file_to_module_path(py_file: Path, pkg_parent: Path) -> str:
    """Convert e.g. encord/foo/bar.py (relative to pkg_parent) into encord.foo.bar."""
    parts = list(py_file.relative_to(pkg_parent).with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _extract_file_symbols(py_file: Path) -> set[str]:
    """Return symbol names directly defined at module and class level in a file."""
    try:
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
    except Exception:
        return set()

    symbols: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.add(node.name)
        elif isinstance(node, ast.ClassDef):
            symbols.add(node.name)
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    symbols.add(f"{node.name}.{child.name}")
                elif isinstance(child, ast.Assign):
                    for target in child.targets:
                        if isinstance(target, ast.Name):
                            symbols.add(f"{node.name}.{target.id}")
                elif isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
                    symbols.add(f"{node.name}.{child.target.id}")
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    symbols.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            symbols.add(node.target.id)
    return symbols


def _build_reexport_map(pkg_parent: Path) -> dict[str, dict[str, str]]:
    """
    For every __init__.py under encord/, build:
      module_path → {local_name: origin_module}
    for names brought in via 'from X import Y' statements.
    """
    reexports: dict[str, dict[str, str]] = {}
    for init_file in sorted((pkg_parent / "encord").rglob("__init__.py")):
        module = _file_to_module_path(init_file, pkg_parent)
        try:
            tree = ast.parse(init_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        module_map: dict[str, str] = {}
        for node in tree.body:
            if not isinstance(node, ast.ImportFrom) or not node.names:
                continue
            if node.level == 0:
                origin_base = node.module or ""
            else:
                # Relative import: go up node.level package steps from module
                parts = module.split(".")
                steps = node.level
                if steps > len(parts):
                    continue
                base_parts = parts[:-steps] if steps < len(parts) else []
                suffix = node.module or ""
                origin_base = ".".join(base_parts + [suffix]) if suffix else ".".join(base_parts)

            for alias in node.names:
                if alias.name == "*":
                    continue
                local_name = alias.asname if alias.asname else alias.name
                module_map[local_name] = origin_base

        reexports[module] = module_map
    return reexports


def _build_symbol_registry(
    pkg_parent: Path,
) -> tuple[dict[str, set[str]], dict[str, dict[str, str]]]:
    """Build (registry, reexports) for the encord package under pkg_parent."""
    registry: dict[str, set[str]] = {}
    encord_dir = pkg_parent / "encord"
    if not encord_dir.exists():
        return registry, {}
    for py_file in sorted(encord_dir.rglob("*.py")):
        module_path = _file_to_module_path(py_file, pkg_parent)
        registry[module_path] = _extract_file_symbols(py_file)
    return registry, _build_reexport_map(pkg_parent)


def _find_pkg_parent(paths: list[Path]) -> Optional[Path]:
    """Locate the workspace root that contains encord/__init__.py."""
    candidates: list[Path] = [Path.cwd()]
    for p in paths:
        d = p if p.is_dir() else p.parent
        candidates += [d, d.parent]
    for candidate in candidates:
        if (candidate / "encord" / "__init__.py").exists():
            return candidate
    return None


def _extract_encord_links(docstring: str) -> list[str]:
    """Return all encord.* cross-reference targets found in a docstring."""
    links: list[str] = []
    for m in _SPHINX_LINK_RE.finditer(docstring):
        raw = m.group(1).strip()
        # Handle 'display text <target>' form: e.g. "Foo <encord.foo.Foo>"
        angle = re.search(r"<([^>]+)>$", raw)
        target = angle.group(1) if angle else raw
        target = target.lstrip("~")  # strip display-shortening tilde
        target = target.rstrip("()")  # strip trailing () on method refs
        if target.startswith("encord."):
            links.append(target)
    return links


def _resolve_encord_link(
    ref: str,
    registry: dict[str, set[str]],
    reexports: dict[str, dict[str, str]],
) -> tuple[bool, bool]:
    """
    Return (is_valid, is_checkable).

    is_valid=True    → the reference resolves to a known symbol.
    is_checkable=True → the relevant module was found; False means skip reporting.
    """
    parts = ref.split(".")
    found_module = False

    for i in range(len(parts), 0, -1):
        module = ".".join(parts[:i])
        if module not in registry:
            continue

        found_module = True
        remainder_parts = parts[i:]
        remainder = ".".join(remainder_parts)

        if not remainder:
            return True, True  # reference to the module itself

        if remainder in registry[module]:
            return True, True  # direct symbol found

        # Follow re-exports: resolve the first remaining component through __init__.py
        if remainder_parts and module in reexports:
            head = remainder_parts[0]
            origin = reexports[module].get(head)
            if origin and origin in registry and remainder in registry[origin]:
                return True, True

    return False, found_module


def check_links_in_file(
    path: Path,
    registry: dict[str, set[str]],
    reexports: dict[str, dict[str, str]],
) -> list[tuple[int, str, list[str]]]:
    """Return list of (line_no, snippet, broken_links) for a file."""
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []

    source_lines = source.splitlines()
    issues: list[tuple[int, str, list[str]]] = []

    for lineno, docstring in _extract_docstring_nodes(tree):
        broken: list[str] = []
        for link in _extract_encord_links(docstring):
            valid, checkable = _resolve_encord_link(link, registry, reexports)
            if checkable and not valid:
                broken.append(link)
        if broken:
            snippet = source_lines[lineno - 1].strip() if lineno <= len(source_lines) else ""
            issues.append((lineno, snippet, sorted(set(broken))))

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Spell-check docstrings in Python files (US English).")
    parser.add_argument(
        "paths",
        nargs="*",
        default=["."],
        metavar="PATH",
        help="Files or directories to check (default: current directory)",
    )
    parser.add_argument(
        "--words",
        metavar="FILE",
        help="Path to a file with additional allowed words (one per line)",
    )
    parser.add_argument(
        "--suggest",
        action="store_true",
        help="Show spelling suggestions for each misspelled word",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Auto-apply the top suggestion for each misspelled word and rewrite files in place",
    )
    parser.add_argument(
        "--no-check-links",
        action="store_true",
        help="Skip cross-reference link validation",
    )
    args = parser.parse_args()

    spell = SpellChecker(language="en")
    spell.word_frequency.load_words(KNOWN_WORDS)

    if args.words:
        extra = Path(args.words).read_text().splitlines()
        spell.word_frequency.load_words(w.strip().lower() for w in extra if w.strip())

    # Collect .py files
    py_files: list[Path] = []
    raw_paths: list[Path] = []
    for raw in args.paths:
        p = Path(raw)
        raw_paths.append(p)
        if p.is_file() and p.suffix == ".py":
            py_files.append(p)
        elif p.is_dir():
            py_files.extend(sorted(p.rglob("*.py")))
        else:
            print(f"warning: skipping {raw!r} (not a .py file or directory)", file=sys.stderr)

    # Build symbol registry for link checking
    registry: dict[str, set[str]] = {}
    reexports: dict[str, dict[str, str]] = {}
    link_checking = not args.no_check_links and not args.fix
    if link_checking:
        pkg_parent = _find_pkg_parent(raw_paths)
        if pkg_parent is None:
            print(
                "warning: encord/ package not found; skipping link validation",
                file=sys.stderr,
            )
            link_checking = False
        else:
            registry, reexports = _build_symbol_registry(pkg_parent)

    total_spell_words = 0
    total_spell_docstrings = 0
    total_broken_links = 0
    total_link_docstrings = 0

    for path in py_files:
        spell_issues = check_file(path, spell)
        link_issues = check_links_in_file(path, registry, reexports) if link_checking else []

        if args.fix:
            source = path.read_text(encoding="utf-8")
            for _lineno, _snippet, misspelled in spell_issues:
                for word in misspelled:
                    correction = spell.correction(word)
                    if not correction or correction == word:
                        continue

                    def _replace(m: re.Match, _corr: str = correction) -> str:
                        orig = m.group()
                        if orig.isupper():
                            return _corr.upper()
                        if orig[0].isupper():
                            return _corr.capitalize()
                        return _corr

                    source = re.sub(rf"\b{re.escape(word)}\b", _replace, source, flags=re.IGNORECASE)
                    print(f"  fixed: {word!r} -> {correction!r}")
            path.write_text(source, encoding="utf-8")
            print(f"{path}: rewrote with corrections")
            continue

        for lineno, snippet, misspelled in spell_issues:
            total_spell_words += len(misspelled)
            total_spell_docstrings += 1
            print(f"{path}:{lineno}: misspelled: {misspelled}")
            if snippet:
                print(f"    {snippet}")
            if args.suggest:
                for word in misspelled:
                    suggestions = spell.candidates(word) or set()
                    print(f"    {word!r} -> {sorted(suggestions)[:5]}")

        for lineno, snippet, broken in link_issues:
            total_broken_links += len(broken)
            total_link_docstrings += 1
            print(f"{path}:{lineno}: broken links: {broken}")
            if snippet:
                print(f"    {snippet}")

    if args.fix:
        print("Done.")
        return 0

    has_issues = False

    if total_spell_words:
        print(f"\n{total_spell_words} misspelling(s) across {total_spell_docstrings} docstring(s).")
        has_issues = True
    else:
        print("No misspellings found.")

    if link_checking:
        if total_broken_links:
            print(f"{total_broken_links} broken link(s) across {total_link_docstrings} docstring(s).")
            has_issues = True
        else:
            print("No broken links found.")

    return 1 if has_issues else 0


if __name__ == "__main__":
    sys.exit(main())
