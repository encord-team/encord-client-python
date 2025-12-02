#!/usr/bin/env python3
"""
Docstring Linter for Encord SDK

Checks and fixes docstring formatting to ensure optimal documentation generation.
Enforces Sphinx role usage, consistent section headers, and proper cross-references.

Usage:
    # Check only (dry run, no modifications will be made):
    python docstring_linter.py --sdk-path /path/to/encord-client-python/encord --check

    # Check with detailed output (shows all issues grouped by type):
    python docstring_linter.py --sdk-path /path/to/encord-client-python/encord --check --verbose

    # Fix issues automatically:
    python docstring_linter.py --sdk-path /path/to/encord-client-python/encord --fix

    # Check specific files:
    python docstring_linter.py --files user_client.py project.py --check

    # Check specific files with detailed output:
    python docstring_linter.py --files user_client.py project.py --check --verbose

    # Generate detailed report:
    python docstring_linter.py --sdk-path /path/to/sdk --check --report report.json
"""

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union


@dataclass
class DocstringIssue:
    """Represents a single docstring issue."""

    file_path: str
    line_number: int
    function_name: str
    issue_type: str
    severity: str  # 'error', 'warning', 'info'
    message: str
    original: Optional[str] = None
    suggested_fix: Optional[str] = None


@dataclass
class LintResult:
    """Results from linting operation."""

    issues: List[DocstringIssue] = field(default_factory=list)
    files_checked: int = 0
    files_modified: int = 0

    def add_issue(self, issue: DocstringIssue):
        self.issues.append(issue)

    def get_stats(self) -> Dict[str, int]:
        """Get statistics about issues found."""
        stats = {
            "total": len(self.issues),
            "errors": sum(1 for i in self.issues if i.severity == "error"),
            "warnings": sum(1 for i in self.issues if i.severity == "warning"),
            "info": sum(1 for i in self.issues if i.severity == "info"),
        }
        # Count by type
        for issue in self.issues:
            stats[issue.issue_type] = stats.get(issue.issue_type, 0) + 1
        return stats


