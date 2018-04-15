/*
 *JavaScript functions to run logic of Accessibility Web-application
 *Created by: David Kerr
 *University of Leeds
 *January 2018
 * NOTE: Geoserver WMS url should be adjusted according to Geoserver instance IP
 *address to which it is requesting data.
 * In most cases, an attempt was made to use JQuery for element selection, however, in some 
 * cases it was not possible, in which case conventional JavaScript DOM interaction was used.
 */

/* Bing key for satellite basemap*/
var apiKey = 'AsITKrfH_sDI9TfdJEl4A-kGG_QqNCaXLe80R_kyLWoyHMgnzpTB1BYxHxDVT1TA';

//URL to access Geoserver layers
var geoserverURL = 'http://172.17.0.2:8080/geoserver/dissertation/wms';

var time_cost_raster_added = false; //Keep false until time_cost_raster_returned from Geoserver. When true, layer will be toggle-able

/*
 * Main function to initialise map and add layers
 */


function initialiseMap() {

	/*OSM tile layer*/
	var OSMTiles = new ol.layer.Tile({
		title: 'Open Street Map',
		source: new ol.source.OSM(),
	});

	/*Bing satellite tile layer*/
	var bingSatellite = new ol.layer.Tile({
		title: 'Bing Satellite',
		source: new ol.source.BingMaps({
			key: apiKey,
			imagerySet: 'AerialWithLabels'
		}),
	});


	/*Layer to hold points with styling*/
	var pointVectorLayer = new ol.layer.Vector ({
		source: new ol.source.Vector ({
		}),
		style: new ol.style.Style ({
			image: new ol.style.Circle ({
				fill: new ol.style.Fill ({
					color: 'red'
				}),
				stroke: new ol.style.Stroke ({
					color: 'black',
					width: 1
				}),
				radius: 6
			})
		})
	});

	//Set point layer to top of stack so always visible
	pointVectorLayer.setZIndex(15);

	/* Map view */
	var view = new ol.View({
		center: ol.proj.fromLonLat([25.4, -1.32]),
		zoom: 4,
		maxZoom: 20
	});

	/*Attribution for overview map*/
	var attribution = new ol.Attribution({
	  html: 'Tiles &copy; <a href="http://services.arcgisonline.com/ArcGIS/' +
		  'rest/services/World_Topo_Map/MapServer">ArcGIS</a>'
	});

	/* On-map controls (zoom, map overview etc) */
	var controls =  ol.control.defaults().extend([
			new ol.control.FullScreen(),
			new ol.control.MousePosition({
				coordinateFormat: ol.coordinate.createStringXY(2),
				projection: 'EPSG:4326'
			}),
			new ol.control.OverviewMap({
				collapsed: false, 
				collapsible: false,
				className: 'ol-overviewmap ol-custom-overviewmap',
				layers: [
					new ol.layer.Tile({
						source: new ol.source.XYZ({
							url: 'http://server.arcgisonline.com/ArcGIS/rest/services/' +
								'World_Topo_Map/MapServer/tile/{z}/{y}/{x}'
						})
					})
					],
				attibutions: [attribution]
			}),
			new ol.control.ScaleLine(),
			new ol.control.ZoomSlider(),
		]);


	/*Add slider to control the opacity of the satellite layer in order to see the OSM layer*/
	var $opacity = $('#js-opacity');

	$('#js-slider').slider({
		min: 0,
		max: 100,
		value: 100,
		slide: function(event, ui) {
			$opacity.text(ui.value + '%');
			map.getLayers().item(1).setOpacity(ui.value / 100);
		}
	});


	/*Create a list of layers to be added to the map */
	var mapLayers = [OSMTiles, bingSatellite, pointVectorLayer];
	
	/* Instantiate the map */
	var map = new ol.Map({
		target: 'map',
		layers: mapLayers,
		view: view,
		controls: controls,
		interactions : ol.interaction.defaults({doubleClickZoom :false}),	
	});




	/************************************CODE TO ADD LAYERS FROM POSTGIS/GEOSERVER *********************************/
	/*+++++++++++++++++++++++++++++++++++++++++COUNTRY SELECT+++++++++++++++++++++++++++++++++++++++++++++++++++*/
	//Global variable to hold user selections
	var country_L1;
	var country_selected = false;
	var country;

	/*
	* Function to listen for country selection to be made by user and request
	* that country's borders from Geoserver,
	* add it to the map and zoom to country's extent.
	*/
	$(document).ready(function() {
		$("#country_select").on('change',function() {
			country = $(this).find("option:selected").attr("id");
			if (country != "none_chosen") {
				country_selected = true;		//Ensure country is selected and change Boolean
			} else {
				country_selected = false;
			};
			var layer = 'dissertation:' + country;	//Create variable of country chosen for WMS
			if (country_L1) {
				map.removeLayer(country_L1);	//If other countries have been selected previously, remove them 
				map.removeLayer(pop_raster);
				$("#raster_select").get(0).selectedIndex = 0;
			};
			//Make WMS request for boundary
			country_L1 = new ol.layer.Tile({
				source: new ol.source.TileWMS({
					url: geoserverURL,
					params: {'FORMAT': 'image/png', 
		                   'VERSION': '1.1.1',
		                   tiled: true,
		                STYLES: '',
		                LAYERS: layer,
		          }
				})
			});
			map.addLayer(country_L1);
			country_L1.setZIndex(100);	//Add layer to map and set it as the top layer.

				//Zoom to country's extent
				view.animate({
					source: map.getView().getCenter(),
					duration: 550,
					easing: ol.easing.easeIn
				});

			//Zoom to Benin
			if (country == "ben_adm1") {
				map.getView().fit([252042, 686304, 594234, 1376387], map.getSize());
			};

			////Zoom to Nigeria
			if (country == "nga_adm1") {
				map.getView().fit([456541, 466712, 471532, 1541119], map.getSize());
			};
			////Zoom to Cameroon
			if (country == "cmr_adm1") {
				map.getView().fit([440045, 176319, 633266, 1452336], map.getSize());
			};
			////Zoom to Niger
			if (country == "ner_adm1") {
				map.getView().fit([1295517.28511,9696.27051521, 2625378.15168,1813385.38075], map.getSize());
			};
			////Zoom to South Africa
			if (country == "zaf_adm1") {
				map.getView().fit([1822265.97337,-4150121.92933, 3670587.63108,-2518908.1929], map.getSize());
			};
			////Zoom to Zambia
			if (country == "zmb_adm1") {
				map.getView().fit([2442443.11049,-2052624.00459, 3758618.03331,-913149.932948], map.getSize());
			};
			////Zoom to Chad
			if (country == "tcd_adm1") {
				map.getView().fit([819425.273343,1507852.2185, 2619393.98167,2760152.26035], map.getSize());
			};
		});
	});	
	/*+++++++++++++++++++++++++++++++++++++++++COUNTRY SELECT+++++++++++++++++++++++++++++++++++++++++++++++++++*/

	/*****************************************ADD POPULATION RASTER *********************************************/
	//Global variable to hold user selections
	var pop_raster;
	var raster_selected = false;


	/*
	* Function to listen for demographic group selection to be made by user and 
	* request the chosen demographic group's raster from Geoserver,
	* add it to the map
	*/
	$(document).ready(function() {
		$("#raster_select").on('change', function() {
			if (!country_selected) {
				alert("Please first select a country");		//Message to alert no country selected
			} 
			if (pop_raster) {
				map.removeLayer(pop_raster);				//Remove previous countries' rasters
			};

			var raster_layer = country.slice(0,-5).toUpperCase() + $("#raster_select").find("option:selected").attr("id");

			if ($("#raster_select").find("option:selected").attr("id") != "no_pop_chosen") {
				raster_selected = true;
			} else {
				raster_selected = false;		//Ensure demographic group is chosen before making request
			};
			//Make Geoserver WMS request
			pop_raster = new ol.layer.Tile({
				source: new ol.source.TileWMS({
					url: geoserverURL,
					params: {'FORMAT': 'image/png',
							'VERSION': '1.1.1',
							tiled: true,
							STYLES: '',
							LAYERS: raster_layer
						}
				})
			});
			//Add layer and legend.  
			map.addLayer(pop_raster);
			$("#legend").css('visibility', 'visible'); //Make legend visible
			$("#population_raster").attr('disabled', false); //Enable legend for selection
		});
	});
	/**********************************ADD POPULATION RASTER***********************************************/

	/******************************ADD IMPEDANCE SURFACE RASTER *********************************************/
	//Global variable to hold user selections
	var impedance_raster;
	var impedance_selected = false;


	/*
	* Function to listen for mode of transport selection to be made by user and 
	* request that mode's raster from Geoserver,
	* add it to the map.
	*/
	$(document).ready(function() {
		$("#impedance_select").on('change', function() {
			if (!country_selected) {
				alert("Please first select a country");	//Message to alert no country selected
			} 
			if (impedance_raster) {
				map.removeLayer(impedance_raster);		//Remove previous countries' rasters
			};

			var impedance_layer = country.slice(0,-5).toUpperCase() + "_friction";

			if ($("#impedance_select").find("option:selected").attr("id") != "no_trans_chosen") {
				raster_selected = true;
			} else {
				raster_selected = false; 				//Esure mode of transport is selected before making request
			};
			//Make Geoserver WMS request
			impedance_raster = new ol.layer.Tile({
				source: new ol.source.TileWMS({
					url: geoserverURL,
					params: {'FORMAT': 'image/png',
							'VERSION': '1.1.1',
							tiled: true,
							STYLES: '',
							LAYERS: impedance_layer						}
				})
			});
			//Add layer and legend.
			map.addLayer(impedance_raster);
			$("#travel_time_raster").attr('disabled', false);	//Enable legend for selection
		});
	});

	/******************************ADD IMPEDANCE SURFACE RASTER *********************************************/


	/* BUTTON TO Remove points using overlay */
	var delOverlay = new ol.Overlay({
		element: document.getElementById("js-overlay")
	});

	map.addOverlay(delOverlay);
	document.getElementById("js-overlay").style.display = "block";

	var selectedFeature;
	//Select/highlight the clicked point
	var pointSelect = new ol.interaction.Select({
		condition: ol.events.condition.click,
	 	layers: [pointVectorLayer]
	});
	map.addInteraction(pointSelect);

	//Pass position of point to function to add button to its postion
	pointSelect.on('select', function(event) {
	 	selectedFeatureCoord = event.mapBrowserEvent.coordinate;
	 	selectedFeature = event.selected[0];
	 	(selectedFeature) ?
	 		delOverlay.setPosition(selectedFeatureCoord) :
	 		delOverlay.setPosition(undefined);
	});
	//Remove clicked point
	document.getElementById('js-remove').addEventListener('click', function() {
    	pointVectorLayer.getSource().removeFeature(selectedFeature);
    	delOverlay.setPosition(undefined);
    	pointSelect.getFeatures().clear();
	});


	/*Array in which to store newly added points from file uploaded by user*/
	var pointCoords = [];

	/*
	* Function to allow the uploading of a file. If it is a latlong CSV, each 
	* coordinate pair is passed into an array, which is added to the pointCoords array
	* which will be processed outside of the function and added to the map
	*/
	$(document).ready(function() {
		$('#files').on('change', function() {
			var file = $('#files')[0].files[0];
			if (!file) {
				alert('PLease select a file');
				return;
			}
			var start = 0;
			var stop = file.size -1;

			var reader = new FileReader();
			reader.readAsText(file);
			reader.onloadend = function(evt) {
				if (evt.target.readyState == FileReader.DONE) {
					var text = evt.target.result;	 
					var lines = text.split("\n");
					for (var i=0; i<lines.length -1; i++){
						var element = lines[i].split(",");
						var latx = parseFloat(element[0]);
						var lony = parseFloat(element[1]);
						var pointCoord = [latx, lony];
						pointCoords.push(pointCoord);						
					}
					window.alert("Click points and 'Remove' button to delete points");
					for (var j = 0; j < pointCoords.length; j++) {
						var latitude = pointCoords[j][0];
						var longitude = pointCoords[j][1];
						var point = new ol.geom.Point(ol.proj.transform(pointCoords[j], 'EPSG:4326', 'EPSG:3857'));
						var featurePoint = new ol.Feature({
							name: "Point",
							geometry: point
						});
						pointVectorLayer.getSource().addFeature(featurePoint);											
					}
				}
			}
		});

	}); // End of function to add points via upload

	//Function to manually add points by double-clicking on map when button is clicked
	$("button#add-points").on('click', function() {
	 	window.alert("Double click on map to add points. Click point and 'Remove' button to delete points");
			map.on('dblclick', function(event) {
				var latLon = event.coordinate
				var point = new ol.geom.Point(latLon);
				var featurePoint = new ol.Feature({
					name: "Point",
					geometry: point
				});
				pointVectorLayer.getSource().addFeature(featurePoint);
			});		
	}); //End of function to app points manually

	/*
	 * Function to post variables and data to server-side for processing. When response is received
	 * a table is created and filled with data and displayed (via toggle button) on screen.
	 * Output raster also requested from Geoserver and displayed
	 */
	$('#postPoints').click(function() {
		var time_travel = parseFloat($("#time_travel").val());
		if(time_travel == "") {
			time_travel = parseFloat(2);
		}
		var travel_method = $("#impedance_select").find("option:selected").attr("id");
		var country_chosen = country;
		var population_chosen = $("#raster_select").find("option:selected").attr("id");
		var features = pointVectorLayer.getSource().getFeatures();
		var pointsArray = [];
		features.forEach(function(feature){
	 		pointsArray.push(ol.proj.transform(feature.getGeometry().getCoordinates(), 'EPSG:3857', 'EPSG:4326'));	//Project points to WGS84
	 	});
	 	$('.loading-overlay').show();	//Show spinning loading wheel
		$('#interface *').attr('disabled', true);	//Disable further input while processing
		//Post to server as JSON
		$.ajax({
 			data: JSON.stringify({
 				'array' : pointsArray, 
 				'time_travel': time_travel,
 				'travel_method': travel_method,
 				'country_chosen': country_chosen,
 				'population_chosen': population_chosen
 			}),
 			contentType: "application/json; charset=utf-8",
 			type: 'POST',
 			url: '/process',
 			success: function(response) {
				makeTable(JSON.parse(response));
				$('.loading-overlay').hide();	//Remove spinning loading wheel
				$('#interface *').attr('disabled', false); //Enable interface for interaction
			}
 		}) //End of Post request

	}); //End of function to send and receive data

	//Function to display output, called in previous function
	function makeTable(response){
		if ($('#myTable').length){ 
			$('#resultsPanel').html(""); //Clear previous table if present
			map.removeLayer(time_cost_raster); //Remove previous output raster if present
		}
		var travel_time = $('#time_travel').val();
		var demographic_group = $("#raster_select").find("option:selected").text();
		if (demographic_group == "Women of child-bearing age"){
			demographic_group = "WOCBA";
		};
		//Create table
		var tbl = $("<table/>").attr("id", "myTable");
		//Table headings
		var table_title = "<p><b>" + demographic_group + " accessibility to health facilities</b></p>"
		var head1 = "<tr><th>State</th><th>Total " + demographic_group + "</th><th>" + demographic_group + " inside " + travel_time +"hrs</th><th>" + demographic_group + " outside " + travel_time + "hrs</th><th>% \
		 with access</th></tr>";
		$("#resultsPanel").append(table_title);
		$("#resultsPanel").append(tbl);
		$("#resultsTable").css('visibility', 'visible');	//Make table visible
		$("#myTable").append(head1);
		for (var i = 0; i < response.length; i++) {
			var state_name = response[i][0].travel_in_state;
			var total_population = Number(response[i][0].total_pop).toFixed(0);
			var pop_inside = (Number(response[i][0].pop_inside_2hrs).toFixed(0)	== 0 ? 0 : Number(response[i][0].pop_inside_2hrs).toFixed(0));
			var pop_outside = (Number(response[i][0].pop_inside_2hrs).toFixed(0) == 0 ? total_population : Number(response[i][0].pop_outside_2hrs).toFixed(0));
			//var percent_without = (Number(response[i][0].pop_inside_2hrs).toFixed(0) \
			//	== 0 ? 100 : Number(response[i][0].percent_without_access).toFixed(2));
			var percent_with = (Number(response[i][0].pop_inside_2hrs).toFixed(0) == 0 ? 100 : (100 - Number(response[i][0].percent_without_access)).toFixed(2));
			//Add data to cells in the table
			var tr = "<tr>";
			var td0 = "<td class='state'>" + state_name + "</td>"
			var td1 = "<td>" + Number(total_population).toLocaleString() + "</td>"
			var td2 = "<td>" + Number(pop_inside).toLocaleString() + "</td>"
			var td3 = "<td>" + Number(pop_outside).toLocaleString() + "</td>"
			var td4 = "<td>" + percent_with + "</td></tr>"
			$("#myTable").append(tr + td0 + td1 + td2 + td3 + td4);
		};
		//Request output raster from Geoserver
		time_cost_raster = new ol.layer.Tile({
			source: new ol.source.TileWMS({
				url: geoserverURL,
				params: {'FORMAT': 'image/png',
						'VERSION': '1.1.1',
						tiled: true,
						STYLES: '',
						LAYERS: 'time-cost-raster'
					}
			})
		}); //Finihsed function to request raster from Geoserver
		map.addLayer(time_cost_raster);
		time_cost_raster_added = true;
		$("#time_cost_raster").attr('disabled', false); //Add raster to map and enable interaction with raster legend		}
	}; //End of function to display output


	//Function to change layers' order for users' preference and display legends
	$(document).ready(function() {
 		$('input[type=radio][name=optradio]').change(function() {
			if (this.id == 'population_raster') {
				pop_raster.setVisible(true);
				pop_raster.setZIndex(10); //Put layer on top				
				if (time_cost_raster == true) {
					time_cost_raster.setZIndex(0);
				};
				if (impedance_raster) {
					impedance_raster.setZIndex(0);
				}
				makeLegendBins('population_raster');
			};
			if (this.id == 'travel_time_raster') {
				impedance_raster.setVisible(true);
				impedance_raster.setZIndex(10); //Put layer on top
				if (pop_raster) {
					pop_raster.setZIndex(0);
				};
				if (time_cost_raster == true) {
					time_cost_raster.setZIndex(0);
				}
				makeLegendBins('travel_time_raster');
			};
			if (this.id == 'time_cost_raster') {
				time_cost_raster.setVisible(true);
				time_cost_raster.setZIndex(10); //Put layer on top
				if (impedance_raster) {
					impedance_raster.setZIndex(0);
				}
				if (pop_raster) {
					pop_raster.setZIndex(0);
				}
				makeLegendBins('time_cost_raster');
			};
			//Remove all rasters and legends
			if (this.id == 'remove_rasters') {
				pop_raster.setVisible(false);
				impedance_raster.setVisible(false);
				/*if (pop_raster) {
					pop_raster.setVisible(false);
				}
				if (impedance_raster) {
					impedance_raster.setVisible(false);
				}*/
				if (time_cost_raster_added == true) {
					time_cost_raster.setVisible(false);
				}
				$("#legend_bins").html(""); //Delete legend of current map
			};
		});
	});

	//Function to dynamically make legends according to input raster pixel values - called by above function
	function makeLegendBins(input_raster) {
		var population_raster_colours = ["#ffffcc", "#a1dab4", "#41b6c4", "#2c7fb8", "#253494"];
		var population_raster_bins = ["0-4", "4-7", "7-10", "10-14", ">14"];
		var travel_time_raster_colours = ["#ca0020", "#eb846e", "#f5d6c8", "#cee3ed", "#75b4d4", "#0571b0"];
		//Set impedance raster road values according to method of transport
		if ($("#impedance_select").find("option:selected").attr("id") == "walking") {
			var roadSpeed = "12";
		} else if ($("#impedance_select").find("option:selected").attr("id") == "cycling") {
			var roadSpeed = "4";
		} else {
			var roadSpeed = "1";
		};		
		var travel_time_raster_bins = [roadSpeed, "6", "24", "36", "48", "60"];
		var time_cost_raster_colours = ["#1a9641", "#58b353", "#96d165", "#c3e586", "#ebf6ac", "#feedaa", "#fdc980", "#f89d59", "#e75b3a", "#d7191c"];
		var timeTravel = parseFloat($("#time_travel").val()).toFixed(2);
		var greaterThan = ">";
		var time_cost_raster_bins = ["0", ((timeTravel/4).toFixed(2)).toString(),((timeTravel/3).toFixed(2)).toString(), ((timeTravel/2).toFixed(2)).toString(),(timeTravel).toString(), (timeTravel * 2).toString(), (timeTravel * 3).toString(), (timeTravel * 4).toString(), (timeTravel * 5).toString(), greaterThan.concat(((timeTravel * 6).toFixed(2)).toString())];
		var col_str = "_colours";
		var bin_str = "_bins";
		var colour = eval(input_raster.concat(col_str));
		var bin_range = eval(input_raster.concat(bin_str));
		if (input_raster == 'population_raster'){
			extraString = ' per grid square';
		} else if (input_raster == 'travel_time_raster') {
			extraString = ' minutes per Km';
		} else {
			extraString = ' hour(s) from facility';
		}
		var html = '<h5>Legend</h5><ul class="legend_list" style="list-style-type: none; padding-left:5px;">';
		for (var i = 0; i < colour.length; i++ ) {
			html += '<li><i style="background: ' + colour[i] + '"></i>' + bin_range[i] + extraString + '</li>'
		};
		html += '</ul>';
		$("#legend_bins").html(html);
	}; //End of function to make legends and bins

	//Instructions modal popup window
	$("#showInstructions").click(function() {
		var modal = $(".modal");
		var span = $(".close")[0];
		$(".modal").css('display', 'block');
		span.onclick = function() {
		    $(".modal").css('display', 'none');
		}
		$('#closeInstructions').on('click', function() {
			$(".modal").css('display', 'none');
		});
	}); //End of modal popup window
};//End of initialiseMap()