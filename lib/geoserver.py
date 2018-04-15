"""Module defines the Geoserver class, which posts rasters to Geoserver via 
REST API, and creates and posts raster styles dependent on what the user input as the 
travel-time threshold on the client-side.

Geoserver class has functions to:
raster_to_geoserver -> Main function which zips raster and calls other function
upload_raster_geoserver -> Posts raster to Geoserver
make_sld -> Creates style 
save_sld -> Read sld data into XML file
upload_sld -> Post style to Geoserver
upload_style -> Create style in Geoserver
"""

import requests
import zipfile
from urlparse import urljoin


class Geoserver:
	"""Class to create style for output raster and post style and raster to Geoserver"""


	def __init__(self, num_hours):
		"""Function to initialise object and create class variables
		
		Arguments:
		num_hours -> Input travel-time threshold

		Returns:
		None
		"""
		self.num_hours = num_hours
		self.api_entry = 'http://172.17.0.2:8080/geoserver/rest/'
		self.credential = ('admin', 'geoserver')

	

	def upload_raster_geoserver(self, file_name):
		"""Function to create coverage (raster) store in geoserver and upload 
		created GEOTiff to the store.

		Arguments:
		file_name -> Zipped output cost-raster

		Returns:
		None
		"""
		resource = 'workspaces/dissertation/coveragestores/time-cost-raster/file.geotiff' #Location in Geoserver
		headers = {'content-type': 'application/zip'}
		request_url = urljoin(self.api_entry, resource)
		#Read file into Geoserver
		with open(file_name, 'rb') as f:
			r = requests.put(
				request_url,
				data=f,
				headers=headers,
				auth=self.credential
			)


	def apply_style(self):
		"""Function to apply style to raster using SLD style file in Geoserver.

		Arguments:
		None

		Returns:
		None
		"""
		resource = 'layers/dissertation:time-cost-raster' #location
		payload = '<layer><defaultStyle><name>time-cost-style</name></defaultStyle></layer>' #data
		headers = {'Content-type': 'text/xml'}
		request_url = urljoin(self.api_entry, resource)
		resp = requests.put(request_url, auth=self.credential, data=payload, headers=headers) #send data


	def upload_sld(self, file_name, sld_name):
		"""Function to create new style in Geoserver
		
		Arguments:
		file_name -> Output raster
		sld_name -> XML style file
		"""
		resource = 'styles/{}'.format(sld_name) #location
		headers = {'content-type': 'application/vnd.ogc.sld+xml'}
		request_url = urljoin(self.api_entry, resource) 
		with open(file_name, 'rb') as f:
			r = requests.put(
				request_url,
				data=f,
				headers=headers,
				auth=self.credential
			)
		self.apply_style()


	#function that creates a new style on geoserver and uploads a specified SLD file to the style container on ther server
	def upload_style(self, filename, sld_name):
		resource = 'styles'
		payload = '<style><name>{0}</name><filename>{1}</filename></style>'.format(sld_name[:-4], filename)
		headers = {'content-type': 'text/xml'}
		request_url = urljoin(self.api_entry, resource)
		r = requests.post(
			request_url,
			data=payload,
			headers=headers,
			auth=self.credential
		)
		#upload SLD file to the style container on the server
		self.upload_sld(filename, sld_name)
		

	#Make sld style XML file for Geoserver
	def make_sld(self, cost_distance_threshold):
		"""Function to make SLD style XML file for Geoserver based on user's 
		travel-time threshold.

		Arguments:
		cost_distance_threshold

		Returns:
		None
		"""
		hrs_dist = cost_distance_threshold * 60
		#string that will be parsed into SLD(XML) file	
		sld_string = '<?xml version="1.0" encoding="UTF-8"?>\n'
		sld_string += '<StyledLayerDescriptor version="1.0.0"\n'
		sld_string += '\txsi:schemaLocation="http://www.opengis.net/sld\n'
		sld_string += '\thttp://schemas.opengis.net/sld/1.0.0/\n'
		sld_string += '\tStyledLayerDescriptor.xsd"\n'
		sld_string += '\txmlns="http://www.opengis.net/sld"\n'
		sld_string += '\txmlns:ogc="http://www.opengis.net/ogc"\n'
		sld_string += '\txmlns:xlink="http://www.w3.org/1999/xlink"\n'
		sld_string += '\txmlns:xsi="http://www.w3.org/2001/\n'
		sld_string += '\tXMLSchema-instance">\n'
		sld_string += '\t\t<NamedLayer>\n'
		sld_string += '\t\t<Name>Time-cost style</Name>\n'
		sld_string += '\t\t<UserStyle>\n'
		sld_string += '\t\t<Title>Time-cost style</Title>\n'
		sld_string += '\t\t\t<FeatureTypeStyle>\n'
		sld_string += '\t\t\t\t<Rule>\n'
		sld_string += '\t\t\t\t\t<RasterSymbolizer>\n'
		sld_string += '\t\t\t\t\t\t<ColorMap>\n'
		sld_string += '\t\t\t\t\t\t\t<ColorMapEntry color="#ffffcc" quantity="-1" opacity="0" />\n'
		sld_string += '\t\t\t\t\t\t\t<ColorMapEntry color="#1a9641" quantity="{}" opacity="0.8" />\n'.format(0)            
		sld_string += '\t\t\t\t\t\t\t<ColorMapEntry color="#58b353" quantity="{}" opacity="0.8"/>\n'.format(hrs_dist/4) #Bins coloured shades of green <= threshold and yellow-orange-red for values > threshold
		sld_string += '\t\t\t\t\t\t\t<ColorMapEntry color="#96d165" quantity="{}" opacity="0.8"/>\n'.format(hrs_dist/3)               
		sld_string += '\t\t\t\t\t\t\t<ColorMapEntry color="#c3e586" quantity="{}" opacity="0.8"/>\n'.format(hrs_dist/2)               
		sld_string += '\t\t\t\t\t\t\t<ColorMapEntry color="#ebf6ac" quantity="{}" opacity="0.8"/>\n'.format(hrs_dist)               
		sld_string += '\t\t\t\t\t\t\t<ColorMapEntry color="#feedaa" quantity="{}" opacity="0.8"/>\n'.format(hrs_dist*2)               
		sld_string += '\t\t\t\t\t\t\t<ColorMapEntry color="#fdc980" quantity="{}" opacity="0.8"/>\n'.format(hrs_dist*3)               
		sld_string += '\t\t\t\t\t\t\t<ColorMapEntry color="#f89d59" quantity="{}" opacity="0.8"/>\n'.format(hrs_dist*4)               
		sld_string += '\t\t\t\t\t\t\t<ColorMapEntry color="#e75b3a" quantity="{}" opacity="0.8"/>\n'.format(hrs_dist*5)               
		sld_string += '\t\t\t\t\t\t\t<ColorMapEntry color="#d7191c" quantity="{}" opacity="0.8"/>\n'.format(hrs_dist*6)               
		sld_string += '\t\t\t\t\t\t</ColorMap>\n'
		sld_string += '\t\t\t\t\t</RasterSymbolizer>\n'
		sld_string += '\t\t\t\t</Rule>\n'
		sld_string += '\t\t\t</FeatureTypeStyle>\n'
		sld_string += '\t\t</UserStyle>\n'
		sld_string += '\t</NamedLayer>\n'
		sld_string += '</StyledLayerDescriptor>\n'
		#read string into file and save
		sld_name = 'time-cost-style.sld'
		filename = "opt/geoserver/data_dir/produced_rasters/{}".format(sld_name)
		fh = open(filename, 'w')
		fh.write(sld_string)
		fh.close()
		#create a style and upload the file 
		self.upload_style(filename, sld_name)
		#self.upload_sld(filename, sld_name)

	def raster_to_geoserver(self):
		"""Main function to call functions to create files and upload to Geoserver.

		Arguments:
		None

		Returns:
		None
		"""
		zipfile.ZipFile('opt/geoserver/data_dir/produced_rasters/time-cost-raster.tif.zip', 'w').write('opt/geoserver/data_dir/produced_rasters/time-cost-raster.tif') #Zip raster to be uploaded to geoserver
		self.upload_raster_geoserver('opt/geoserver/data_dir/produced_rasters/time-cost-raster.tif.zip') #Upload raster to Geoserver
		self.make_sld(self.num_hours) #Create SLD file and upload to Geoserver
