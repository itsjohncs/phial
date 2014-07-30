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

# stdlib
import glob
import os.path

def glob_files(files):
    """
    Returns a list of files matching the pattern(s) in ``files``.

    :param files: May be either a string or a list of strings. If a string, the
        pattern will be globbed and all matching files will be returned. If a
        list of strings, all of the patterns will be globbed and all unique
        file paths will be returned.

    :returns: A list of file paths.

    """

    if isinstance(files, basestring):
        result = glob.glob(files)
    else:
        # Glob every pattern and grab the unique results
        result_set = set()
        for i in files:
            result_set.update(glob.glob(i))
        result = list(result_set)

    return result


def is_path_under_directory(path, directory):
    """Returns True if ``path`` is in ``dir``.

    This operates only on paths and does not actually access the filesystem.
    """
    # TODO(brownhead): This might not handle unicode correctly...
    directory = os.path.abspath(directory) + "/"
    path = os.path.abspath(path) + "/"
    return path.startswith(directory)


# TODO(brownhead): Spruce this up so we just get log message with a traceback
# included. It might be worthwhile to get fancy and cut off the last frame
# (this one) to avoid the common confusion of the last frame being pretty
# useless.
def log_and_die(logging_module, *args, **kwargs): 
    logging_module.error(*args, **kwargs)
    raise RuntimeError()
