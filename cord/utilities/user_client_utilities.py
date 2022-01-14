from dataclasses import dataclass
from typing import Union, List


@dataclass
class LocalImport:
    """
    file_path: Supply the path of the exported folder which contains the images and `annotations.xml` file. Make
    sure to select "Save images" when exporting your CVAT Task or Project.
    """

    file_path: str


ImportMethod = Union[LocalImport]
"""Using images/videos in cloud storage as an alternative import method will be supported in the future."""


@dataclass
class Issue:
    """
    For each `issue_type` there may be multiple occurrences which are documented in the `instances`. The `instances`
    list can provide additional information on how the issue was encountered. If there is no additional information
    available, the `instances` list will be empty.
    """

    issue_type: str
    instances: List[str]


@dataclass
class Issues:
    """
    Any issues that came up during importing a project. These usually come from incompatibilities between data saved
    on different platforms.

    Examples:
        You can use the prettyprinter package to inspect this dataclass if you're using Python 3.9 or older

        >>> import prettyprinter as pp
        >>> pp.install_extras()
        >>>
        >>> issues = ... # some code which returns this object
        >>> pp.pprint(issues)
    """

    errors: List[Issue]
    warnings: List[Issue]
    infos: List[Issue]

    @staticmethod
    def from_dict(d: dict) -> "Issues":
        errors, warnings, infos = [], [], []
        for error in d["errors"]:
            issue = Issue(issue_type=error["issue_type"], instances=error["instances"])
            errors.append(issue)
        for warning in d["warnings"]:
            issue = Issue(issue_type=warning["issue_type"], instances=warning["instances"])
            warnings.append(issue)
        for info in d["infos"]:
            issue = Issue(issue_type=info["issue_type"], instances=info["instances"])
            infos.append(issue)
        return Issues(errors=errors, warnings=warnings, infos=infos)


@dataclass
class CvatImporterSuccess:
    project_hash: str
    dataset_hash: str
    issues: Issues


@dataclass
class CvatImporterError:
    dataset_hash: str
    issues: Issues
