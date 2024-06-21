# osm-bridges-server
Repository for the backend processing and handling of OSM data requests for the BRIDGES project

## Setup

Create a python 3.8 virtual environment. It works also with a 3.6
environment. But likely not a 3.10 environment and further. And reset
the pip packages in the environment from `requirements.txt`.

```bash
$ /opt/python-3.8.10/bin/python3 -m venv myvenv
$ . ./myvenv/bin/activate
$ pip install -r requirements.txt
```

## Launching Flask Server

(Assuming you have activated the environment first. )

Step 1: To launch the flask server first compile the web server
```bash
$ export FLASK_APP=run.py
```

Step 2: Launch the web server 
```bash
$ flask run --host=0.0.0.0 --port=8080
```
--host signifies that the server should use its default IP when listening for requests

--port is the port that it is listening on, the server will be listening on port 8080, unless the server configuration for 8080 redirects to port 80
