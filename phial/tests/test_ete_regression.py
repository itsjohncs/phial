# internal
from .test_resources import sites
from .. import tool

# external
import pytest

# stdlib
import multiprocessing
import tempfile
import shutil
import os


def recursive_compare(dir1, dir2):
    """Return True iff dir1 and dir2 have the same contents. """
    def get_all_files(dir_path):
        for root, dirs, files in os.walk(dir_path):
            for name in files + dirs:
                yield os.path.relpath(os.path.join(root, name), dir_path)

    dir1_files = set(get_all_files(dir1))
    dir2_files = set(get_all_files(dir2))

    if dir1_files.symmetric_difference(dir2_files):
        return False

    common = dir1_files.intersection(dir2_files)
    for i in common:
        path1 = os.path.join(dir1, i)
        path2 = os.path.join(dir2, i)

        isdir1 = os.path.isdir(path1)
        isdir2 = os.path.isdir(path2)
        if isdir1 != isdir2:
            return False

        if (not isdir1 and not isdir2 and
                open(path1).read() != open(path2).read()):
            return False

    return True


class TestSites:
    @pytest.mark.parametrize("site_name", sites.list_sites())
    def test_output_matches(self, site_name):
        """Ensure the output of the site is what we expect."""
        temp_dir = tempfile.mkdtemp()
        try:
            copied_site_dir = os.path.join(temp_dir, "site")
            shutil.copytree(sites.get_site_dir(site_name), copied_site_dir)

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
            assert recursive_compare(output_path, expected_output_path)
        finally:
            shutil.rmtree(temp_dir)
