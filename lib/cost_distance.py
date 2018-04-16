"""Module defines the Cost_distance class, which takes some input variables passed from
client-side by AJAX, and calculates cost-distance from each pixel in input country to each input
point dataset.

Cost_distance class contains methods to:
__init__ -> Create variables
empty_folders -> clear previous data
define_variables -> define variables
open_ds_and_array -> read data into array
get_offsets -> offset input coordinates to position in array
get_costs -> calculate cost distance from each input point
build_rasters -> create output rasters
polygonise_travel_times -> create binary shapefiles
"""


import os
import gdal, osr, ogr
import numpy as np
from skimage import graph


class Cost_distance:
	"""Class to create variables and rasters, and carries out cost-distance analysis"""

	def __init__(self, start_coord, num_hours, travel_method, country_chosen, population_chosen):
		"""Function initialises object and creates class variables.
		
		Arguments:
		Input variables from client-side:
		start_coord, num_hours, travel_method, country_chosen, population_chosen

		Returns:
		None
		"""
		self.start_coord = start_coord
		self.num_hours = num_hours
		self.travel_method = travel_method
		self.country_chosen = country_chosen
		self.population_chosen = population_chosen
		self.postgis_table = ""
		self.Costsurfacefn = ""
		self.raster_bin = ""
		self.raster_cont = ""
		self.shp_bin = ""

	def empty_folders(self):
		"""Function to delete folders of previously produced data
		
		Arguments:
		None

		Returns:
		None
		"""
		raster_files_to_delete = os.listdir("opt/geoserver/data_dir/produced_rasters") # Empty output folders of previously produced rasters
		for raster in raster_files_to_delete:
			os.remove(os.path.join("opt/geoserver/data_dir/produced_rasters",raster))
		shape_files_to_delete = os.listdir("opt/geoserver/data_dir/produced_shapefiles") # Empty output folders of previously produced shapefiles
		for shape in shape_files_to_delete:
			os.remove(os.path.join("opt/geoserver/data_dir/produced_shapefiles", shape))
		binary_raster_to_delete = os.listdir("output/")
		for raster in binary_raster_to_delete:
			os.remove(os.path.join("output", raster))

	def define_variables(self):
		"""Function to define variables for data to be created from variables received via AJAX.

		Arguments:
		None

		Returns:
		None
		"""		
		self.CostSurfacefn = "rasters/" + self.country_chosen.upper() + "/" + self.country_chosen.upper() + "_" + self.travel_method + "_friction.tif" #Cost raster for chosen country and travel method
		self.empty_folders()
		self.raster_bin = "output/" + self.country_chosen + "_raster_bin.tif" # Binary output raster
		self.raster_cont = "opt/geoserver/data_dir/produced_rasters/time-cost-raster.tif" # Continuous output raster -> Needs to be displayed in Geoserver
		self.shp_bin = "opt/geoserver/data_dir/produced_shapefiles/" + self.country_chosen + "_shp_bin.shp" # Binary shp polygon showing pop inside travel time -> Needs to go to postgis and geoserver
		self.postgis_table = self.country_chosen + "_travel_costs_polygon"

	def open_ds_and_array(self):
		"""Function to open impedance raster and create arrays of same dimensions
		to hold the output data.

		Arguments:
		None

		Returns:
		impedance raster, band, geotransform, cost_array (Numpy array of impedance raster),
		holder_arr (empty array in which to place output - same dimensions as impedance),
		 graph dataset of impedance raster
		"""
		in_ds = gdal.Open(self.CostSurfacefn) #Open impedance raster with GDAL
		in_band = in_ds.GetRasterBand(1) #Access raster band
		geotransform = in_ds.GetGeoTransform() #Access Geotransform data - Origin, pixel dimensions etc
		costarray = in_band.ReadAsArray() #Read impedance raster into NumPy array
		holder_array = np.zeros_like(costarray, dtype=np.int32) #Empty copy of impedance raster
		costDistMCP = graph.MCP_Geometric(costarray, fully_connected=True) #Create graph dataset of impedance raster using scikit-image
		return in_ds, in_band, geotransform, costarray, holder_array, costDistMCP

	def get_offsets(self, startCoord, geotransform):
		"""Function to convert WGS84 input coordinates to cartesian coordinates
		used to place points within NumPy array.

		Arguments:
		List of start coordinates from AJAX
		Geotransform information from impedance raster

		Returns:
		List of hospital offsets
		"""
		hosp_offset = []
		originX = geotransform[0] #Origin pixels
		originY = geotransform[3] #Origin pixels
		pixelWidth = geotransform[1] #Pixel dimensions
		pixelHeight = geotransform[5] #Pixel dimensions
		for coord in startCoord:
			xOffset = int((coord[0] - originX)/pixelWidth) #Calculate cartesian position within array
			yOffset = int((coord[1] - originY)/pixelHeight) #Calculate cartesian position within array
			xy = (yOffset, xOffset) #Cartesian coordinates
			hosp_offset.append(xy)
		return hosp_offset

	def get_costs(self, holder_array, hosp_offset, costDistMCP, num_hours, costarray):
		"""Function calculates cost (travel-time in minutes) from each pixel to 
		each hospital. Output array is created for each input hospital point, the 
		arrays are stacked, and the minimum is extracted for each stack of pixels
		to create array of travel-time from each pixel to its closest input point
		(in travel time).

		Arguments:
		holder_array - empty
		hosp_offset - array of point coordinates
		costDistMCP - graph representation of impedance raster
		num_hours - input threshold from AJAX
		costarray - impedance array

		Returns:
		cum_cost_array_cont -> Continuous cost-distance array
		cum_cost_array_bin -> Binary (threshold) array
		"""
		cost_arrays = [] #list to hold cost arrays for each hospital. These will be stacked later and minimum values extraced
		for i in hosp_offset:
			cumcostdist, trace2 = costDistMCP.find_costs([i]) #Sci-kit image function to calculate costs
			holder_array = np.asarray(cumcostdist) #Insert values into holder_array
			cost_arrays.append(np.copy(holder_array))
		stack = np.stack(cost_arrays, axis=2) #Stack all cost_arrays in z-dimension
		cum_cost_array_cont = stack.min(axis=2) #Extract minimums from 3D stack in z-dimension to create 2D array of minimums
		cum_cost_array_cont = np.rint(cum_cost_array_cont) #Round deimals to closest round number
		cum_cost_array_cont = cum_cost_array_cont.astype(np.int32) #Convert to integer 32 datatype
		np.place(cum_cost_array_cont, costarray==255, -50) #Make nodata value from impedance negative in output so as not to conflict with real values 
		cum_cost_array_bin = np.where(cum_cost_array_cont <= ((num_hours*60)), 1, 0)
		np.place(cum_cost_array_bin, costarray==255, 255) #Set nodata values in binary
		return cum_cost_array_cont, cum_cost_array_bin

	def build_rasters(self, in_ds, in_band, geotransform, cum_cost_array_cont, cum_cost_array_bin):
		"""Function to create output rasters from output NumPy arrays using GDAL
		library.
		
		Arguments:
		input data (in_ds, in_band, geotransform)
		output raster names (raster_cont, raster_bin)
		Output Numpy arrays (cum_cost_array_cont, cum_cost_array_bin)

		Returns:
		None
		"""
		gtiff = gdal.GetDriverByName('GTiff')
		#Create continous raster
		out_ds_cont = gtiff.Create(self.raster_cont, in_band.XSize, in_band.YSize, 1, gdal.GDT_Int32) #Create a tiff with same dimensions as impedance
		out_ds_cont.SetProjection(in_ds.GetProjection())
		out_ds_cont.SetGeoTransform(geotransform)
		out_band_cont = out_ds_cont.GetRasterBand(1)
		out_band_cont.SetNoDataValue(-1)
		out_band_cont.WriteArray(cum_cost_array_cont) #Write Numpy array into raster band
		out_ds_cont.FlushCache()

		#Create binary raster
		out_ds_bin = gtiff.Create(self.raster_bin, in_band.XSize, in_band.YSize, 1, gdal.GDT_Int32) #Create a tiff with same dimensions as impedance
		out_ds_bin.SetProjection(in_ds.GetProjection())
		out_ds_bin.SetGeoTransform(geotransform)
		out_band_bin = out_ds_bin.GetRasterBand(1)
		out_band_bin.SetNoDataValue(255)
		out_band_bin.WriteArray(cum_cost_array_bin) #Write Numpy array into raster band
		out_ds_bin.FlushCache()

	def polygonise_travel_times(self):
		"""Function to polygonise binary raster using GDAL/OGR for input to PostGIS for Zonal statistics.

		Arguments:
		None

		Returns:
		None
		"""		
		latlong = osr.SpatialReference()
		latlong.ImportFromEPSG( 4326 ) #Set SRS
		polygon = self.shp_bin.encode('utf-8') #Set encodings
		in_poly_ds = gdal.Open(self.raster_bin) #Get raster data
		polygon_band = in_poly_ds.GetRasterBand(1)
		drv = ogr.GetDriverByName("ESRI Shapefile") #Set output as ESRI Shp file
		dst_ds = drv.CreateDataSource(polygon)
		dst_layer = dst_ds.CreateLayer(polygon, srs=latlong)
		newField = ogr.FieldDefn('Value', ogr.OFTInteger) # Create field to hold raster binary values (PostGIS selects only 1 and NOT 0)
		dst_layer.CreateField(newField)
		#gdal.Polygonize(polygon_band, None, dst_layer, -1, ["value"], callback=None)
		gdal.Polygonize(polygon_band, None, dst_layer, 0, [], callback=None) #Polygonize raster



	

