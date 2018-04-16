"""Module defines the Zonal_statistics class, which has functions to import binary
shapefile into PostGIS, and to carry out zonal statistics within the zones specified
as 1 (threshold travel-time) in the shapefile.

Zonal_statistics class has functions to:
shp_to_postGIS -> import shapefile to PostGIS database
get_zonal_stats -> Calculate zonal statistics on imported shapefile against
underlying population in database.
"""
import json
import gdal, osr, ogr
import psycopg2


class Zonal_statistics:

	def __init__(self, postgis_table, shp_bin, country_chosen, population_chosen):
		"""Function to initialise object and create class variables

		Arguments:
		postgis_table -> name of table past from main module
		shp_bin -> name of binary shapefile to be imported
		country_chosen; population_chosen -> client variables passed by AJAX

		Returns:
		None
		"""
		self.postgis_table = postgis_table
		self.shp_bin = shp_bin
		self.country_chosen = country_chosen
		self.population_chosen = population_chosen

	def shp_to_postGIS(self):
		"""Function to make connection with PostGIS database and import binary shapefile.

		Arguments:
		postgis_table -> name of table past from main module
		shp_bin -> name of binary shapefile to be imported
		country_chosen; population_chosen -> client variables passed by AJAX

		Returns:
		None
		"""
		try:
			connection = psycopg2.connect("dbname='gis' user='postgres' host='172.17.0.3' password='goat_75'")

		except:
			print "Can't connect to the database"

		cursor = connection.cursor()
		#Drop tables from previous analyses and create new table
		cursor.execute("DROP TABLE IF EXISTS {0}".format(self.postgis_table)) 
		cursor.execute("""CREATE TABLE {0} (
							id SERIAL,
							value integer,
							PRIMARY KEY (id))
						""".format(self.postgis_table))
		cursor.execute("DROP INDEX IF EXISTS levelIndex;")
		cursor.execute("DROP INDEX IF EXISTS geomIndex;")
		cursor.execute("CREATE INDEX levelIndex ON {0}(value)".format(self.postgis_table)) #Create index on threshold zones
		cursor.execute("SELECT AddGeometryColumn('{0}', ".format(self.postgis_table) +
									"'geom', 4326, 'POLYGON', 2)")
		cursor.execute("CREATE INDEX geomIndex ON {0} ".format(self.postgis_table) + #Create index on geometry
						"USING GIST (geom)")
		connection.commit()
		#Open shapefile and convert to WKT (Well known text) for import query.
		for pol in [0,1]:
			fName = self.shp_bin
			shapefile = ogr.Open(fName)
			layer = shapefile.GetLayer(0)
			for i in range(layer.GetFeatureCount()):
				feature = layer.GetFeature(i)
				if feature.GetField('Value') == 1:
					geometry = feature.GetGeometryRef()
					wkt = geometry.ExportToWkt()
					cursor.execute("INSERT INTO {0} (value, geom) ".format(self.postgis_table) + #Insert table into database
									"VALUES (%s, ST_GeomFromText(%s, " +
									"4326))", (pol, wkt))
					connection.commit()

		old_level = connection.isolation_level
		connection.set_isolation_level(0)
		cursor.execute("UPDATE {0} SET geom = ST_MAKEVALID(geom) WHERE NOT ST_IsValid(geom)".format(self.postgis_table)) #Fix self-intersecting geometries
		cursor.execute("VACUUM ANALYZE") #Vacuum analyse to optimise table
		##################################Zonal Stats##################################
		#Drop/Create tables of threshold polygons within each admin unit
		cursor.execute("DROP TABLE IF EXISTS travel_polygons;")
		cursor.execute("DROP index IF EXISTS travel_polygons_geom;")
		cursor.execute("CREATE TABLE travel_polygons AS (SELECT (st_dump(geom)).geom geom FROM {0} WHERE value =1);".format(self.postgis_table))
		cursor.execute("CREATE index travel_polygons_geom on travel_polygons using gist(geom);")
		cursor.execute("DROP TABLE IF EXISTS travel_inter_adm1;")
		cursor.execute("CREATE table travel_inter_adm1 AS(SELECT st_intersection({0}_adm1.geom,travel_polygons.geom) as geom, name_1 as \
		     travel_in_state FROM travel_polygons inner join {0}_adm1 on st_intersects(travel_polygons.geom, {0}_adm1.geom));".format(self.country_chosen))
		cursor.execute("CREATE index travel_inter_adm1_geom on travel_inter_adm1 using gist(geom);")
		cursor.execute("ALTER table travel_inter_adm1 ADD COLUMN key_column BIGSERIAL PRIMARY KEY;")
		#Create table for zonal_stats (population within each admin unit zone)
		cursor.execute("DROP TABLE IF EXISTS zonal_stats_{0};".format(self.country_chosen))
		cursor.execute("DROP TABLE IF EXISTS {0}_{1}_total".format(self.country_chosen, self.population_chosen))
		cursor.execute("CREATE TABLE {0}_{1}_total AS (select distinct (name_1), SUM((ST_SUMMARYStats(a.rast)).sum) as population from {0}_{1} AS a, \
			    {0}_adm1 AS b WHERE ST_Intersects(b.geom, a.rast)GROUP BY name_1)".format(self.country_chosen, self.population_chosen))
		cursor.execute("CREATE TABLE zonal_stats_{0} AS (SELECT distinct(travel_in_state), (SUM(ST_SUMMARYStats(St_clip(rast,geom)))).sum\
		     AS pop_inside_2hrs FROM {0}_{1} INNER JOIN travel_inter_adm1 ON ST_Intersects(travel_inter_adm1.geom, rast) GROUP BY travel_in_state);".format(self.country_chosen, self.population_chosen))
		cursor.execute("ALTER TABLE zonal_stats_{0} ADD COLUMN total_pop numeric,ADD COLUMN pop_outside_2hrs numeric, ADD COLUMN percent_without_access numeric;".format(self.country_chosen))
		cursor.execute("UPDATE zonal_stats_{0} b SET total_pop = a.population FROM {0}_{1}_total a WHERE b.travel_in_state = a.name_1;".format(self.country_chosen, self.population_chosen))
		cursor.execute("UPDATE zonal_stats_{0} SET pop_outside_2hrs = total_pop - pop_inside_2hrs, percent_without_access = ((total_pop - pop_inside_2hrs)/total_pop)*100".format(self.country_chosen))
		connection.set_isolation_level(old_level)

	def get_zonal_stats(self):
		"""Function to query database and get zonal statistics table to be
		returned to client-side.

		Arguments:
		country_chosen

		Returns:
		results -> In json format
		"""
		try:
			connection = psycopg2.connect("dbname='gis' user='postgres' host='172.17.0.3' password='goat_75'")
		except:
			print "Can't connect to the database"
		old_level = connection.isolation_level
		connection.set_isolation_level(0)
		cursor = connection.cursor()
		cursor.execute("SELECT row_to_json(zonal_stats_{0}) as json FROM public.zonal_stats_{0}".format(self.country_chosen)) #Query to select table and convert to JSON
		query = cursor.fetchall()
		results = json.dumps(query)
		connection.set_isolation_level(old_level)
		return results