class DocstringLinter:
    """Lints Python docstrings for documentation generation."""

    # Patterns for SDK classes that should be cross-referenced
    SDK_CLASS_PATTERNS = [
        r"\bLabelRowV2\b",
        r"\bDataset\b",
        r"\bProject\b",
        r"\bOntologyStructure\b",
        r"\bWorkflow\b",
        r"\bStorageItem\b",
        r"\bStorageFolder\b",
        r"\bCollection\b",
        r"\bOntology\b",
        r"\bProjectUser\b",
        r"\bDataRow\b",
        r"\bObjectInstance\b",
        r"\bClassificationInstance\b",
    ]

    # Mapping of class names to their actual import paths
    CLASS_TO_MODULE = {
        "LabelRowV2": "encord.objects.LabelRowV2",
        "Dataset": "encord.dataset.Dataset",
        "Project": "encord.project.Project",
        "OntologyStructure": "encord.objects.OntologyStructure",
        "Workflow": "encord.workflow.Workflow",
        "StorageItem": "encord.storage.StorageItem",
        "StorageFolder": "encord.storage.StorageFolder",
        "Collection": "encord.collection.Collection",
        "Ontology": "encord.ontology.Ontology",
        "ProjectUser": "encord.utilities.project_user.ProjectUser",
        "DataRow": "encord.orm.dataset.DataRow",
        "ObjectInstance": "encord.objects.ObjectInstance",
        "ClassificationInstance": "encord.objects.ClassificationInstance",
    }

    # Known exception names - automatically extracted from exceptions.py
    EXCEPTION_CLASSES = {
        "EncordException",
        "InitialisationError",
        "AuthenticationError",
        "AuthorisationError",
        "ResourceNotFoundError",
        "TimeOutError",
        "RequestException",
        "RateLimitExceededError",
        "PayloadTooLargeError",
        "UnknownException",
        "InvalidDateFormatError",
        "MethodNotAllowedError",
        "OperationNotAllowed",
        "AnswerDictionaryError",
        "CorruptedLabelError",
        "FileTypeNotSupportedError",
        "FileSizeNotSupportedError",
        "FeatureDoesNotExistError",
        "ModelWeightsInconsistentError",
        "ModelFeaturesInconsistentError",
        "UploadOperationNotSupportedError",
        "DetectionRangeInvalidError",
        "InvalidAlgorithmError",
        "ResourceExistsError",
        "DuplicateSshKeyError",
        "SshKeyNotFound",
        "InvalidArgumentsError",
        "GenericServerError",
        "CloudUploadError",
        "MultiLabelLimitError",
        "LabelRowError",
        "OntologyError",
        "WrongProjectTypeError",
        "BundledMoveWorkflowTasksPayloadError",
        # Exceptions from other modules
        "MetadataSchemaError",
    }

    # Build regex patterns for all exceptions
    EXCEPTION_PATTERNS = [rf"\b{exc}\b" for exc in EXCEPTION_CLASSES]

    # Normalize exception names to match actual class names
    # (Some docstrings use American spelling but the class uses British spelling)
    EXCEPTION_NAME_MAPPING = {
        "AuthorizationError": "AuthorisationError",  # Normalize to British spelling
        "AuthorisationError": "AuthorisationError",  # Already correct
    }
    # Default: map each exception to itself
    for exc in EXCEPTION_CLASSES:
        if exc not in EXCEPTION_NAME_MAPPING:
            EXCEPTION_NAME_MAPPING[exc] = exc

    # Exceptions not in encord.exceptions need special path mapping
    EXCEPTION_MODULE_MAPPING = {
        "MetadataSchemaError": "encord.metadata_schema.MetadataSchemaError",
    }

    # Valid Google-style section headers
    VALID_SECTIONS = {
        "Args:",
        "Arguments:",  # Removed 'Parameters:' and 'Params:' - use Args: instead
        "Returns:",
        "Return:",
        "Yields:",
        "Yield:",
        "Raises:",
        "Raise:",
        "Throws:",
        "Note:",
        "Notes:",
        "Warning:",
        "Warnings:",
        "Caution:",
        "Example:",
        "Examples:",
        "See Also:",
        "See also:",
        "Attributes:",
        "Deprecated:",
    }

    # Invalid section headers (markdown bold or non-standard)
    INVALID_SECTION_PATTERNS = [
        r"\*\*Args\*\*:?",  # Matches **Args** or **Args:**
        r"\*\*Args:\*\*",  # Matches **Args:** (bold with colon inside)
        r"Args::",  # Matches Args:: (double colon)
        r"\*\*Returns\*\*:?",  # Matches **Returns** or **Returns:**
        r"\*\*Returns:\*\*",  # Matches **Returns:** (bold with colon inside)
        r"Returns::",  # Matches Returns:: (double colon)
        r"\*\*Raises\*\*:?",  # Matches **Raises** or **Raises:**
        r"\*\*Raises:\*\*",  # Matches **Raises:** (bold with colon inside)
        r"Raises::",  # Matches Raises:: (double colon)
        r"\*\*Note\*\*:?",  # Matches **Note** or **Note:**
        r"\*\*Note:\*\*",  # Matches **Note:** (bold with colon inside)
        r"Note::",  # Matches Note:: (double colon)
        r"\*\*Notes\*\*:?",  # Matches **Notes** or **Notes:**
        r"\*\*Notes:\*\*",  # Matches **Notes:** (bold with colon inside)
        r"Notes::",  # Matches Notes:: (double colon)
        r"\*\*Params\*\*:?",  # Matches **Params** or **Params:**
        r"\*\*Params:\*\*",  # Matches **Params:** (bold with colon inside)
        r"Params::",  # Matches Params:: (double colon)
        r"\*\*Parameters\*\*:?",  # Matches **Parameters** or **Parameters:**
        r"\*\*Parameters:\*\*",  # Matches **Parameters:** (bold with colon inside)
        r"Parameters::",  # Matches Parameters:: (double colon)
        r"\*\*Warning\*\*:?",  # Matches **Warning** or **Warning:**
        r"\*\*Warning:\*\*",  # Matches **Warning:** (bold with colon inside)
        r"Warning::",  # Matches Warning:: (double colon)
        r"\*\*Warnings\*\*:?",  # Matches **Warnings** or **Warnings:**
        r"\*\*Warnings:\*\*",  # Matches **Warnings:** (bold with colon inside)
        r"Warnings::",  # Matches Warnings:: (double colon)
        r"\*\*Example\*\*:?",  # Matches **Example** or **Example:**
        r"\*\*Example:\*\*",  # Matches **Example:** (bold with colon inside)
        r"Example::",  # Matches Example:: (double colon)
        r"\*\*Examples\*\*:?",  # Matches **Examples** or **Examples:**
        r"\*\*Examples:\*\*",  # Matches **Examples:** (bold with colon inside)
        r"Examples::",  # Matches Examples:: (double colon)
        r"\*\*Attributes\*\*:?",  # Matches **Attributes** or **Attributes:**
        r"\*\*Attributes:\*\*",  # Matches **Attributes:** (bold with colon inside)
        r"Attributes::",  # Matches Attributes:: (double colon)
        r"\*\*Yields\*\*:?",  # Matches **Yields** or **Yields:**
        r"\*\*Yields:\*\*",  # Matches **Yields:** (bold with colon inside)
        r"Yields::",  # Matches Yields:: (double colon)
    ]

    # Non-standard section headers that should be replaced
    DEPRECATED_SECTIONS = {
        "Parameters:": "Args:",  # NumPy style → Google style
        "Params:": "Args:",  # Abbreviated form → Standard form
    }

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.sdk_package_name = self.config.get("sdk_package_name", "encord")

    def lint_file(self, file_path: Path, fix: bool = False) -> LintResult:
        """Lint a single Python file.

        Args:
            file_path: Path to the Python file.
            fix: If True, apply fixes to the file.

        Returns:
            LintResult with issues found.
        """
        result = LintResult()
        result.files_checked = 1

        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(file_path))
        except Exception as e:
            result.add_issue(
                DocstringIssue(
                    file_path=str(file_path),
                    line_number=0,
                    function_name="<file>",
                    issue_type="parse_error",
                    severity="error",
                    message=f"Failed to parse file: {e}",
                )
            )
            return result

        # Extract all docstrings
        docstrings = self._extract_docstrings(tree, file_path)

        # Check each docstring
        for node, docstring in docstrings:
            issues = self._check_docstring(node, docstring, file_path)
            result.issues.extend(issues)

        # Check for missing class docstrings
        missing_docstring_issues = self._check_missing_docstrings(tree, file_path)
        result.issues.extend(missing_docstring_issues)

        # Apply fixes if requested
        # Loop until all fixable issues are resolved (some fixes might reveal new issues or
        # prevent other fixes from being found on the first pass)
        max_iterations = 5  # Prevent infinite loops
        iteration = 0
        while fix and result.issues and iteration < max_iterations:
            # Check if there are any fixable issues
            fixable_types = {
                "invalid_section_header",
                "spelling_inconsistency",
                "deprecated_section_header",
                "markdown_list_formatting",
                "inconsistent_indentation",
                "section_spacing",
                "redundant_type_annotation",
                "malformed_class_reference",
                "malformed_method_reference",
                "returns_missing_crossref",
                "incomplete_class_reference",
            }
            has_fixable = any(any(ftype in issue.issue_type for ftype in fixable_types) for issue in result.issues)

            if not has_fixable:
                break

            modified = self._apply_fixes(file_path, content, result.issues)
            if modified:
                result.files_modified = 1
                # Re-parse and re-check with fix=True to continue fixing
                content = file_path.read_text(encoding="utf-8")
                result = self.lint_file(file_path, fix=False)
                iteration += 1
            else:
                # No changes made, exit loop
                break

        return result

    def _extract_docstrings(self, tree: ast.AST, file_path: Path) -> List[Tuple[ast.AST, str]]:
        """Extract all docstrings from an AST.

        Returns:
            List of (node, docstring) tuples.
        """
        docstrings: list[tuple[ast.AST, str]] = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
                docstring = ast.get_docstring(node)
                if docstring:
                    docstrings.append((node, docstring))

        return docstrings

    def _check_missing_docstrings(self, tree: ast.AST, file_path: Path) -> List[DocstringIssue]:
        """Check for classes without docstrings.

        Args:
            tree: The AST tree to check.
            file_path: Path to the file being checked.

        Returns:
            List of issues for missing class docstrings.
        """
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                docstring = ast.get_docstring(node)
                if not docstring:
                    # Skip private classes (starting with _) unless they're special (__init__, etc.)
                    if node.name.startswith("_") and not node.name.startswith("__"):
                        continue

                    issues.append(
                        DocstringIssue(
                            file_path=str(file_path),
                            line_number=node.lineno,
                            function_name=node.name,
                            issue_type="missing_class_docstring",
                            severity="warning",
                            message=f'Class "{node.name}" is missing a docstring',
                        )
                    )

        return issues

    def _check_docstring(self, node: ast.AST, docstring: str, file_path: Path) -> List[DocstringIssue]:
        """Check a single docstring for issues.

        Args:
            node: AST node containing the docstring.
            docstring: The docstring text.
            file_path: Path to the file.

        Returns:
            List of issues found.
        """
        issues: list[DocstringIssue] = []

        # Get function/class name and line number
        if isinstance(node, ast.Module):
            name = "<module>"
            line_number = 1
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            name = node.name
            line_number = node.lineno
        else:
            # Shouldn't happen, but satisfy type checker
            name = "<unknown>"
            line_number = 1

        # Check for issues
        issues.extend(self._check_unlinked_exceptions(docstring, file_path, line_number, name))
        issues.extend(self._check_unlinked_classes(docstring, file_path, line_number, name))
        issues.extend(self._check_malformed_class_references(docstring, file_path, line_number, name))
        issues.extend(self._check_malformed_method_references(docstring, file_path, line_number, name))
        issues.extend(self._check_incomplete_class_references(docstring, file_path, line_number, name))
        issues.extend(self._check_invalid_section_headers(docstring, file_path, line_number, name))
        issues.extend(self._check_deprecated_sections(docstring, file_path, line_number, name))
        issues.extend(self._check_markdown_list_formatting(docstring, file_path, line_number, name))
        issues.extend(self._check_indentation_consistency(docstring, file_path, line_number, name))
        issues.extend(self._check_section_spacing(docstring, file_path, line_number, name))
        issues.extend(self._check_spelling_inconsistencies(docstring, file_path, line_number, name))
        issues.extend(self._check_returns_section(docstring, file_path, line_number, name))

        # Check for redundant type annotations (only for functions)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            issues.extend(self._check_redundant_type_annotations(docstring, file_path, line_number, name, node))

        return issues

    def _check_unlinked_exceptions(
        self, docstring: str, file_path: Path, line_number: int, name: str
    ) -> List[DocstringIssue]:
        """Check for exceptions in Raises section without Sphinx roles."""
        issues: list[DocstringIssue] = []

        # Find Raises section (match lines with or without trailing newline)
        raises_match = re.search(r"Raises?:\s*\n((?:[ \t]+.+(?:\n|$))+)", docstring, re.MULTILINE)
        if not raises_match:
            return issues

        raises_section = raises_match.group(1)

        # Look for exception names without :class: role
        for pattern in self.EXCEPTION_PATTERNS:
            for match in re.finditer(pattern, raises_section):
                exception_name = match.group(0)

                # Check if it's already in a Sphinx role
                start = match.start()
                # Look back far enough to catch the full path
                prefix = raises_section[max(0, start - 100) : start]

                # Check if we're inside a Sphinx role by finding the last backtick before our position
                last_backtick = prefix.rfind("`")
                if last_backtick != -1:
                    # Check if there's a role opener before that backtick
                    text_before_backtick = prefix[:last_backtick]
                    if ":class:" in text_before_backtick or ":exc:" in text_before_backtick:
                        continue

                # Normalize exception name (e.g., AuthorizationError -> AuthorisationError)
                normalized_name = self.EXCEPTION_NAME_MAPPING.get(exception_name, exception_name)

                # Get the full path for the exception
                if normalized_name in self.EXCEPTION_MODULE_MAPPING:
                    exception_path = self.EXCEPTION_MODULE_MAPPING[normalized_name]
                else:
                    exception_path = f"{self.sdk_package_name}.exceptions.{normalized_name}"

                issues.append(
                    DocstringIssue(
                        file_path=str(file_path),
                        line_number=line_number,
                        function_name=name,
                        issue_type="unlinked_exception",
                        severity="warning",
                        message=f'Exception "{exception_name}" should use :class: role',
                        original=exception_name,
                        suggested_fix=f":class:`~{exception_path}`",
                    )
                )

        return issues

    def _check_unlinked_classes(
        self, docstring: str, file_path: Path, line_number: int, name: str
    ) -> List[DocstringIssue]:
        """Check for SDK class references without Sphinx roles."""
        issues = []

        # Skip YAML front matter (between --- markers) if it exists
        front_matter_end = 0
        if docstring.startswith("---"):
            second_marker = docstring.find("---", 3)
            if second_marker != -1:
                front_matter_end = second_marker + 3

        for pattern in self.SDK_CLASS_PATTERNS:
            for match in re.finditer(pattern, docstring):
                class_name = match.group(0)
                start = match.start()

                # Skip if in front matter section
                if start < front_matter_end:
                    continue

                # Check if it's already in a Sphinx role (:class:, :meth:, etc.)
                # Look back far enough to catch the full path (e.g., :class:`~encord.project.XXX`)
                prefix = docstring[max(0, start - 100) : start]

                # Check if we're inside a Sphinx role by finding the last backtick before our position
                last_backtick = prefix.rfind("`")
                if last_backtick != -1:
                    # Check if there's a role opener before that backtick
                    text_before_backtick = prefix[:last_backtick]
                    if (
                        ":class:" in text_before_backtick
                        or ":meth:" in text_before_backtick
                        or ":func:" in text_before_backtick
                        or ":exc:" in text_before_backtick
                        or ":attr:" in text_before_backtick
                        or ":mod:" in text_before_backtick
                    ):
                        continue

                # Skip if in code block (indented or triple backticks)
                line_start = docstring.rfind("\n", 0, start) + 1
                line = docstring[line_start : start + len(class_name)]
                if line.startswith("    ") or line.startswith("```"):
                    continue

                # Skip if it's the function/class name itself being defined
                if class_name == name:
                    continue

                # Use the mapping to get the correct module path, or fall back to naive approach
                if class_name in self.CLASS_TO_MODULE:
                    suggested_path = self.CLASS_TO_MODULE[class_name]
                else:
                    # Fallback: assume module name is class name in lowercase
                    suggested_path = f"{self.sdk_package_name}.{class_name.lower()}.{class_name}"

                issues.append(
                    DocstringIssue(
                        file_path=str(file_path),
                        line_number=line_number,
                        function_name=name,
                        issue_type="unlinked_class",
                        severity="info",
                        message=f'Class "{class_name}" could use :class: role for cross-reference',
                        original=class_name,
                        suggested_fix=f":class:`~{suggested_path}`",
                    )
                )

        return issues

    def _check_malformed_class_references(
        self, docstring: str, file_path: Path, line_number: int, name: str
    ) -> List[DocstringIssue]:
        """Check for malformed :class: role syntax."""
        issues = []

        # Pattern to find malformed :class: references
        # Valid: :class:`path.to.Class` or :class:`~path.to.Class`
        # Invalid: :class:`Class [path]` or :class:`Class path`

        # Find :class: with brackets like :class:`Name [path]`
        bracket_pattern = r":class:`([^`\[]+)\s*\[([^\]]+)\]`"
        for match in re.finditer(bracket_pattern, docstring):
            _display_name = match.group(1).strip()  # Extracted but not used, path is authoritative
            path = match.group(2).strip()
            original = match.group(0)

            # Suggest proper format
            suggested_fix = f":class:`~{path}`"

            issues.append(
                DocstringIssue(
                    file_path=str(file_path),
                    line_number=line_number,
                    function_name=name,
                    issue_type="malformed_class_reference",
                    severity="error",
                    message=f"Malformed :class: syntax. Use :class:`~{path}` instead of brackets.",
                    original=original,
                    suggested_fix=suggested_fix,
                )
            )

        # Find :class: with space-separated name and path like :class:`Name path.to.Name`
        space_pattern = r":class:`([A-Z]\w+)\s+([a-z_][\w.]+[A-Z]\w+)`"
        for match in re.finditer(space_pattern, docstring):
            _display_name = match.group(1)  # Extracted but not used, path is authoritative
            path = match.group(2)
            original = match.group(0)

            # Suggest proper format
            suggested_fix = f":class:`~{path}`"

            issues.append(
                DocstringIssue(
                    file_path=str(file_path),
                    line_number=line_number,
                    function_name=name,
                    issue_type="malformed_class_reference",
                    severity="error",
                    message=f"Malformed :class: syntax. Use :class:`~{path}` instead of space separation.",
                    original=original,
                    suggested_fix=suggested_fix,
                )
            )

        return issues

    def _check_malformed_method_references(
        self, docstring: str, file_path: Path, line_number: int, name: str
    ) -> List[DocstringIssue]:
        """Check for malformed :meth: role syntax."""
        issues = []

        # Pattern to find malformed :meth: references
        # Valid: :meth:`path.to.method` or :meth:`~path.to.method`
        # Invalid: :meth:`Name [path]` or :meth:`Name path`

        # Find :meth: with brackets like :meth:`method_name [path.to.method]`
        bracket_pattern = r":meth:`([^`\[]+)\s*\[([^\]]+)\]`"
        for match in re.finditer(bracket_pattern, docstring):
            _display_name = match.group(1).strip()  # Extracted but not used, path is authoritative
            path = match.group(2).strip()
            original = match.group(0)

            # Suggest proper format
            suggested_fix = f":meth:`~{path}`"

            issues.append(
                DocstringIssue(
                    file_path=str(file_path),
                    line_number=line_number,
                    function_name=name,
                    issue_type="malformed_method_reference",
                    severity="error",
                    message=f"Malformed :meth: syntax. Use :meth:`~{path}` instead of brackets.",
                    original=original,
                    suggested_fix=suggested_fix,
                )
            )

        # Find :meth: with space-separated name and path like :meth:`method_name path.to.method`
        space_pattern = r":meth:`([a-z_]\w+)\s+([a-z_][\w.]+\.[a-z_]\w+)`"
        for match in re.finditer(space_pattern, docstring):
            _display_name = match.group(1)  # Extracted but not used, path is authoritative
            path = match.group(2)
            original = match.group(0)

            # Suggest proper format
            suggested_fix = f":meth:`~{path}`"

            issues.append(
                DocstringIssue(
                    file_path=str(file_path),
                    line_number=line_number,
                    function_name=name,
                    issue_type="malformed_method_reference",
                    severity="error",
                    message=f"Malformed :meth: syntax. Use :meth:`~{path}` instead of space separation.",
                    original=original,
                    suggested_fix=suggested_fix,
                )
            )

        return issues

    def _check_incomplete_class_references(
        self, docstring: str, file_path: Path, line_number: int, name: str
    ) -> List[DocstringIssue]:
        """Check for :class: references that are missing the tilde and full path.

        For example: :class:`EncordException` should be :class:`~encord.exceptions.EncordException`
        """
        issues = []

        # Pattern 1: Find :class:`ClassName` without tilde and full path
        # Match :class:`SomeClass` but not :class:`~path.to.SomeClass` or :class:`path.to.SomeClass`
        pattern_with_backticks = r":class:`([A-Z]\w+)`"

        for match in re.finditer(pattern_with_backticks, docstring):
            class_name = match.group(1)
            original = match.group(0)

            # Check if it's an exception class
            if class_name in self.EXCEPTION_CLASSES:
                # It's an exception - get the correct path
                normalized_name = self.EXCEPTION_NAME_MAPPING.get(class_name, class_name)
                if normalized_name in self.EXCEPTION_MODULE_MAPPING:
                    exception_path = self.EXCEPTION_MODULE_MAPPING[normalized_name]
                else:
                    exception_path = f"{self.sdk_package_name}.exceptions.{normalized_name}"
                suggested_fix = f":class:`~{exception_path}`"
            elif class_name in self.CLASS_TO_MODULE:
                # It's a known SDK class - use the mapping
                suggested_path = self.CLASS_TO_MODULE[class_name]
                suggested_fix = f":class:`~{suggested_path}`"
            else:
                # Unknown class - skip it
                continue

            issues.append(
                DocstringIssue(
                    file_path=str(file_path),
                    line_number=line_number,
                    function_name=name,
                    issue_type="incomplete_class_reference",
                    severity="warning",
                    message=f':class: reference for "{class_name}" is missing tilde and full path',
                    original=original,
                    suggested_fix=suggested_fix,
                )
            )

        # Pattern 2: Find :class:ClassName without backticks at all
        # This is malformed - should be :class:`~path.to.ClassName`
        pattern_no_backticks = r":class:([A-Z]\w+)\b"

        for match in re.finditer(pattern_no_backticks, docstring):
            class_name = match.group(1)
            original = match.group(0)

            # Check if it's an exception class
            if class_name in self.EXCEPTION_CLASSES:
                # It's an exception - get the correct path
                normalized_name = self.EXCEPTION_NAME_MAPPING.get(class_name, class_name)
                if normalized_name in self.EXCEPTION_MODULE_MAPPING:
                    exception_path = self.EXCEPTION_MODULE_MAPPING[normalized_name]
                else:
                    exception_path = f"{self.sdk_package_name}.exceptions.{normalized_name}"
                suggested_fix = f":class:`~{exception_path}`"
            elif class_name in self.CLASS_TO_MODULE:
                # It's a known SDK class - use the mapping
                suggested_path = self.CLASS_TO_MODULE[class_name]
                suggested_fix = f":class:`~{suggested_path}`"
            else:
                # Unknown class - skip it
                continue

            issues.append(
                DocstringIssue(
                    file_path=str(file_path),
                    line_number=line_number,
                    function_name=name,
                    issue_type="incomplete_class_reference",
                    severity="error",
                    message=f':class: reference for "{class_name}" is missing backticks, tilde and full path',
                    original=original,
                    suggested_fix=suggested_fix,
                )
            )

        return issues

    def _check_invalid_section_headers(
        self, docstring: str, file_path: Path, line_number: int, name: str
    ) -> List[DocstringIssue]:
        """Check for invalid section headers (e.g., **Args** instead of Args:)."""
        issues = []

        for pattern in self.INVALID_SECTION_PATTERNS:
            for match in re.finditer(pattern, docstring):
                invalid_header = match.group(0)

                # Skip if this section has markdown list formatting (will be handled by markdown_list_formatting check)
                # Check if the section is followed by blank line(s) and then markdown list items
                pos = match.end()
                remaining = docstring[pos : pos + 200]  # Check next 200 chars
                has_markdown_list = re.search(r"^\s*\n(\s*\n)?\s*-\s+", remaining)
                if has_markdown_list:
                    continue  # Skip - will be handled by markdown_list_formatting

                # Extract the section name (strip both asterisks and colons)
                # Strip colons first, then asterisks (order matters for **Note**: format)
                section_name = invalid_header.rstrip(":").strip("*")
                valid_header = f"{section_name}:"

                issues.append(
                    DocstringIssue(
                        file_path=str(file_path),
                        line_number=line_number,
                        function_name=name,
                        issue_type="invalid_section_header",
                        severity="warning",
                        message=f'Use "{valid_header}" instead of "{invalid_header}"',
                        original=invalid_header,
                        suggested_fix=valid_header,
                    )
                )

        return issues

    def _check_deprecated_sections(
        self, docstring: str, file_path: Path, line_number: int, name: str
    ) -> List[DocstringIssue]:
        """Check for deprecated section headers like Parameters: that should be Args:."""
        issues = []

        for deprecated, replacement in self.DEPRECATED_SECTIONS.items():
            # Look for the deprecated section header at the start of a line (with indentation)
            pattern = rf"^\s*{re.escape(deprecated)}"
            for match in re.finditer(pattern, docstring, re.MULTILINE):
                # Skip if this section has markdown list formatting (will be handled by that check)
                # Check if there's a markdown list after this header
                pos = match.end()
                remaining = docstring[pos : pos + 500]  # Check next 500 chars
                if re.search(r"^\s*\n(\s*\n)?\s*-\s+", remaining):
                    continue  # Skip - will be handled by markdown_list_formatting

                issues.append(
                    DocstringIssue(
                        file_path=str(file_path),
                        line_number=line_number,
                        function_name=name,
                        issue_type="deprecated_section_header",
                        severity="warning",
                        message=f'Use "{replacement}" instead of "{deprecated}" (Google style)',
                        original=deprecated,
                        suggested_fix=replacement,
                    )
                )

        return issues

    def _check_markdown_list_formatting(
        self, docstring: str, file_path: Path, line_number: int, name: str
    ) -> List[DocstringIssue]:
        """Check for markdown list formatting in Args/Returns sections (should be Google Style)."""
        issues = []

        # Pattern to find Args/Parameters/Returns followed by markdown lists
        # Matches "Args:", "**Args**", or "**Args:**" formats
        # Looks for section header followed by optional blank line, then lines starting with "- "
        # The (?:\n|$) handles both lines with newlines and the last line without trailing newline
        section_pattern = r"(\*\*(Args|Parameters|Params|Returns|Yields|Raises)\*\*:?|(Args|Parameters|Params|Returns|Yields|Raises):)\s*\n(\s*\n)?((?:\s*-\s+.*(?:\n|$))+)"

        for match in re.finditer(section_pattern, docstring, re.MULTILINE):
            # Extract section name from either **Name** or Name: format
            if match.group(2):  # **Name** format
                section_name_raw = match.group(2)
            else:  # Name: format
                section_name_raw = match.group(3)

            _blank_line = match.group(4) or ""  # Captured for regex structure, not used
            markdown_list = match.group(5)

            # Normalize section name to Google Style
            section_name = section_name_raw
            if section_name in ("Parameters", "Params"):
                section_name = "Args"

            # Check if this is actually a markdown list (has "- " pattern)
            if re.search(r"^\s*-\s+", markdown_list, re.MULTILINE):
                # Convert markdown list to Google Style
                converted_lines = []
                for line in markdown_list.splitlines():
                    line = line.strip()
                    if line.startswith("- "):
                        # Remove leading "- "
                        line = line[2:]

                        # Remove backticks around parameter name
                        # Pattern: `param_name` (Type): description
                        line = re.sub(r"`([^`]+)`\s*\([^)]+\):", r"\1:", line)

                        # Or just: `param_name`: description
                        line = re.sub(r"`([^`]+)`:", r"\1:", line)

                        # Add proper indentation (4 spaces)
                        converted_lines.append(f"    {line}")

                suggested_section = f"{section_name}:\n" + "\n".join(converted_lines) + "\n"

                issues.append(
                    DocstringIssue(
                        file_path=str(file_path),
                        line_number=line_number,
                        function_name=name,
                        issue_type="markdown_list_formatting",
                        severity="warning",
                        message=f'Section uses markdown list format, should use Google Style "{section_name}:"',
                        original=match.group(0),  # Full matched section
                        suggested_fix=suggested_section,
                    )
                )

        return issues

    def _check_indentation_consistency(
        self, docstring: str, file_path: Path, line_number: int, name: str
    ) -> List[DocstringIssue]:
        """Check for inconsistent indentation in Args/Returns/Raises sections.

        Parameter definition lines should have 4 spaces of indentation.
        Continuation lines (that don't start with param_name:) should have 8 spaces.
        """
        issues = []

        # Pattern to find common docstring sections in Google Style (no markdown lists)
        section_pattern = r"(Args|Returns|Yields|Raises|Note|Notes|Warning|Warnings|See Also|Attributes|Examples?):[ \t]*\n((?:(?!(?:Args|Returns|Yields|Raises|Note|Notes|Warning|Warnings|See Also|Attributes|Examples?):)(?:(?![ \t]*-\s+).*\n|\n))*(?:(?!(?:Args|Returns|Yields|Raises|Note|Notes|Warning|Warnings|See Also|Attributes|Examples?):)(?![ \t]*-\s+).+)?)"

        for match in re.finditer(section_pattern, docstring, re.MULTILINE):
            section_name = match.group(1)
            section_content = match.group(2)

            # Only check indentation for lines before the first blank line
            # Special case: if there's a blank line immediately after the section header,
            # check the lines after it until the next blank line
            lines = section_content.splitlines()

            # Find the first blank line
            first_blank_idx = None
            for i, line in enumerate(lines):
                if not line.strip():
                    first_blank_idx = i
                    break

            # Determine which lines to check
            if first_blank_idx == 0:
                # Blank line immediately after section header - check lines after it
                # Find the next blank line
                second_blank_idx = None
                for i in range(1, len(lines)):
                    if not lines[i].strip():
                        second_blank_idx = i
                        break

                if second_blank_idx is not None:
                    lines_to_check = lines[1:second_blank_idx]
                else:
                    lines_to_check = lines[1:]
            elif first_blank_idx is not None:
                # Blank line found later - check lines before it
                lines_to_check = lines[:first_blank_idx]
            else:
                # No blank line - check all lines
                lines_to_check = lines

            if len(lines_to_check) == 0:
                continue

            # Analyze line types: parameter definitions vs continuation lines
            # A parameter line typically has format: "name: description" or "name (type): description"
            # For Raises sections, also match Sphinx roles: ":class:`ExceptionName`: description"
            # Also match incomplete Sphinx roles: ":class:ExceptionName: description"
            param_line_pattern = r"^\s*(\w+(\s*\([^)]+\))?|:[a-z_:]+:`[^`]+`|:[a-z_:]+:\w+)\s*:"

            # Section headers that should not be treated as parameter lines
            section_headers = {
                "Args:",
                "Returns:",
                "Yields:",
                "Raises:",
                "Attributes:",
                "Note:",
                "Notes:",
                "Example:",
                "Examples:",
                "See Also:",
                "Parameters:",
                "Warning:",
                "Warnings:",
            }

            # For Args/Raises sections: distinguish param lines (4 spaces) from continuation lines (8 spaces)
            # For Returns/Yields sections: all content lines should have 4 spaces (no param lines)
            is_param_section = section_name in ["Args", "Raises"]

            has_incorrect_indent = False
            lines_with_endings = section_content.splitlines(keepends=True)
            fixed_lines = []

            # Determine the range of lines to modify based on blank line position
            if first_blank_idx == 0:
                # Blank line immediately after header - modify lines after first blank until second blank
                second_blank_idx = None
                for i in range(1, len(lines)):
                    if not lines[i].strip():
                        second_blank_idx = i
                        break
                modify_start = 1
                modify_end = second_blank_idx if second_blank_idx is not None else len(lines)
            elif first_blank_idx is not None:
                # Blank line found later - modify lines before it
                modify_start = 0
                modify_end = first_blank_idx
            else:
                # No blank line - modify all lines
                modify_start = 0
                modify_end = len(lines)

            for i, original_line in enumerate(lines_with_endings):
                if i < modify_start or i >= modify_end:
                    # Outside the range to modify - keep as-is
                    fixed_lines.append(original_line)
                elif not original_line.strip():
                    # Keep blank lines as-is
                    fixed_lines.append(original_line)
                else:
                    # Non-empty line before first blank
                    stripped = original_line.lstrip()
                    current_indent = len(original_line) - len(stripped)

                    # Check if this is a section header (should not be treated as parameter line)
                    is_section_header = stripped in section_headers

                    if is_section_header:
                        # Section headers should be left as-is (don't modify indentation)
                        fixed_lines.append(original_line)
                    elif is_param_section:
                        # Args/Raises sections: check if this is a parameter definition line or continuation
                        is_param_line = re.match(param_line_pattern, original_line)

                        if is_param_line:
                            # Parameter definition: should have 4 spaces
                            expected_indent = 4
                        else:
                            # Continuation line: should have 8 spaces
                            expected_indent = 8

                        if current_indent != expected_indent:
                            has_incorrect_indent = True
                            fixed_line = " " * expected_indent + stripped
                            fixed_lines.append(fixed_line)
                        else:
                            fixed_lines.append(original_line)
                    else:
                        # Returns/Yields sections: all description lines should have 4 spaces
                        expected_indent = 4

                        if current_indent != expected_indent:
                            has_incorrect_indent = True
                            fixed_line = " " * expected_indent + stripped
                            fixed_lines.append(fixed_line)
                        else:
                            fixed_lines.append(original_line)

            if has_incorrect_indent:
                fixed_section = "".join(fixed_lines)

                # Include section header to make the replacement unique
                # This prevents replacing the wrong occurrence when multiple functions have similar content
                section_header = section_name + ":\n"  # e.g., "Returns:\n"
                original_with_header = section_header + section_content
                fixed_with_header = section_header + fixed_section

                issues.append(
                    DocstringIssue(
                        file_path=str(file_path),
                        line_number=line_number,
                        function_name=name,
                        issue_type="inconsistent_indentation",
                        severity="warning",
                        message=f"Inconsistent indentation in {section_name} section",
                        original=original_with_header,
                        suggested_fix=fixed_with_header,
                    )
                )

        return issues

    def _check_section_spacing(
        self, docstring: str, file_path: Path, line_number: int, name: str
    ) -> List[DocstringIssue]:
        """Check that there's exactly 1 blank line between sections.

        Google Style requires exactly 1 blank line between sections like Args, Returns, Raises, etc.
        """
        issues = []

        # Pattern to find section headers in Google Style
        section_pattern = (
            r"(Args|Returns|Yields|Raises|Note|Notes|Example|Examples|See Also|Attributes|Parameters):[ \t]*\n"
        )

        # Find all section headers
        sections = list(re.finditer(section_pattern, docstring, re.MULTILINE))

        # Check spacing before the first section (if there's content before it)
        if sections:
            first_section = sections[0]
            before_first = docstring[: first_section.start()]

            # Only check if there's actual content before the first section
            # (not just the opening """ or blank lines)
            if before_first.strip():
                # Count trailing blank lines before the section
                lines = before_first.split("\n")
                trailing_empty = 0
                for line in reversed(lines):
                    if line.strip():
                        break
                    trailing_empty += 1

                num_blank_lines = trailing_empty - 1

                # Google Style requires exactly 1 blank line after summary and before first section
                if num_blank_lines != 1:
                    # Find the last non-blank line
                    last_nonblank_idx = len(lines) - trailing_empty - 1

                    if last_nonblank_idx >= 0:
                        # Reconstruct: content lines + exactly 1 blank line
                        fixed_lines = lines[: last_nonblank_idx + 1] + ["", ""]

                        original = "\n".join(lines)
                        fixed = "\n".join(fixed_lines)

                        if original != fixed:
                            issues.append(
                                DocstringIssue(
                                    file_path=str(file_path),
                                    line_number=line_number,
                                    function_name=name,
                                    issue_type="section_spacing",
                                    severity="warning",
                                    message=f"Expected exactly 1 blank line before {first_section.group(1)} section (found {num_blank_lines})",
                                    original=original,
                                    suggested_fix=fixed,
                                )
                            )

        # Check spacing between consecutive sections
        for i in range(len(sections) - 1):
            current_section = sections[i]
            next_section = sections[i + 1]

            # Get the text between the end of current section header and start of next section header
            between_text = docstring[current_section.end() : next_section.start()]

            # Count blank lines at the end (between sections)
            # Split by newline - when we have "content\n\n", split gives ['content', '', '']
            # The number of trailing empty strings minus 1 is the number of blank lines
            lines = between_text.split("\n")

            # Count empty strings from the end
            trailing_empty = 0
            for line in reversed(lines):
                if line.strip():
                    break
                trailing_empty += 1

            # Number of blank lines = trailing_empty - 1
            # (the last empty string is just after the final \n of the last content line)
            num_blank_lines = trailing_empty - 1

            # Google Style requires exactly 1 blank line between sections
            if num_blank_lines != 1:
                # Find the last non-blank line
                last_nonblank_idx = len(lines) - trailing_empty - 1

                if last_nonblank_idx >= 0:
                    # Reconstruct: content lines + exactly 1 blank line before next section
                    # The blank line is represented by adding an empty string, then the final empty string
                    # This gives us: content\n\n (one blank line)
                    fixed_lines = lines[: last_nonblank_idx + 1] + ["", ""]

                    # Include section headers to make the replacement unique
                    # This prevents replacing the wrong occurrence when multiple functions have similar content
                    current_header = current_section.group(0)  # e.g., "Returns:\n"
                    next_header = next_section.group(0)  # e.g., "Raises:\n"

                    original_with_headers = current_header + "\n".join(lines) + next_header
                    fixed_with_headers = current_header + "\n".join(fixed_lines) + next_header

                    # Only report if there's an actual difference
                    if original_with_headers != fixed_with_headers:
                        issues.append(
                            DocstringIssue(
                                file_path=str(file_path),
                                line_number=line_number,
                                function_name=name,
                                issue_type="section_spacing",
                                severity="warning",
                                message=f"Expected exactly 1 blank line between {current_section.group(1)} and {next_section.group(1)} sections (found {num_blank_lines})",
                                original=original_with_headers,
                                suggested_fix=fixed_with_headers,
                            )
                        )

        return issues

    def _check_redundant_type_annotations(
        self,
        docstring: str,
        file_path: Path,
        line_number: int,
        name: str,
        node: Union[ast.FunctionDef, ast.AsyncFunctionDef],
    ) -> List[DocstringIssue]:
        """Check for redundant type annotations in docstrings when function has type hints."""
        issues: list[DocstringIssue] = []

        # Get function arguments with type annotations
        typed_params = set()
        for arg in node.args.args:
            if arg.annotation is not None:
                typed_params.add(arg.arg)
        # Also check kwonly args
        for arg in node.args.kwonlyargs:
            if arg.annotation is not None:
                typed_params.add(arg.arg)

        if not typed_params:
            # No type annotations in signature, nothing to check
            return issues

        # Find Args sections
        # Pattern matches Args/Parameters section and captures all content until next section or end
        # Uses (?:\n|$) to match lines with or without trailing newlines (last line might not have \n)
        section_pattern = r"(Args|Parameters):[ \t]*\n((?:(?!(?:Args|Returns|Yields|Raises|Example|Note):).*(?:\n|$))*)"

        for match in re.finditer(section_pattern, docstring, re.MULTILINE):
            section_name = match.group(1)
            section_content = match.group(2)

            # Pattern to match parameter lines with type annotations
            # Format: "    param_name (type): description"
            # The type can contain nested brackets, commas, spaces, etc.
            param_with_type_pattern = r"^(\s*)(\w+)\s*\(([^)]+(?:\([^)]*\))*[^)]*)\)\s*:\s*(.*)$"

            lines = section_content.splitlines(keepends=True)
            fixed_lines = []
            has_changes = False

            for line in lines:
                match_param = re.match(param_with_type_pattern, line)
                if match_param:
                    _indent = match_param.group(1)  # Original indent, will be normalized
                    param_name = match_param.group(2)
                    _type_annotation = match_param.group(3)  # Extracted for detection, will be removed
                    description = match_param.group(4)

                    # If this parameter has a type annotation in the function signature,
                    # remove it from the docstring
                    if param_name in typed_params:
                        has_changes = True
                        # Reconstruct line without type annotation
                        # Always use 4 spaces for parameter lines in Args sections
                        correct_indent = "    "  # 4 spaces
                        fixed_line = (
                            f"{correct_indent}{param_name}: {description}\n"
                            if line.endswith("\n")
                            else f"{correct_indent}{param_name}: {description}"
                        )
                        fixed_lines.append(fixed_line)
                    else:
                        # Keep the type annotation if parameter doesn't have one in signature
                        fixed_lines.append(line)
                else:
                    # Not a parameter line (could be continuation or blank line)
                    fixed_lines.append(line)

            if has_changes:
                fixed_section = "".join(fixed_lines)

                issues.append(
                    DocstringIssue(
                        file_path=str(file_path),
                        line_number=line_number,
                        function_name=name,
                        issue_type="redundant_type_annotation",
                        severity="warning",
                        message=f"Type annotations in {section_name} section are redundant when function has type hints",
                        original=section_content,
                        suggested_fix=fixed_section,
                    )
                )

        return issues

    def _check_spelling_inconsistencies(
        self, docstring: str, file_path: Path, line_number: int, name: str
    ) -> List[DocstringIssue]:
        """Check for spelling inconsistencies."""
        issues: list[DocstringIssue] = []

        # Note: AuthorisationError uses British spelling intentionally
        # (that's the actual class name in encord.exceptions)

        return issues

    def _check_returns_section(
        self, docstring: str, file_path: Path, line_number: int, name: str
    ) -> List[DocstringIssue]:
        """Check Returns section for missing cross-references."""
        issues: list[DocstringIssue] = []

        # Find Returns section
        returns_match = re.search(r"Returns?:\s*\n((?:[ \t]+.+\n)+)", docstring, re.MULTILINE)
        if not returns_match:
            return issues

        returns_section = returns_match.group(1)

        # Check if SDK classes are mentioned without :class: role
        for pattern in self.SDK_CLASS_PATTERNS:
            for match in re.finditer(pattern, returns_section):
                class_name = match.group(0)
                start = match.start()

                # Check if it's already in a Sphinx role (:class:, :meth:, etc.)
                # Look back far enough to catch the full path
                prefix = returns_section[max(0, start - 100) : start]

                # Check if we're inside a Sphinx role by finding the last backtick before our position
                last_backtick = prefix.rfind("`")
                if last_backtick != -1:
                    # Check if there's a role opener before that backtick
                    text_before_backtick = prefix[:last_backtick]
                    if (
                        ":class:" in text_before_backtick
                        or ":meth:" in text_before_backtick
                        or ":func:" in text_before_backtick
                        or ":exc:" in text_before_backtick
                        or ":attr:" in text_before_backtick
                        or ":mod:" in text_before_backtick
                    ):
                        continue

                # Use the mapping to get the correct module path, or fall back to naive approach
                if class_name in self.CLASS_TO_MODULE:
                    suggested_path = self.CLASS_TO_MODULE[class_name]
                else:
                    # Fallback: assume module name is class name in lowercase
                    suggested_path = f"{self.sdk_package_name}.{class_name.lower()}.{class_name}"

                issues.append(
                    DocstringIssue(
                        file_path=str(file_path),
                        line_number=line_number,
                        function_name=name,
                        issue_type="returns_missing_crossref",
                        severity="info",
                        message=f'Class "{class_name}" in Returns section should use :class: role',
                        original=class_name,
                        suggested_fix=f":class:`~{suggested_path}`",
                    )
                )

        return issues

    def _apply_fixes(self, file_path: Path, content: str, issues: List[DocstringIssue]) -> bool:
        """Apply automatic fixes to a file.

        Args:
            file_path: Path to the file.
            content: Current file content.
            issues: List of issues to fix.

        Returns:
            True if file was modified, False otherwise.
        """
        modified = False

        # Group issues by what can be auto-fixed
        fixable_issues = [
            i for i in issues if i.original and i.suggested_fix and i.severity in ("error", "warning", "info")
        ]

        if not fixable_issues:
            return False

        # Filter out invalid_section_header fixes if there's a markdown_list_formatting fix for the same function
        # (markdown_list_formatting will handle the full conversion including the header)
        markdown_formatting_functions = {
            i.function_name for i in fixable_issues if i.issue_type == "markdown_list_formatting"
        }
        fixable_issues = [
            i
            for i in fixable_issues
            if not (i.issue_type == "invalid_section_header" and i.function_name in markdown_formatting_functions)
        ]

        # Merge fixes that have the same original text
        # This handles cases where both indentation and spacing fixes apply to the same content
        merged_issues = []
        processed = set()

        for i, issue in enumerate(fixable_issues):
            if i in processed:
                continue

            # Look for other issues with the same original text
            conflicts = []
            for j, other in enumerate(fixable_issues[i + 1 :], start=i + 1):
                if other.original == issue.original and other.function_name == issue.function_name:
                    conflicts.append((j, other))

            if conflicts:
                # Merge the fixes: combine indentation and spacing fixes intelligently
                if issue.suggested_fix is None:
                    # Should not happen for fixable_issues, but handle for type safety
                    merged_issues.append(issue)
                    processed.add(i)
                    continue

                combined_fix: str = issue.suggested_fix

                for idx, (j, conflict) in enumerate(conflicts):
                    # If the conflict is section_spacing, it needs blank lines adjusted (added or removed)
                    if conflict.issue_type == "section_spacing":
                        # section_spacing adjusts blank lines at the end
                        # Count how many newlines are at the end of each
                        def count_trailing_newlines(s: str | None) -> int:
                            if s is None:
                                return 0
                            count = 0
                            for c in reversed(s):
                                if c == "\n":
                                    count += 1
                                else:
                                    break
                            return count

                        if conflict.suggested_fix is not None:
                            # Count trailing newlines to adjust combined fix
                            _orig_newlines = count_trailing_newlines(conflict.original)  # For reference only
                            fix_newlines = count_trailing_newlines(conflict.suggested_fix)

                            # Adjust the combined fix to have the correct number of trailing newlines
                            # Remove existing trailing newlines and add the correct amount
                            combined_fix = combined_fix.rstrip("\n") + "\n" * fix_newlines

                    processed.add(j)

                # Create a merged issue
                merged_issue = DocstringIssue(
                    file_path=issue.file_path,
                    line_number=issue.line_number,
                    function_name=issue.function_name,
                    issue_type=f"{issue.issue_type}+{'+'.join(c.issue_type for _, c in conflicts)}",
                    severity=issue.severity,
                    message=f"{issue.message} (combined with {len(conflicts)} other fixes)",
                    original=issue.original,
                    suggested_fix=combined_fix,
                )
                merged_issues.append(merged_issue)
                processed.add(i)
            else:
                merged_issues.append(issue)
                processed.add(i)

        fixable_issues = merged_issues

        # Sort fixes to apply markdown_list_formatting FIRST
        # This prevents other fixes from changing headers before we can convert the markdown lists
        def fix_priority(issue):
            if issue.issue_type == "markdown_list_formatting":
                return 0  # Highest priority
            else:
                return 1  # Everything else

        fixable_issues.sort(key=fix_priority)

        # Apply fixes
        for issue in fixable_issues:
            # Check if issue type is fixable (handle merged types like "inconsistent_indentation+section_spacing")
            fixable_types = {
                "invalid_section_header",
                "spelling_inconsistency",
                "deprecated_section_header",
                "markdown_list_formatting",
                "inconsistent_indentation",
                "section_spacing",
                "redundant_type_annotation",
                "malformed_class_reference",
                "malformed_method_reference",
                "returns_missing_crossref",
                "incomplete_class_reference",
            }
            is_fixable = any(ftype in issue.issue_type for ftype in fixable_types)

            if not is_fixable or issue.original is None or issue.suggested_fix is None:
                continue

            old_content = content
            original_text: str = issue.original
            suggested_text: str = issue.suggested_fix

            # Handle different types of replacements:
            # 1. Line-based formatting (needs indentation handling)
            # 2. Inline text within docstrings (needs docstring boundary checking)
            # 3. Simple replacements (section headers, etc.)

            needs_indentation_handling = any(
                ftype in issue.issue_type
                for ftype in [
                    "markdown_list_formatting",
                    "inconsistent_indentation",
                    "section_spacing",
                    "redundant_type_annotation",
                ]
            )

            needs_docstring_only = any(
                ftype in issue.issue_type
                for ftype in [
                    "malformed_class_reference",
                    "malformed_method_reference",
                    "returns_missing_crossref",
                    "incomplete_class_reference",
                ]
            )

            if needs_indentation_handling:
                # For line-based formatting issues, we need to handle indentation
                content = self._replace_with_indentation(content, original_text, suggested_text)
            elif needs_docstring_only:
                # For inline text, only replace within docstrings
                content = self._replace_in_docstrings(content, original_text, suggested_text)
            else:
                # For section headers and other simple replacements
                content = content.replace(original_text, suggested_text)

            if content != old_content:
                modified = True

        # Write back if modified
        if modified:
            file_path.write_text(content, encoding="utf-8")
            print(f"  ✓ Fixed {len(fixable_issues)} issues in {file_path.name}")

        return modified

    def _is_within_docstring(self, content: str, pos: int) -> bool:
        """Check if a position in content is within a docstring (between triple quotes)."""
        # Count triple quotes before this position
        before = content[:pos]
        # Count both ''' and """ as docstring delimiters
        triple_double = before.count('"""')
        triple_single = before.count("'''")

        # If odd number of triple quotes before, we're inside a docstring
        # We check both types independently
        in_double = (triple_double % 2) == 1
        in_single = (triple_single % 2) == 1

        return in_double or in_single

    def _is_within_sphinx_role(self, content: str, pos: int) -> bool:
        """Check if a position is within a Sphinx role like :class:`...`."""
        # Look back up to 200 characters to find if we're inside a role
        prefix = content[max(0, pos - 200) : pos]

        # Find the last backtick before our position
        last_backtick = prefix.rfind("`")
        if last_backtick == -1:
            return False

        # Check if there's a role opener (:class:, :meth:, etc.) before that backtick
        text_before_backtick = prefix[:last_backtick]
        sphinx_roles = [":class:", ":meth:", ":func:", ":exc:", ":attr:", ":mod:", ":data:", ":const:"]
        for role in sphinx_roles:
            if role in text_before_backtick:
                # Make sure there's not a closing backtick between the role and our position
                text_after_role = prefix[text_before_backtick.rfind(role) :]
                if text_after_role.count("`") % 2 == 1:
                    # Odd number of backticks means we're inside the role
                    return True
        return False

    def _replace_in_docstrings(self, content: str, original: str, replacement: str) -> str:
        """Replace text only within docstrings (between triple quotes) and not within Sphinx roles.

        This is for inline replacements like class names that appear in the middle of lines.
        Unlike _replace_with_indentation, this works for text anywhere in a docstring.

        Args:
            content: File content with docstrings.
            original: Text to find and replace.
            replacement: Replacement text.

        Returns:
            Modified content with replacements only in docstrings and not in Sphinx roles.
        """
        result = []
        pos = 0

        while True:
            # Find next occurrence
            found_pos = content.find(original, pos)
            if found_pos == -1:
                # No more occurrences, append rest of content
                result.append(content[pos:])
                break

            # Check if this occurrence is within a docstring and not within a Sphinx role
            if self._is_within_docstring(content, found_pos) and not self._is_within_sphinx_role(content, found_pos):
                # Within docstring and not in a role - replace it
                result.append(content[pos:found_pos])
                result.append(replacement)
                pos = found_pos + len(original)
            else:
                # Not in docstring or already in a role - keep original
                result.append(content[pos : found_pos + len(original)])
                pos = found_pos + len(original)

        return "".join(result)

    def _replace_with_indentation(self, content: str, original: str, replacement: str) -> str:
        """Replace text in content, handling different indentation levels.

        The original text is from a dedented docstring, but the file content
        has indented docstrings. This method finds the indented version and
        replaces it with the properly indented replacement.

        Args:
            content: File content with indented docstrings.
            original: Dedented text to find (from AST).
            replacement: Dedented replacement text.

        Returns:
            Modified content with replacement applied.
        """
        # Split original into lines to understand structure
        orig_lines = original.splitlines(keepends=True)
        if not orig_lines:
            return content

        # If last line doesn't have \n, we need to handle both cases
        # (with and without trailing \n in the file)
        variants = [original]
        if not original.endswith("\n"):
            # Try version with trailing newline too
            variants.append(original + "\n")
        elif original.endswith("\n"):
            # Try version without trailing newline too
            variants.append(original.rstrip("\n"))

        # Try to find the original text with various indentation levels (0-16 spaces)
        for i, variant in enumerate(variants):
            variant_lines = variant.splitlines(keepends=True)

            for indent_level in range(0, 17, 4):
                indent = " " * indent_level

                # Create indented version of original
                indented_original = "".join(indent + line if line.strip() else line for line in variant_lines)

                # Find all occurrences and check if they're in docstrings
                pos = 0
                while True:
                    pos = content.find(indented_original, pos)
                    if pos == -1:
                        break

                    # Check if this occurrence is within a docstring
                    if self._is_within_docstring(content, pos):
                        # Found it! Now create indented replacement
                        repl_lines = replacement.splitlines(keepends=True)
                        indented_replacement = "".join(indent + line if line.strip() else line for line in repl_lines)

                        # Match the trailing newline behavior of what we found
                        if not variant.endswith("\n") and indented_replacement.endswith("\n"):
                            indented_replacement = indented_replacement.rstrip("\n")

                        # Do the replacement
                        return content[:pos] + indented_replacement + content[pos + len(indented_original) :]

                    pos += 1

            # Try mixed indentation: first line unindented (for """text format), rest indented
            # This handles docstrings that start with """SomeText on the same line
            for indent_level in range(4, 17, 4):
                indent = " " * indent_level

                # First line no indent, rest with indent
                indented_lines = []
                for idx, line in enumerate(variant_lines):
                    if idx == 0:
                        # First line: no indentation
                        indented_lines.append(line)
                    elif line.strip():
                        # Other non-blank lines: add indentation
                        indented_lines.append(indent + line)
                    else:
                        # Blank lines: keep as-is
                        indented_lines.append(line)

                indented_original = "".join(indented_lines)

                # Find all occurrences and check if they're in docstrings
                pos = 0
                while True:
                    pos = content.find(indented_original, pos)
                    if pos == -1:
                        break

                    # Check if this occurrence is within a docstring
                    if self._is_within_docstring(content, pos):
                        # Found it! Now create indented replacement with same pattern
                        repl_lines = replacement.splitlines(keepends=True)
                        indented_repl_lines = []
                        for idx, line in enumerate(repl_lines):
                            if idx == 0:
                                indented_repl_lines.append(line)
                            elif line.strip():
                                indented_repl_lines.append(indent + line)
                            else:
                                indented_repl_lines.append(line)

                        indented_replacement = "".join(indented_repl_lines)

                        # Match the trailing newline behavior
                        if not variant.endswith("\n") and indented_replacement.endswith("\n"):
                            indented_replacement = indented_replacement.rstrip("\n")

                        return content[:pos] + indented_replacement + content[pos + len(indented_original) :]

                    pos += 1

        # Fallback: try simple replacement (for non-indented cases) but only within docstrings
        pos = content.find(original)
        if pos != -1 and self._is_within_docstring(content, pos):
            return content[:pos] + replacement + content[pos + len(original) :]

        return content

    def lint_directory(self, directory: Path, fix: bool = False) -> LintResult:
        """Lint all Python files in a directory recursively.

        Args:
            directory: Directory to lint.
            fix: If True, apply fixes to files.

        Returns:
            Combined LintResult for all files.
        """
        combined_result = LintResult()

        python_files = list(directory.rglob("*.py"))
        print(f"Scanning {len(python_files)} Python files in {directory}...\n")

        for py_file in python_files:
            # Skip __pycache__ and similar
            if "__pycache__" in str(py_file) or ".pytest_cache" in str(py_file):
                continue

            result = self.lint_file(py_file, fix=fix)
            combined_result.files_checked += result.files_checked
            combined_result.files_modified += result.files_modified
            combined_result.issues.extend(result.issues)

        return combined_result


