import re


def test_package_version_available():
    from encord import __version__
    expected_pattern = re.compile(r"\d\.\d\.\d")
    assert expected_pattern.match(__version__)

