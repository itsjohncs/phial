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

class BadFrontMatterError(RuntimeError):
	def __self__(self, path, error_string = None, yaml_error = None):
		self.path = path
		self.error_string = error_string
		self.yaml_error = yaml_error

	def get_string(self):
		return str(self)

	def __str__(self):
		return self.get_string()

class BadPageFunction(RuntimeError):
    def __self__(self, message, page):
        self.message = message
        self.page = page

        RuntimeError.__init__(self, message)

    def get_string(self):
        return str(self)

    def __str__(self):
        return self.get_string()
