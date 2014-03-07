# Copyright (c) 2013 John Sullivan
# Copyright (c) 2013 Other contributers as noted in the CONTRIBUTERS file
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
from . import documents

# set up logging
import logging
log = logging.getLogger("phial.pages")

_pages = []
"""
A list of all of the pages registered in the application.

.. note::

    This should not be accessed directly, use get_pages() instead.

"""

def register_page(func, *args, **kwargs):
    _pages.append(Page(func, *args, **kwargs))
    log.debug("Collected page with function %r from module %r.", func.__name__,
        func.__module__)

def register_asset(source_path, *args, **kwargs):
    _pages.append(StaticPage(source_path, *args, **kwargs))
    log.debug("Collected asset at %r.", source_path)

def page(*dec_args, **dec_kwargs):
    # The way decorators with arguments work is that we need to return another
    # decorator that takes in a function, then that decorator will be applied
    # to the function.
    def real_decorator(function):
        # The only thing this decorator does is add the function and its
        # arguments to the list of known pages.
        register_page(function, *dec_args, **dec_kwargs)

        # We don't do the typical decorator thing of wrapping the function so
        # just return the function unchanged.
        return function

    # We want to handle the case of no arguments being passed in

    return real_decorator

def get_pages():
    """Returns a list of all of the pages registered in the application."""

    return _pages

class RenderedPage:
    def __init__(self, content, path = None):
        self.content = content
        self.path = path

class Page(object):
    def __init__(self, func, path = None, files = None):
        """
        :param func: The function that will be called to generate the page.
        :param path: The desired relative path of the page. If `None`, a path must
                be specified in `func`'s return value.
        :param files: May be `None`, a string, or a list of strings.  If a
                string, that string will be globbed and `func` will be called
                for each unique matching file. If a list of strings, each
                string in the list will be globbed and then `func` will be
                called for each unique matching file. If `None`, `func` will be
                called only once.

        """

        self.func = func
        self.path = path
        self.files = files

    def render(self, from_file = None):
        """
        Calls ``func`` appropriately and returns a RenderedPage object.

        """

        if from_file is None:
            result = self.func()
        else:
            result = self.func(from_file)

        if result is None:
            log.info("Page function %s returned None, ignoring.",
                repr(self))
            return None

        if isinstance(result, basestring):
            if self.path is None:
                log.error(
                    "Page function for %s returned only content and path not "
                    "set.", repr(self)
                )
                raise RuntimeError("Path not set.")

            result = RenderedPage(content = result, path = self.path)

        return result

class StaticPage(Page):
    def __init__(self, source_path, dest_path = None):
        self.source_path = source_path

        if dest_path is None:
            dest_path = self.source_path

        super(StaticPage, self).__init__(func = self._static_func,
            path = dest_path)

    def _static_func(self):
        return RenderedPage(
            content = documents.open_file(self.source_path).read(),
            path = self.path)
