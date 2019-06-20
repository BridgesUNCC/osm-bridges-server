# osm-bridges-server
Repository for the backend processing and handling of OSM data requests for the BRIDGES project

## Setup
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
The first step is to create a python virtual environment within your project the project folder
```bash
python3.6 -m venv venv
```

After creating the python virtual environment run this line to launch the virtual environment
```bash
source venv/bin/activate
```

To launch the flask server first compile the web server
```bash
export FLASK_APP=run.py
```

Finally to launch the web server run 
```bash
flask run --host=0.0.0.0 --port=8080
```
--host signifies that the server should use its default IP when listening for requests

--port is the port that it is listening on, 8080 redirects to port 80
