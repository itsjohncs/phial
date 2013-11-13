class BadFrontMatterError(RuntimeError):
	def __self__(self, path, error_string = None, yaml_error = None):
		self.path = path
		self.error_string = error_string
		self.yaml_error = yaml_error

	def get_string(self):
		return str(self)

	def __str__(self):
		return self.get_string()
