# Copyright (c) 2013-2014 John Sullivan
# Copyright (c) 2013-2014 Other contributers as noted in the CONTRIBUTERS file
#
# This file is part of phial
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

# stdlib
import pkg_resources
import os

def get_site_dir(name=None):
    """Returns a path containing a site.

    Will extract the site's directory if necessary (if we're in a zip file).
    If ``None`` is given for ``name``, a path to the ``sites_dir/`` directory
    will be returned.
    """
    sites_dir = pkg_resources.resource_filename(
        "phial.tests.test_resources", "sites_dir")
    if not os.path.exists(sites_dir):
        raise RuntimeError(
            "Could not find sites directory at {}.".format(sites_dir))

    if name is None:
        return sites_dir
    else:
        result = os.path.join(sites_dir, name)
        if not os.path.exists(result):
            raise ValueError("Could not find site %s." % (name, ))

        return result

def list_sites():
    """Returns a list of all of the test sites available.

    >>> list_sites()
    ["simple", "readme"]
    """
    return os.listdir(get_site_dir())
