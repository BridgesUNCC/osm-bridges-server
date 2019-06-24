from app import app
from flask import request
import wget
import subprocess
import json
import app.osm_to_adj as osm_to_adj
import app.mapInfo as mapInfo
import os
from datetime import *
import shutil
import sys
import resource
import logging
import time
from apscheduler.schedulers.background import BackgroundScheduler

memPercent = .85

pre_def = '--keep=\"highway=motorway =trunk =primary =secondary =tertiary =unclassified =primary_link =secondary_link =tertiary_link =trunk_link =motorway_link\" --drop-version'

@app.route('/loc')
def namedInput():
    logging.basicConfig(filename='log.log',format='%(asctime)s %(message)s', level=logging.DEBUG)
    logging.info(f"Script started with {request.args['location']} parameters")

    try:
        input_Value = request.args['location']
        if not input_Value.isalpha():
            raise ValueError('A very specific bad thing happened.')
    except:
        print("System arguments are invalid")
        logging.exception(f"System arguements invalid {request.args['location']}")
        return "Invalid arguements"
    #Sets a limit on the amount of memory the script is allowed to use
    #Currently set at 85% of free memory
    #Prevents complete memory usage and crashes due to large map files

    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    resource.setrlimit(resource.RLIMIT_AS, (get_memory() * 1024 * memPercent, hard))

    return pipeline(input_Value)

@app.route('/coords')
def coordsInput():
    logging.basicConfig(filename='log.log',format='%(asctime)s %(message)s', level=logging.DEBUG)
    logging.info(f"Script started with {request.args['minLon']}, {request.args['minLat']}, {request.args['maxLon']}, {request.args['maxLat']} parameters")

    try:
        input_Value = [double(request.args['minLon']), double(request.args['minLat']), double(request.args['maxLon']), double(request.args['maxLat'])]
    except:
        print("System arguements are invalid")
        logging.exception(f"System arguements invalid {request.args['minLon']}, {request.args['minLat']}, {request.args['maxLon']}, {request.args['maxLat']}")
        return "Invalid arguements"

    #Sets a limit on the amount of memory the script is allowed to use
    #Currently set at 85% of free memory
    #Prevents complete memory usage and crashes due to large map files

    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    resource.setrlimit(resource.RLIMIT_AS, (get_memory() * 1024 * memPercent, hard))

    return pipeline(input_Value)

@app.route('/')
def noinput():
    return page_not_found()

@app.errorhandler(404)
def page_not_found(e=''):
    list = "Please request a bounding box or a city name. <br> Available Cities: "
    with open('app/namedList.json', 'r') as x:
        loaded = json.load(x)
        #for city in loaded["named"]:
            #list = list + ", " + city["city"]
    return list

@app.errorhandler(500)
def server_error():
    return "Server Error occured while attempting to process your request"

def call_convert(filename, box=[]):
    """Creates a process of the osmconvert, to shrink the map file down to a bounding box as well as change the file type to .o5m

    Parameters:
    filename(str): String of the file path to the map
    box(list): list of longitude and latitude coordinates

    Returns:
    string: String of the directory that the o5m file was generated in

    """

    try:
        bbox = f"-b=\"{box[0]}, {box[1]}, {box[2]}, {box[3]}\""
        command  = (f"app/osm_converts/osmconvert64 " + filename + " " +  bbox + f" -o=app/o5m_Temp.o5m")
    except:
        command  = (f"app/osm_converts/osmconvert64 " + filename + f" -o=app/o5m_Temp.o5m")


    logging.info(f"Converting {box[0]}, {box[1]}, {box[2]}, {box[3]} map to .o5m")


    try:
        subprocess.run([command], shell=True)
        logging.info("Map Successfully Converted to .o5m")
    except:
        print("Error converting file to .o5m")
        logging.exception(f"Exception occurred while converting bounds: {box[0]}, {box[1]}, {box[2]}, {box[3]}")

    return f"app/o5m_Temp.o5m"