def print_report(result: LintResult, verbose: bool = False):
    """Print a human-readable report of linting results.

    Args:
        result: LintResult to report on.
        verbose: If True, show all issues. If False, show summary only.
    """
    stats = result.get_stats()

    print("\n" + "=" * 70)
    print("DOCSTRING LINTING REPORT")
    print("=" * 70)

    print(f"\nFiles checked: {result.files_checked}")
    if result.files_modified > 0:
        print(f"Files modified: {result.files_modified}")

    print(f"\nTotal issues: {stats['total']}")
    print(f"  Errors:   {stats['errors']}")
    print(f"  Warnings: {stats['warnings']}")
    print(f"  Info:     {stats['info']}")

    if stats["total"] == 0:
        print("\n✓ No issues found!")
        return

    # Show breakdown by type
    print("\nIssues by type:")
    issue_types = {k: v for k, v in stats.items() if k not in ("total", "errors", "warnings", "info")}
    for issue_type, count in sorted(issue_types.items(), key=lambda x: -x[1]):
        print(f"  {issue_type}: {count}")

    # Show detailed issues if verbose
    if verbose:
        print("\n" + "-" * 70)
        print("DETAILED ISSUES")
        print("-" * 70)

        # Group by issue type, then by file
        issues_by_type: dict[str, list[DocstringIssue]] = {}
        for issue in result.issues:
            issues_by_type.setdefault(issue.issue_type, []).append(issue)

        # Sort by issue type (descending by count)
        for issue_type in sorted(issues_by_type.keys(), key=lambda t: len(issues_by_type[t]), reverse=True):
            issues = issues_by_type[issue_type]
            print(f"\n{issue_type} ({len(issues)}):")
            print("-" * 70)

            # Group by file within each issue type
            issues_by_file: dict[str, list[DocstringIssue]] = {}
            for issue in issues:
                issues_by_file.setdefault(issue.file_path, []).append(issue)

            for file_path, file_issues in sorted(issues_by_file.items()):
                for issue in sorted(file_issues, key=lambda x: x.line_number):
                    severity_marker = {"error": "✗", "warning": "⚠", "info": "ℹ"}.get(issue.severity, "•")

                    # Use clickable format: file:line: message
                    print(f"{file_path}:{issue.line_number}: {severity_marker} [{issue.function_name}] {issue.message}")
                    if issue.suggested_fix and issue.original:
                        print(f'  "{issue.original}" → "{issue.suggested_fix}"')


