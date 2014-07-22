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

__all__ = ["Pipeline", "TemporaryFile", "concat", "cout"]

# stdlib
import shutil
import StringIO
import sys

class Pipeline(object):
    def prepare_contents(self):
        for i in self.contents:
            assert hasattr(i, "name"), \
                   "{i!r} does not have name attribute.".format(i=i)
            i.seek(0)

    def __init__(self, contents):
        self.contents = contents
        self.prepare_contents()

    def pipe(self, transform):
        self.contents = transform(self.contents)
        self.prepare_contents()
        return self

    def __or__(self, transform):
        return self.pipe(transform)

    def __repr__(self):
        return self.__class__.__name__ + "(" + repr(self.contents) + ")"

class TemporaryFile(StringIO.StringIO):
    def __init__(self, name=None):
        StringIO.StringIO.__init__(self)

        self.name = name

class concat(object):
    def __init__(self, output_name=None):
        self.output_name = output_name

    def __call__(self, contents):
        result = TemporaryFile()
        for i in contents:
            shutil.copyfileobj(i, result)
        return [result]

class cout(object):
	def __init__(self, out=sys.stdout):
		self.out = sys.stdout

    def __call__(self, contents):
        for i in contents:
	        shutil.copyfileobj(i, self.out)
	    return contents