def download_map(url):
    """Uses wget to attempt downloading a map url

    Parameters:
    url(str): String of the URL that the map download is located at

    Returns:
    string: String of the directory location of the map downloaded

    """
    try:
        filename = wget.download(url, out="app/map_files/download")
        print("Map Download Complete")
    except:
        print("Error downloading map")
        logging.exception("Exception occurred while downloading map")
        return
    return filename

def call_filter(o5m_filename):
    """Creates a process of the osmfilter to remove any info that we dont need

    Parameters:
    o5m_filename(str): Name of the file that the the filter will look for

    Returns:
    string: String of the directory that the xml file was generated in
    """

    area = "xml_Temp"

    command = f"app/osm_converts/osmfilter32 {o5m_filename} " + pre_def + f" -o=app/{area}.xml"
    try:
        logging.info(f"Starting osmfilter32 on {o5m_filename}")
        subprocess.run([command], shell=True)
        logging.info("Filtering Complete")
    except:
        print("Error while filtering data")
        logging.exception(f"Exception while filtering data on map: {o5m_filename}")

    return f"app/{area}.xml"

def get_memory():
    '''Retreives current amount of free memory

    Returns:
    int: int of KB of memory free

    '''
    with open('/proc/meminfo', 'r') as mem:
        free_memory = 0
        for i in mem:
            sline = i.split()
            if str(sline[0]) in ('MemFree:', 'Buffers:', 'Cached:'):
                free_memory += int(sline[1])
    return free_memory

def update():
    '''Updates and reduces the root map file'''
    try:
        with open("app/update.json", "r") as f:
            print("Updating maps...")
            loaded = json.load(f)
            os.mkdir("app/map_files/download")
            for sub in loaded["maps"]:
                d = datetime.today()
                #if (d.weekday() == 1 and int(d.strftime("%d")) < 7 and int(d.strftime("%h")) > 1 and int(d.strftime("%h")) < 3):
                try:
                    map_title = sub["map"]

                    print(f"Downloading {map_title} map...")
                    download_map(sub["url"])
                    sub["last-updated"] = date.today().strftime("%Y%m%d")

                except:
                    print("Error Downloading Map")
                    logging.exception(f"Exception occured while downloading map {map_title}")
                    break

                with open("app/update.json", 'w') as f:
                    json.dump(loaded, f, indent=4)

                #filters out info before saving
                try:
                    file_name = sub["file_name"]
                    command  = (f"./app/osm_converts/osmconvert64 app/map_files/download/{file_name} -o=app/o5m_Temp.o5m")
                    subprocess.run([command], shell=True)

                    command = f"./app/osm_converts/osmfilter32 app/o5m_Temp.o5m " + pre_def + f" -o=app/temp.o5m"
                    subprocess.run([command], shell=True)

                    #shutil.rmtree("app/map_files/backup")
                    os.mkdir("app/map_files/download/temp")
                    os.rename("app/map_files/download/" + sub["file_name"], "app/map_files/download/temp/" + sub["file_name"])
                    command  = (f"./app/osm_converts/osmconvert64 app/temp.o5m -o=app/map_files/download/{file_name}")
                    subprocess.run([command], shell=True)

                    os.remove("app/o5m_Temp.o5m")
                    os.remove("app/temp.o5m")

                except:
                    logging.exception("Converting and filtering error")


                os.remove("app/map_files/" + sub["file_name"])
                os.rename("app/map_files/download/" + sub["file_name"], "app/map_files/" + sub["file_name"])

            shutil.rmtree("app/map_files/download")

            #Clears the saved coordinate maps on update call
            shutil.rmtree("app/reduced_maps/coords")
            os.mkdir("app/reduced_maps/coords")

            print("Maps are up-to-date")
    except:
        print("Error reading update file")
        logging.exception("Update file read exception")

