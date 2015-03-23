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

    @pytest.mark.parametrize("path,new_extension,expected", [
        ("joe.txt", ".html", "joe.html"),
        ("joe", ".html", "joe.html"),
        (".bashrc", ".html", ".bashrc.html"),
        ("/var/log/apache.log", ".rst", "/var/log/apache.rst"),
        ("styles/awesome.less", ".css", "styles/awesome.css"),
    ])
    def test_swap_extension(self, path, new_extension, expected):
        print path, new_extension, expected
        assert phial.utils.swap_extension(path, new_extension) == expected
