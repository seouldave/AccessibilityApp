from flask import Flask, render_template, jsonify, request
from main import *


app = Flask(__name__)

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/process', methods=['POST'])
##Received AJAX request from client-side and pass to 'main' module to call other classes. Returns result to client-side
def process():
	data = request.get_json() #Data received from client-side
	start_coord = data['array'] #Data received from client-side
	num_hours = data['time_travel'] #Data received from client-side
	travel_method = data['travel_method'] #Data received from client-side
	country_chosen = data['country_chosen'][:3] #Data received from client-side
	if data['population_chosen'][1:5] == "preg":
		population_chosen = "preg"  #Data received from client-side
	elif data['population_chosen'][1:5] == "wocb":
		population_chosen = "wocba" #Data received from client-side
	else:
		population_chosen = "bth" #Data received from client-side
	#Call main function from 'main' module to pass data for processing. Await zonal statistics results
	results = main(start_coord, num_hours, travel_method, country_chosen, population_chosen)
	return jsonify(results) #Return results to the client-side

if __name__ ==  "__main__":
	app.run(host='0.0.0.0', port=5000, debug=True)