def city_gen():
    '''Generates premade cities based on the namedList.json file'''

    start_time = time.time()

    with open('app/namedList.json', 'r') as x:
        logging.info("Checking for pre-defined cities")
        loaded = json.load(x)
        for city in loaded["named"]:
            name = f"app/reduced_maps/named_places/{city['city'].lower()}"
            filename = "app/map_files/north-america-latest.osm.pbf"
            try:
                if (os.path.isfile(f"{name}/map_data.json")):
                    continue
                location = [city["minLon"], city["minLat"], city["maxLon"], city["maxLat"]]
                o5m = call_convert(str(filename), location)
                filename = call_filter(o5m)
                osm_to_adj.main(filename, 0)
                test2 = osm_to_adj.main(filename, 4)
                os.makedirs(name)
                with open(f"{name}/map_data.json", 'w') as x:
                    json.dump(test2, x, indent=4)

                os.remove("app/o5m_Temp.o5m")
                os.remove("app/temp.o5m")

            except:
                logging.exception(f"Error occured while updating pre-defined cities")
    logging.info("Pre-defined cities check complete in %s seconds" % (time.time() - start_time))
    return

def pipeline(location):
    '''The main method that pipelines the process of converting and shrinking map requests

    Parameters:
    location(str or list): A string with a specific locations name, or a list of coordinates[minLon, minLat, maxLon, maxLat] of bounding box

    Returns:
    string: Directory location of new map json created
    '''

    filename = "app/map_files/north-america-latest.osm.pbf"


    #Checks input for name or list
    if type(location) == str:
        location = location.lower()
        name = f"app/reduced_maps/named_places/{location}"
        if (os.path.isfile(f"{name}/map_data.json")):
            print(f"{location} map has already been generated")
            f = open(f"{name}/map_data.json")
            data = json.load(f)
            f.close()
            return  json.dumps(data, sort_keys = False, indent = 2)
        else:
            print ("Please put a location that is supported")
            return page_not_found()

        #o5m = call_convert(str(filename))


    elif type(location) == list:
        #Used to remove extra trailing zeros to prevent duplicates
        location[0] = float(location[0])
        location[1] = float(location[1])
        location[2] = float(location[2])
        location[3] = float(location[3])


        name = f"app/reduced_maps/coords/{location[0]}/{location[1]}/{location[2]}/{location[3]}"
        if (os.path.isfile(f"{name}/map_data.json")):
            print("This coordinate map has already been generated")
            f = open(f'{name}/map_data.json')
            data = json.load(f)
            f.close()
            return  json.dumps(data, sort_keys = False, indent = 2)


        start_time = time.time()
        o5m = call_convert(str(filename), location)
        logging.info("convertosm: %s" % (time.time() - start_time))

    start_time = time.time()
    filename = call_filter(o5m)
    logging.info("filterosm: %s" % (time.time() - start_time))
    #return filename


    #Starts using osm_to_adj.py
    try:
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        resource.setrlimit(resource.RLIMIT_AS, (get_memory() * 1024 * memPercent, hard))
        logging.info(f"Starting OSM to Adj Convert on {filename}")


        #osm_to_adj.main(filename, 0)

        start_time = time.time()
        test2 = osm_to_adj.main(filename, 4)
        logging.info("osm run1: %s" % (time.time() - start_time))
        logging.info("OSM to Adj complete")

        os.makedirs(name)
        with open(f"{name}/map_data.json", 'w') as x:
            json.dump(test2, x, indent=4)
    except MemoryError:
        logging.exception(f"Memory Exception occurred while processing: {name}")


    print("Complete")
    os.remove(o5m)
    os.remove(filename)

    ti = (time.time() - start_time)
    logging.info(f"Map file created with bounds: {location} in {ti} seconds")
    response = json.dumps(test2, sort_keys = False, indent = 2)
    return response

    #return f"{name}/map_data.json"

#Creates a background scheduled task for the map update method
sched = BackgroundScheduler()
sched.daemonic = True
sched.start()

sched.add_job(update, 'cron', day='1st tue', hour='2', misfire_grace_time=None)

sched.print_jobs()
