# internal
from .. import tool

# external
import pytest

# stdlib
import multiprocessing
import os
import pkg_resources
import shutil
import tempfile


def locate_example(name=None):
    """Returns an examples location on the filesystem.

    This function will extract the site's directory if necessary (which might be the case if we're
    in a zip file).

    If ``None`` is given for ``name``, a path to the ``sites_dir/`` directory
    will be returned.
    """
    examples_dir = pkg_resources.resource_filename("phial", "examples")
    if not os.path.isdir(examples_dir):
        raise RuntimeError("Could not find example directory at {0}.".format(examples_dir))

    if name is None:
        return examples_dir
    else:
        result = os.path.join(examples_dir, name)
        if not os.path.exists(result):
            raise ValueError("Could not find site {0}.".format(name))

        return result


def list_examples():
    """Return a list of all of the examples available.

    >>> list_examples()
    ["simple", "readme"]
    """
    example_dir = locate_example()
    return [i for i in os.listdir(example_dir) if os.path.isdir(os.path.join(example_dir, i))]


def recursive_compare(actual, expected):
    """Return True iff expected and actual have the same contents.

    :param actual: Path of directory with actual file tree (using the local code).
    :type expected: ``str``
    :param expected: Path of directory with expected file tree.
    :type expected: ``str``
    :returns: ``None``
    """
    def get_all_files(dir_path):
        for root, dirs, files in os.walk(dir_path):
            for name in files + dirs:
                yield os.path.relpath(os.path.join(root, name), dir_path)

    expected_files = set(get_all_files(expected))
    actual_files = set(get_all_files(actual))

    # Both directories should have the same listing of files
    assert not expected_files.symmetric_difference(actual_files)

    for i in expected_files:
        path_actual = os.path.join(actual, i)
        path_expected = os.path.join(expected, i)

        isdir_expected = os.path.isdir(path_actual)
        isdir_actual = os.path.isdir(path_expected)
        assert isdir_expected == isdir_actual, "isDirectory mismatch at {0!r}".format(i)

        if not isdir_expected:
            assert open(path_actual).read() == open(path_expected).read(), (
                "Content mismath at {0!r}".format(i))


class TestSites:
    @pytest.mark.parametrize("site_name", list_examples())
    def test_output_matches(self, site_name):
        """Ensure the output of the site is what we expect."""
        temp_dir = tempfile.mkdtemp()
        try:
            copied_site_dir = os.path.join(temp_dir, "site")
            shutil.copytree(locate_example(site_name), copied_site_dir)

            def chdir_and_runtool(*args, **kwargs):
                os.chdir(copied_site_dir)
                tool.run_tool("-vv", "--no-index", "app.py")

            p = multiprocessing.Process(target=chdir_and_runtool)
            p.start()
            p.join(10)
            assert not p.is_alive(), "Phial did not die, pid={0}.".format(p.pid)
            assert p.exitcode == 0

            output_path = os.path.join(copied_site_dir, "output")
            expected_output_path = os.path.join(copied_site_dir,
                                                "expected_output")

            assert os.path.isdir(output_path)
            recursive_compare(output_path, expected_output_path)
        finally:
            shutil.rmtree(temp_dir)
