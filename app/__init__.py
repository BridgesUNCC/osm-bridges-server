
from flask import Flask
from flask import request

app = Flask(__name__)

from app import routes
from app.osm_to_adj import main
