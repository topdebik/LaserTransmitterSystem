#-*- coding: utf-8 -*-

class keyNotInAlfabetError(Exception):
	def __init__(self, *args):
		if args:
			self.message = args[0]
		else:
			self.message = None
	def __str__(self):
		if self.message:
			return f"keyNotInAlfabetError: '{self.message}'"
		else:
			return "keyNotInAlfabetError"