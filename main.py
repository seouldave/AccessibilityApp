"""Module contains main function that instantiates the respective classes needed for the application's
calculation, and calls the objects functions. Finally returns zonal statistics JSON element back to Flask to be returned to 
the client-side. Please see respective modules in lib folder for commented code for different classes."""
	

from lib.cost_distance import *
from lib.zonal_statistics import *
from lib.geoserver import *


def main(start_coord, num_hours, travel_method, country_chosen, population_chosen):
	"""Function create objects from input variables, and carry out functions/processing on the objects.
	Finally returns output data.

	Arguments:
	start_coord
	num_hours
	travel_method
	country_chosen
	population_chosen

	Returns
	zonal_stats
	"""
	#Cost-distance object/Cost-distance calculation
	cost_dist = Cost_distance(start_coord,num_hours, travel_method, country_chosen, population_chosen)
	cost_dist.define_variables()
	in_ds, in_band, geotransform, costarray, holder_array, costDistMCP = cost_dist.open_ds_and_array()
	hosp_offset = cost_dist.get_offsets(start_coord, geotransform)
	cum_cost_array_cont, cum_cost_array_bin = cost_dist.get_costs(holder_array, hosp_offset, costDistMCP, num_hours,costarray)
	cost_dist.build_rasters(in_ds, in_band, geotransform, cum_cost_array_cont, cum_cost_array_bin)
	cost_dist.polygonise_travel_times()
	#Zonal-statistics object/Zonal statistics calculation
	zon_stat_obj = Zonal_statistics(cost_dist.postgis_table, cost_dist.shp_bin, country_chosen, population_chosen)
	zon_stat_obj.shp_to_postGIS()
	zonal_stats = zon_stat_obj.get_zonal_stats()
	#Geoserver object/Post output to Geoserver
	geoserv = Geoserver(num_hours)
	geoserv.raster_to_geoserver()
	return zonal_stats

