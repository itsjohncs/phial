from abc import ABCMeta, abstractmethod

class BuildError(RuntimeError):
	def __init__(self, *args, **kwargs):
		RuntimeError.__init__(self, *args, **kwargs)

class Action(object):
	__metaclass__ = ABCMeta

	@abstractmethod
	def build(self, config):
		pass
