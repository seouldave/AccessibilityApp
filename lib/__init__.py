import sys
import os

path_to_file = os.path.abspath(__file__)
path_to_dir = path_to_file[:-11]
sys.path.append(path_to_dir)
import cost_distance
import zonal_statistics
import geoserver
#import test_class