def save_json_report(result: LintResult, output_path: Path):
    """Save linting results as JSON.

    Args:
        result: LintResult to save.
        output_path: Path to output JSON file.
    """
    data = {
        "files_checked": result.files_checked,
        "files_modified": result.files_modified,
        "statistics": result.get_stats(),
        "issues": [
            {
                "file": issue.file_path,
                "line": issue.line_number,
                "function": issue.function_name,
                "type": issue.issue_type,
                "severity": issue.severity,
                "message": issue.message,
                "original": issue.original,
                "suggested_fix": issue.suggested_fix,
            }
            for issue in result.issues
        ],
    }

    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nJSON report saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Lint Python docstrings for Encord SDK documentation generation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--sdk-path", type=Path, help="Path to SDK source directory")
    group.add_argument("--files", nargs="+", type=Path, help="Specific files to check")

    parser.add_argument("--check", action="store_true", help="Check only (no modifications)")
    parser.add_argument("--fix", action="store_true", help="Automatically fix issues where possible")
    parser.add_argument("--report", type=Path, help="Save JSON report to file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed issues")
    parser.add_argument("--config", type=Path, help="Config file (JSON)")

    args = parser.parse_args()

    # Load config if provided
    config = {}
    if args.config and args.config.exists():
        config = json.loads(args.config.read_text(encoding="utf-8"))

    # Default to check mode if neither specified
    if not args.check and not args.fix:
        args.check = True

    # Create linter
    linter = DocstringLinter(config)

    # Run linting
    if args.sdk_path:
        if not args.sdk_path.exists():
            print(f"Error: SDK path not found: {args.sdk_path}")
            sys.exit(1)
        result = linter.lint_directory(args.sdk_path, fix=args.fix)
    else:
        result = LintResult()
        for file_path in args.files:
            if not file_path.exists():
                print(f"Error: File not found: {file_path}")
                continue
            file_result = linter.lint_file(file_path, fix=args.fix)
            result.files_checked += file_result.files_checked
            result.files_modified += file_result.files_modified
            result.issues.extend(file_result.issues)

    # Print report
    print_report(result, verbose=args.verbose)

    # Save JSON report if requested
    if args.report:
        save_json_report(result, args.report)

    # Exit with error code if issues found
    stats = result.get_stats()
    if stats["errors"] > 0:
        sys.exit(1)
    elif stats["warnings"] > 0:
        sys.exit(0 if args.fix else 1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
