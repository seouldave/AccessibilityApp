import os, sys
import numpy

class Test:
	def __init__(self, name):
		self.name = name

	def say_hello(self):
		print ("Hello, {0}".format(self.name))
		print(os.path.abspath(__file__))
		array = numpy.random.rand(3,2)
		return array

	def print_path(self):
		rasters = os.listdir('opt/geoserver/data_dir/produced_rasters')
		#rasters = os.listdir('./')
		for folder in rasters:
			print (folder)

	def say_goodbye(self, name):
		print(self.name)

class Test_2:
	def __init__(self):
		self.name = ""

	def make_name(self, name):
		self.name = name
		print("Hello {0}. How are you?".format(self.name))