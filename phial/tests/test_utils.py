import pytest
import phial.utils


class TestGlobForeachList:
    def test_list(self, tmpdir):
        directory = tmpdir.mkdir("test_list")

        files = [directory.join(i) for i in ["a1", "a2", "b1", "b3"]]
        for i in files:
            i.open("w")

        globs = [str(directory.join(i)) for i in ["a*", "b*"]]
        assert phial.utils.glob_foreach_list(globs) == files

    def test_single_string(self, tmpdir):
        directory = tmpdir.mkdir("test_single_string")

        files = [directory.join(i) for i in ["a1", "a2"]]
        for i in files:
            i.open("w")

        assert phial.utils.glob_foreach_list(str(directory.join("a*"))) == files

    def test_empty(self, tmpdir):
        assert phial.utils.glob_foreach_list([]) == []

    def test_not_found(self, tmpdir):
        with pytest.raises(IOError):
            phial.utils.glob_foreach_list("adsfasdf")
