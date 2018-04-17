"""Module to carry out acceptability test on application. Current functionality \
calculates average time to process points and evaluates maximum processing capacity \
of server"""

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time

driver = webdriver.Firefox()


def test_page(country, path_to_points):
	"""Function to calculate average time it takes to run analysis on ten points \
	in input country.

	Arguments:
	country
	path_to_points -> csv file of latlongs

	Returns
	None
	"""
	times = []
	for i in range(10):
		#Web-browser instructions
		driver.get("http://localhost:5000")
		driver.find_element_by_xpath("//select[@id='country_select']/option[text()='{0}']".format(country)).click()
		driver.find_element_by_xpath("//select[@id='raster_select']/option[text()='Women of child-bearing age']").click()
		driver.find_element_by_xpath("//select[@id='impedance_select']/option[text()='Motorised (60km/h)']").click()
		driver.find_element_by_id("files").send_keys(path_to_points)
		driver.find_element_by_class_name("readBytesButtons").click()
		driver.find_element_by_id("add-file-points").click()
		driver.switch_to_alert().accept()
		driver.find_element_by_id('time_travel').send_keys('1')
		start = time.time()
		driver.find_element_by_id('postPoints').click()
		while driver.find_element_by_id('time_cost_raster').is_enabled() == False:
			time.sleep(0.5)
		end = time.time()
		duration = end - start # Time processing
		print "Round {0} too {1} seconds".format(i, duration)
		times.append(duration)
		del start, end, duration
		driver.find_element(By.XPATH, '//button[text()="Restart"]')
		time.sleep(5)
	print "The average time for {0} is {1}".format(country, sum(times)/len(times))
	driver.close()


def test_capacity(country, path_to_points_dir):
	"""Function to test maximum processing capacity of server

	Arguments:
	country
	path_to_points_dir
	
	Returns:
	None
	"""
	num_points = [20,40,60,80,100,200] #Incrementally increase number of points processed
	for i in num_points:
		print "Processing {0} points".format(i)
		csv =  '{0}{1}.csv'.format(path_to_points_dir, i)
		#Web-browser instructions		
		driver.get("http://localhost:5000")
		driver.find_element_by_xpath("//select[@id='country_select']/option[text()='{0}']".format(country)).click()
		driver.find_element_by_xpath("//select[@id='raster_select']/option[text()='Women of child-bearing age']").click()
		driver.find_element_by_xpath("//select[@id='impedance_select']/option[text()='Motorised (60km/h)']").click()
		driver.find_element_by_id("files").send_keys(csv)
		driver.find_element_by_class_name("readBytesButtons").click()
		driver.find_element_by_id("add-file-points").click()
		driver.switch_to_alert().accept()
		driver.find_element_by_id('time_travel').send_keys('1')
		start = time.time()
		driver.find_element_by_id('postPoints').click()
		while driver.find_element_by_id('time_cost_raster').is_enabled() == False:
			time.sleep(0.5)
		end = time.time()
		duration = end - start
		print "Round {0} too {1} seconds".format(i, duration)
		#times.append(duration)
		del start, end, duration, csv
		driver.find_element(By.XPATH, '//button[text()="Restart"]')
		time.sleep(5)
		print "{0} points processed".format(i)



countries = [('South Africa', '/home/david/Programming/dissertation_docker/validation/ZAF/ZAF_ponts.csv' '/home/david/Programming/dissertation_docker/validation/ZAF/ZAF_points'), \
    ('Nigeria', '/home/david/Programming/dissertation_docker/validation/NGA/NGA_points.csv', '/home/david/Programming/dissertation_docker/validation/NGA/NGA_points')]

for country in countries:
	test_capacity(country[0], country[1])
	test_page(country[0], country[2])