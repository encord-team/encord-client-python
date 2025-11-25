import warnings

from encord.common.deprecated import deprecated


def test_deprecated() -> None:
    class SampleClass:
        @deprecated(version="1.0", alternative="new_method")
        def method(self):
            return "method called"

    @deprecated(version="1.0")
    class OldClass:
        pass

    with warnings.catch_warnings(record=True) as w:
        obj = SampleClass()
        result = obj.method()

        assert result == "method called"
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "method is deprecated since version 1.0, use new_method instead" in str(w[0].message)

    with warnings.catch_warnings(record=True) as w:
        OldClass()

        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "OldClass is deprecated since version 1.0" in str(w[0].message)
