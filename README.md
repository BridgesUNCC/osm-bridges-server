# osm-bridges-server
Repository for the backend processing and handling of OSM data requests for the BRIDGES project

## Setup
This is a UNIX based server and can only run on such systems due to UNIX only dependencies.
If running on Centos 7 execute the python_setup.sh file.
```bash
sudo ./python_setup
```
This file holds all the commands to download the required python version and python repositories

If you are running a different version of linux run these commands to download Python 3.6
```bash
sudo add-apt-repository ppa:jonathonf/python-3.6
sudo apt-get update
sudo apt-get install python3.6
sudo apt-get install python3.6-pip
sudo apt install python3.6-dev
```
To download the required python libraries run the following commands
```bash
sudo python3.6 -m pip install flask
sudo python3.6 -m pip install wget
sudo python3.6 -m pip install apscheduler
sudo python3.6 -m pip install virtualenv
```

## Launching Flask Server
(Optional)
The first step is to create a python virtual environment within your project the project folder
```bash
python3.6 -m venv venv
```
(Optional)
After creating the python virtual environment run this line to launch the virtual environment
```bash
source venv/bin/activate
```

Step 1: To launch the flask server first compile the web server
```bash
export FLASK_APP=run.py
```

Step 2: Launch the web server 
```bash
flask run --host=0.0.0.0 --port=8080
```
--host signifies that the server should use its default IP when listening for requests

--port is the port that it is listening on, the server will be listening on port 8080, unless the server configuration for 8080 redirects to port 80


## Making Queries
To make queries with the server you require two pieces of information, first the bounding box (or city, state) of the area you want returned, and second the filter parameter you want. The both queries can either take in a bounding box of cordinates or a city name and state. 
* Bounding Box
  * minLon
  * minLat
  * maxLon
  * maxLat

* City, State
  * City, State
  
### Map Queries

Map with Bounding Box
```
http://cci-bridges-osm.uncc.edu/coords?minLon=23.6435&minLat=32.4532&maxLon=64.231&maxLat=34.2344&level=default
```

Map with City Name
```
http://cci-bridges-osm.uncc.edu/loc?location=Chicago, Illinois&level=default
```
To view a list of possible cities visit and the format they should be in visit
[City List](http://cci-bridges-osm.uncc.edu/cities)

* Possible Filtering Values
  * motorway
  * trunk (includes the above too)
  * primary (includes the above too)
  * secondary (includes the above too)
  * tertiary (includes the above too)
  * unclassified (includes the above too)
  * residential (includes the above too)
  * living_street (includes the above too)
  * service (includes the above too)
  * trails
  * walking (includes trails)
  * bicycle (includes tertiary, unclassified, residential and living_street)

If no filter value is given a default value will be used, this default is equivalent to 'unclassified'

### Amenity Queries

Query with Bounding Box
```
http://cci-bridges-osm.uncc.edu/amenity?minLon=23.6435&minLat=32.4532&maxLon=64.231&maxLat=34.2344&amenity=food
```
Query with City, State
```
http://cci-bridges-osm.uncc.edu/amenity?city=Chicago,%20Illinois&amenity=food
```
*(Note) The '%20' is used to represent a space*

* Possible Filtering Values
  * food
  * school
  * firestation
  * airport
  * heli
  
## Data Format Returned
### OSM
```json
{  
  "nodes": [
    [
      31843386,
      39.1846873,
      -76.8962161
    ],
    [
      31843411,
      39.1844418,
      -76.8964387
    ],
    [
      31843417,
      39.183929,
      -76.8965795
    ]
  ],
  "edges": [
    [
      31843386,
      37190373,
      269.98552269243726
    ],
    [
      31843411,
      37190432,
      210.00120973373004
    ],
    [
      31843417,
      1256047296,
      50.68643531552827
    ]
  ],
  "meta": {
    "lat_min": 39.1210027,
    "lat_max": 39.2079898,
    "lon_min": -77.054985,
    "lon_max": -76.8050138,
    "name": "temp_map"
  }
}
```

### Amenities
node format
```
[
   id
   lat
   lon
   name
   amenity
   FAA (Airport Only)
   IATA (Airport Only)
   ICAO (Airport Only)
]

```
______________________________
```json
{
    "nodes": [
        [
            368381033,
            39.9502553,
            -80.7593715,
            "Glendale Fokker Field",
            "aerodrome",
            null,
            "GWV",
            null
        ],
        [
            368381053,
            39.8811867,
            -80.7356412,
            "Marshall County Airport",
            "aerodrome",
            "MPG",
            null,
            "KMPG"
        ],
        [ ... ]
    ],
    "meta": {
        "count": 127,
        "minlat": 39.0611,
        "minlon": -84.6151,
        "maxlat": 41.8525,
        "maxlon": -80.6106
    }
}
```

## Examples Parameters

### OSM
- "Chicago, Illinois", "default"
- -77.055, 39.121, -76.805, 39.208, "default"
- -73.9225, 40.7866, -74.0625, 40.6809, "default"

### Amenities
- "Chicago, Illinois", "bar,atm,school"
- "-80.97006, 35.08092, -80.6693, 35.3457, "food"
- "-111.6869, 33.6906, -112.2718, 33.3213, "school"

