# Copyright (c) 2013-2014 John Sullivan
# Copyright (c) 2013-2014 Other contributers as noted in the CONTRIBUTERS file
#
# This file is part of Phial
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
#
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# internal
from .test_resources import sites
from .. import tool

# external
import pytest

# stdlib
import multiprocessing
import tempfile
import shutil
import filecmp
import os

def recursive_compare(dir1, dir2):
    """Returns True iff dir1 and dir2 have the same contents.
    """
    def get_all_files(dir_path):
        for root, dirs, files in os.walk(dir_path):
            for name in files + dirs:
                yield name

    dir1_files = set(get_all_files(dir1))
    dir2_files = set(get_all_files(dir2))

    if dir1_files.symmetric_difference(dir2_files):
        return False

    common = dir1_files.intersection(dir2_files)
    for i in common:
        a = open(os.path.join(dir1, i)).read()
        b = open(os.path.join(dir2, i)).read()
        if a != b:
            return False

    return True

class TestSites:
    @pytest.mark.parametrize("site_name", sites.list_sites())
    def test_output_matches(self, site_name):
        """Ensure the output of the site is what we expect.
        """
        temp_dir = tempfile.mkdtemp()
        try:
            copied_site_dir = os.path.join(temp_dir, "site")
            shutil.copytree(sites.get_site_dir(site_name), copied_site_dir)

            def chdir_and_runtool(*args, **kwargs):
                os.chdir(copied_site_dir)
                tool.run_tool("-vv", "app.py")

            p = multiprocessing.Process(target=chdir_and_runtool)
            p.start()
            p.join(10)
            assert not p.is_alive(), "Phial did not die, pid={}.".format(p.pid)
            assert p.exitcode == 0

            output_path = os.path.join(copied_site_dir, "output")
            expected_output_path = os.path.join(copied_site_dir,
                                                "expected_output")

            assert os.path.isdir(output_path)
            assert recursive_compare(output_path, expected_output_path)
        finally:
            shutil.rmtree(temp_dir)
