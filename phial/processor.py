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
from . import exceptions
from . import pages
from . import documents
from . import utils

# stdlib
import errno
import inspect
import os
import shutil
import stat

# set up logging
import logging
log = logging.getLogger(__name__)

def _mkdirs(dir_path):
    """Creates a directory and its parents if they don't exist."""

    try:
        os.makedirs(dir_path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

def process(source_dir = "./site", output_dir = "./output",
        index_path = ".phial_index"):
    """
    Processes all of the pages in your site appropriately. This is the function
    the drives the generation of a Phial site and is what is run when you use
    the Phial command line tool.

    """

    # Render the entire site and generate a list of RenderedPage and
    # ResolvedAsset objects. The file system will not be affected by this call.
    artifacts = render_site(source_dir)

    # Figure out the actual paths on the filesystem each RenderedPage and
    # ResolvedAsset object deals with. This will also raise an exception if
    # any relative file paths try to jump out of the source or output
    # directories.
    finalize_paths(artifacts, source_dir, output_dir)

    if index_path is not None:
        index_path = os.path.join(output_dir, index_path)
        clean_output_dir(output_dir, index_path)

    # Actually output the site. After this call exits the entire site will have
    # been given to the filesystem.
    output_site(artifacts)

    if index_path is not None:
        write_index(artifacts, output_dir, index_path)

def write_index(artifacts, output_dir, index_path):
    with open(index_path, "w") as f:
        for i in artifacts:
            # Write the target's path to the index (relative to the output
            # directory).
            print >> f, os.path.relpath(i._target_path, output_dir)

def clean_output_dir(output_dir, index_path):
    # Make a list of old files
    old_files = []

    # I don't embed the open in the with structure before because the nesting
    # looks super unpleasent.
    try:
        f = open(index_path)
    except IOError as e:
        log.debug("Could not open Phial index at %r: %r", index_path, e)
        return

    # Canonicalize the output directory
    output_dir = os.path.abspath(output_dir)

    with f:
        for i in f:
            # Strip any whitespace (there should be a trailing newline)
            i = i.strip()

            # Figure out the actual path of the entry
            path = os.path.join(output_dir, i)

            # Ensure that the path given is not outside of the output
            # directory.
            if not os.path.abspath(path).startswith(output_dir):
                raise RuntimeError("invalid path in index: {!r}".format(i))

            try:
                mode = os.stat(path).st_mode
            except OSError as e:
                if e.errno == errno.ENOENT:
                    log.warning("Entry in Phial index does not exist: %r",
                        os.path.relpath(path))
                    continue

            if stat.S_ISREG(mode):
                old_files.append(path)

    old_directories = set()
    for i in old_files:
        # Keep track of the directories these were in, we'll delete the
        # directories afterwards if they're empty.
        old_directories.add(os.path.dirname(i))

        os.remove(i)

    for i in old_directories:
        try:
            os.removedirs(i)
        except OSError:
            pass

    log.debug("Cleaned output directory. Deleted files %r. Deleted "
        "directories %r.", [os.path.relpath(i) for i in old_files],
        [os.path.relpath(i) for i in old_directories])

def render_site(source_dir):
    """
    Calls the page functions of all registered pages as well as resolving all
    of the registered assets.

    :param source_dir: The source directory to change into.

    :returns: A list of artifacts (RenderedPage and ResolvedAsset objects).

    .. warning::

        This function changes the current directory using ``os.chdir()``. Be
        wary of using this function in a multi-threaded application. It changes
        it back to its previous value right before the function returns.

    """

    # We want all of the relative paths in the user's code to be relative to
    # the source directory, so we're actually going to modify our current
    # directory process-wide.
    old_cwd = os.getcwd()
    os.chdir(source_dir)

    artifacts = []

    # Go through every page we know about and process each one
    for i in pages._pages:
        artifacts += render_page(i)

    # Go through every asset and process each one
    for i in pages._assets:
        artifacts += resolve_asset(i)

    # Reset it back so we don't mess anything up
    os.chdir(old_cwd)

    return artifacts

def finalize_paths(artifacts, source_dir, output_dir):
    """
    Figures out exactly where on the filesystem the artifacts' targets and
    sources (if applicable) are located.

    :param artifacts: A list of artifacts to look at. This list will be
            modified in place and each artifact will have appropriate
            ``_target_path`` and ``_source_path`` attributes set.
    :param source_dir: The source directory as provided by the user.
    :param output_dir: The output directory as provided by the user.

    :returns: None

    """

    # Make the output and source directories canonical
    source_dir = os.path.abspath(source_dir)
    output_dir = os.path.abspath(output_dir)

    # Go through every artifact and make sure that its target and source (if
    # applicable) are valid.
    for i in artifacts:
        # Figure out exactly where on the filesystem we're going to put the
        # artifact.
        i._target_path = os.path.abspath(
            os.path.join(output_dir, i.target))

        # This will ensure that the final destination of this artifact is not
        # outside of the output directory.
        if not i._target_path.startswith(output_dir):
            log.error("Artifact's target is outside of the output "
                "directory: %r", i)
            raise RuntimeError("Artifact target is outside output directory.")

        # Do the same for the source if this is an asset
        if isinstance(i, pages.ResolvedAsset):
            i._source_path = os.path.abspath(
                os.path.join(source_dir, i.source))

            # This will ensure that the source of this artifact is not outside
            # of the source directory.
            if not i._source_path.startswith(source_dir):
                log.error("Artifact's source is outside of source "
                    "directory: %r", i)
                raise RuntimeError("Artifact source is outside source "
                    "directory.")

def output_site(artifacts):
    """
    Outputs the site.

    :param artifacts: A list of artifacts that have already been sent through
            finalize_paths().

    :returns: None

    """

    for i in artifacts:
        # Make sure the destination's directory exists
        _mkdirs(os.path.dirname(i._target_path))

        if isinstance(i, pages.RenderedPage):
            with open(i._target_path, "w") as f:
                if isinstance(i.content, unicode):
                    f.write(i.content.encode("utf_8"))
                else:
                    f.write(i.content)
        else: # it's a ResolvedAsset
            shutil.copy(i._source_path, i._target_path)

def _resolve_target(raw_target, source):
    """
    Resolves a target string with the provided source.

    :param raw_target: The unresolved target string (ex:
            ``projects/{name}.htm``)
    :param source: A Document instance or a file path (the same as what gets
            passed to a Page's func).

    :returns: The resulting file path.

    """

    # We're going to collect information we'll give to str.format()
    target_info = {}

    if source is not None:
        # The source is either a Document or a path
        if isinstance(source, documents.Document):
            source_path = source.file_path
            target_info["frontmatter"] = source.frontmatter
        else:
            source_path = source

        # Give format lots of info on the file's path
        target_info.update({
            "path": source_path,
            "dir": os.path.dirname(source_path),
            "fullname": os.path.basename(source_path),
            "name": os.path.splitext(os.path.basename(source_path))[0],
        })

    # Actually run format on the string and resolve it now
    return raw_target.format(**target_info)

def _resolve_result(result, page, source):
    """
    Takes a result as returned by a page function and transforms it into an
    appropriate RenderedPage or ResolvedAsset object.

    :param result: The return value of a page function.
    :param page: The page object housing that page function.
    :param source: The source provided to the page function. May be ``None``
            to imply that a source was not provided.

    :returns: A RenderedPage or ResolvedAsset object.

    """

    # If the user returned just content, package it up into a RenderedPage
    if not isinstance(result, (pages.RenderedPage, pages.ResolvedAsset)):
        result = pages.RenderedPage(target = None, content = result)

    # If the user didn't explictly provide a target in their return value,
    # and there the page has a target listed...
    if result.target is None and page.target is not None:
        result.target = _resolve_target(page.target, source)

    # If no path is provided by the user but we have a source, we default
    # to using the source's path as the target path as well.
    if result.target is None and source is not None:
        # The source can be a document or a file path
        if isinstance(source, documents.Document):
            result.target = source.file_path
        else:
            result.target = source

    # If the result still doesn't have a target a this point we don't have
    # enough information to figure it out.
    if result.target is None:
        raise RuntimeError("not enough informaton to resolve target for "
            "{!r}".format(page))

    return result

def render_page(page):
    """
    Renders a single page.

    :returns: A list of RenderedPage and/or ResolvedAsset objects.

    """

    # Figure out which parameters the page function supports. See issue #5 for
    # more information on why we do this.
    argspec = inspect.getargspec(page.func)
    arguments = set(argspec.args)
    def filter_args(dictionary):
        """Returns a dictionary containing only keys in ``arguments``."""

        # Include everything is they have a catchall **kwargs
        if argspec.keywords is not None:
            return dictionary

        return dict(i for i in dictionary.items() if i[0] in arguments)

    results = []
    if page.files is None:
        potential_args = {
            "self": page,
            "target": page.target
        }

        result = page.func(**filter_args(potential_args))

        result = _resolve_result(result, page, None)
        results.append(result)
    else:
        # We're going to execute the page function with each file we find
        for path in utils.glob_files(page.files):
            # Only open and parse the file if we're supposed to
            if page.parse_files:
                source = documents.Document(path)
            else:
                source = path

            potential_args = {
                "self": page,
                "source": source,
                "target": _resolve_target(page.target, source)
            }

            # Execute the page function and get whatever the user returns
            result = page.func(**filter_args(potential_args))

            if result is None:
                continue

            result = _resolve_result(result, page, source)
            results.append(result)

    return results

def resolve_asset(asset):
    """
    Resolves a single asset.

    :returns: A list of ResolvedAsset objects.

    """

    results = []
    for path in utils.glob_files(asset.files):
        resolved = pages.ResolvedAsset(target = None, source = path)
        if asset.target is not None:
            resolved.target = _resolve_target(asset.target, path)
        else:
            resolved.target = path

        results.append(resolved)

    return results
