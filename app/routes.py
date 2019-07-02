from app import app
from flask import request
import wget
import subprocess
import json
import app.osm_to_adj as osm_to_adj
import os
from datetime import *
import shutil
import sys
import resource
import logging
import time
import hashlib
from apscheduler.schedulers.background import BackgroundScheduler

memPercent = .85 # % of RAM allowed for osm_to_adj.py to use
degreeRound = 4 #number of decimal places to round bounding box coords too

default = '--keep=\"highway=motorway =trunk =primary =secondary =tertiary =unclassified =primary_link =secondary_link =tertiary_link =trunk_link =motorway_link\" --drop-version'
map_convert_command = '--keep=\"highway=motorway =trunk =primary =secondary =tertiary =unclassified =primary_link =secondary_link =tertiary_link =trunk_link =motorway_link\" --drop-version'
motorway = '=motorway =motorway_link'
trunk = ' =trunk =trunk_link'
primary = ' =primary =primary_link'
secondary = ' =secondary =secondary_link'
tertiary = ' =tertiary =tertiary_link'
unclassified = ' =unclassified'

divider = "-----------------------------------------------------------------"

@app.route('/loc')
def namedInput():

    try:
        input_Value = request.args['location']
        logging.info(divider)
        logging.info(f"Requester: {request.remote_addr}")
        logging.info(f"Script started with {request.args['location']} parameters")
        if not input_Value.isalpha():
            raise ValueError()
    except:
        print("System arguments are invalid")
        logging.exception(f"System arguements invalid {request.args['location']}")
        return "Invalid arguements"

    try:
        if (request.args['level'].lower() == 'motorway' or request.args['level'].lower() == 'trunk' or request.args['level'].lower() == 'primary' or request.args['level'].lower() == 'secondary' or request.args['level'].lower() == 'tertiary' or request.args['level'].lower() == 'unclassified'):
            level = str(request.args['level'])
            logging.info(f"Script using street detail level of: {request.args['level']}")
        else:
            level = "default"
            logging.info(f"Script using street detail level of default (full detail)")
    except:
        level = "default"
        logging.info(f"Script using street detail level of default (full detail)")



    try:
        coords = city_coords(input_Value)
        if (coords != 404):
            return pipeline(coords, level, input_Value.lower())
        else:
            return page_not_found()
    except:
        logging.info(f"Error occured while looking up city: {input_Value}")
        return server_error()

@app.route('/coords')
def coordsInput():

    try:
        #rounds and converts the args to floats and rounds to a certain decimal
        input_Value = [round(float(request.args['minLon']), degreeRound), round(float(request.args['minLat']), degreeRound), round(float(request.args['maxLon']), degreeRound), round(float(request.args['maxLat']), degreeRound)]
        logging.info(divider)
        logging.info(f"Requester: {request.remote_addr}")
        logging.info(f"Script started with Box: {request.args['minLon']}, {request.args['minLat']}, {request.args['maxLon']}, {request.args['maxLat']} bounds")
    except:
        print("System arguements are invalid")
        logging.exception(f"System arguements invalid {request.args}")
        return "Invalid arguements"

    try:
        if (request.args['level'].lower() == 'motorway' or request.args['level'].lower() == 'trunk' or request.args['level'].lower() == 'primary' or request.args['level'].lower() == 'secondary' or request.args['level'].lower() == 'tertiary' or request.args['level'].lower() == 'unclassified'):
            level = str(request.args['level'])
            logging.info(f"Script using street detail level of: {request.args['level']}")
        else:
            level = "default"
            logging.info(f"Script using street detail level of default (full detail)")
    except:
        level = "default"
        logging.info(f"Script using street detail level of default (full detail)")

    return pipeline(input_Value, level)

@app.route('/hash')
def hashreturn():
    type = None
    try:
        loc = str(request.args['location']).lower()
        input_Value = city_coords(loc)
        type = "loc"
        logging.info(divider)
        logging.info(f"Requester: {request.remote_addr}")
        logging.info(f"Hash checking for map with bounds: {input_Value[0]}, {input_Value[1]}, {input_Value[2]}, {input_Value[3]}")
    except:
        try:
            #rounds and converts the args to floats and rounds to a certain decimal
            input_Value = [round(float(request.args['minLon']), degreeRound), round(float(request.args['minLat']), degreeRound), round(float(request.args['maxLon']), degreeRound), round(float(request.args['maxLat']), degreeRound)]
            type = "coord"
            logging.info(divider)
            logging.info(f"Requester: {request.remote_addr}")
            logging.info(f"Hash checking for map with bounds: {input_Value[0]}, {input_Value[1]}, {input_Value[2]}, {input_Value[3]}")
        except:
            print("System arguements for hash check are invalid")
            logging.exception(f"System arguements for hash check invalid {request.args['minLon']}, {request.args['minLat']}, {request.args['maxLon']}, {request.args['maxLat']}")
            return "Invalid arguements"

    try:
        x = request.args['level'].lower()
        if (x == 'motorway' or x == 'trunk' or x == 'primary' or x == 'secondary' or x == 'tertiary' or rx == 'unclassified'):
            level = str(x)
        else:
            level = "default"
    except:
        level = "default"


    if (type == "loc"):
        dir = f"app/reduced_maps/cities/{loc}/{level}"
    elif (type == "coord"):
        dir = f"app/reduced_maps/coords/{input_Value[0]}/{input_Value[1]}/{input_Value[2]}/{input_Value[3]}/{level}"
    else:
        return page_not_found()



    try:
        with open(f"{dir}/hash.txt", 'r') as f:
            re = f.readlines()
            logging.info(f"Hash value found: {re[0]}")
            return re[0]
    except:
        print("No map hash found")
        return "false"

@app.route('/')
def noinput():
    return page_not_found()

@app.errorhandler(404)
def page_not_found(e=''):
    return 404

@app.errorhandler(500)
def server_error():
    return "Server Error occured while attempting to process your request. Please try again..."

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
        start_time = time.time()
        subprocess.run([command], shell=True)
        logging.info("Map Successfully Converted to .o5m in: %s" % (time.time() - start_time))
    except:
        print("Error converting file to .o5m")
        logging.exception(f"Exception occurred while converting bounds: {box[0]}, {box[1]}, {box[2]}, {box[3]}")

    return f"app/o5m_Temp.o5m"

def call_filter(o5m_filename, level):
    """Creates a process of the osmfilter to remove any info that we dont need

    Parameters:
    o5m_filename(str): Name of the file that the the filter will look for

    Returns:
    string: String of the directory that the xml file was generated in
    """

    area = "xml_Temp"

    para = "--keep=\"highway"

    if (level == "motorway"):
        para = para + motorway
    elif (level == "trunk"):
        para = para + motorway + trunk
    elif (level == "primary"):
        para = para + motorway + trunk + primary
    elif (level == "secondary"):
        para = para + motorway + trunk + primary + secondary
    elif (level == "tertiary"):
        para = para + motorway + trunk + primary + secondary + tertiary
    elif (level == "unclassified"):
        para = para + motorway + trunk + primary + secondary + tertiary + unclassified

    para = para + "\" --drop-version"

    if (level == "default"):
        para = default

    command = f"app/osm_converts/osmfilter {o5m_filename} " + para + f" -o=app/{area}.xml"
    try:
        start_time = time.time()
        logging.info(f"Starting osmfilter on {o5m_filename} with filter command level {level}")
        subprocess.run([command], shell=True)
        logging.info("Filtering Complete in: %s" % (time.time() - start_time))
    except:
        print("Error while filtering data")
        logging.exception(f"Exception while filtering data on map: {o5m_filename}")

    return f"app/{area}.xml"

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

                    command = f"./app/osm_converts/osmfilter app/o5m_Temp.o5m " + map_convert_command + f" -o=app/temp.o5m"
                    subprocess.run([command], shell=True)

                    os.mkdir("app/map_files/download/temp")
                    os.rename("app/map_files/download/" + sub["file_name"], "app/map_files/download/temp/" + sub["file_name"])
                    command  = (f"./app/osm_converts/osmconvert64 app/temp.o5m -o=app/map_files/download/{file_name}")
                    subprocess.run([command], shell=True)

                    os.remove("app/o5m_Temp.o5m")
                    os.remove("app/temp.o5m")

                except:
                    logging.exception("Converting and filtering error")


                if (os.path.isfile("app/map_files/" + sub["file_name"])):
                    os.remove("app/map_files/" + sub["file_name"])
                os.rename("app/map_files/download/" + sub["file_name"], "app/map_files/" + sub["file_name"])

            shutil.rmtree("app/map_files/download")

            #Clears the saved coordinate maps on update call
            shutil.rmtree("app/reduced_maps/coords")
            os.mkdir("app/reduced_maps/coords")

            print("Maps are up-to-date")
    except Exception as e:
        logging.exception("Update file read exception" + e)

def city_gen():
    '''Generates premade cities based on the namedList.json file'''

    start_time = time.time()

    with open('app/namedList.json', 'r') as x:
        logging.info("Checking for pre-defined cities")
        loaded = json.load(x)
        for city in loaded["named"]:
            name = f"app/reduced_maps/cities/{city['city'].lower()}"
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

def city_coords(location):
    coord = None
    try:
        with open('app/cities.json', 'r') as x:
            loaded = json.load(x)
            for city in loaded:
                if (city["city"].lower() == location):
                        minLat = round(city['latitude'] - .25, degreeRound)
                        minLon = round(city['longitude'] - .25, degreeRound)
                        maxLat = round(city['latitude'] + .25, degreeRound)
                        maxLon = round(city['longitude'] + .25, degreeRound)
                        coord = [minLat, minLon, maxLat, maxLon]
                        return coord
        if (coord == None):
            print ("Please put a location that is supported")
            return page_not_found()
    except Exception as e:
        logging.info(e)

def pipeline(location, level, cityName = None):
    '''The main method that pipelines the process of converting and shrinking map requests

    Parameters:
    location(str or list): A string with a specific locations name, or a list of coordinates[minLon, minLat, maxLon, maxLat] of bounding box

    Returns:
    string: Directory location of new map json created
    '''

    filename = "app/map_files/north-america-latest.osm.pbf" # NA map file directory


    #Checks input for name or list
    if cityName is not None :
        location[0] = float(location[0]) #minLat
        location[1] = float(location[1]) #minLon
        location[2] = float(location[2]) #maxLat
        location[3] = float(location[3]) #maxLon
        print(location)
        dir = f"app/reduced_maps/cities/{cityName}/{level}"
        if (os.path.isfile(f"{dir}/map_data.json")):
            logging.info(f"{cityName} map has already been generated")
            f = open(f"{dir}/map_data.json")
            data = json.load(f)
            f.close()
            return  json.dumps(data, sort_keys = False, indent = 2)



    elif cityName == None:
        #Used to remove extra trailing zeros to prevent duplicates
        #might be redundent
        location[0] = float(location[0]) #minLat
        location[1] = float(location[1]) #minLon
        location[2] = float(location[2]) #maxLat
        location[3] = float(location[3]) #maxLon

        # minLat / minLon / maxLat / maxLon
        dir = f"app/reduced_maps/coords/{location[0]}/{location[1]}/{location[2]}/{location[3]}/{level}"
        if (os.path.isfile(f"{dir}/map_data.json")):
            logging.info("The map was found in the servers map storage")
            f = open(f'{dir}/map_data.json')
            data = json.load(f)
            f.close()
            return  json.dumps(data, sort_keys = False, indent = 2) #returns map data from storage

    #Map Convert Call, converts the large NA map to that of the bounding box
    o5m = call_convert(str(filename), location)

    #Map Filter Call, filters out any data that is not required withing the level requested
    filename = call_filter(o5m, level)


    #Starts using osm_to_adj.py
    try:
        #Sets memory constraints on the program to prevent memory crashes
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        resource.setrlimit(resource.RLIMIT_AS, (get_memory() * 1024 * memPercent, hard))
        logging.info(f"Starting OSM to Adj Convert on {filename}")


        start_time = time.time() #timer to determine run time of osm_to_adj
        test2 = osm_to_adj.main(filename, 4) #reduces the number of nodes in map file
        logging.info("OSM to Adj complete in: : %s" % (time.time() - start_time))
        return json.dumps(test2, sort_keys = False, indent = 2)
        #Save map data to server storage
        os.makedirs(dir)
        with open(f"{dir}/map_data.json", 'w') as x:
            json.dump(test2, x, indent=4)
    except MemoryError:
        logging.exception(f"Memory Exception occurred while processing: {dir}")

    #Generates hash file for recently created map
    try:
        md5_hash = hashlib.md5()
        with open(f"{dir}/map_data.json","rb") as f:
            # Read and update hash string value in blocks of 4K
            for byte_block in iter(lambda: f.read(4096),b""):
                md5_hash.update(byte_block)
            logging.info("Hash: " + md5_hash.hexdigest())
        with open(f"{dir}/hash.txt", "w") as h:
            h.write(md5_hash.hexdigest())
    except:
        logging.exception("Hashing error occured")

    #removes temporary files generated while generating map
    os.remove(o5m)
    os.remove(filename)

    ti = (time.time() - start_time)
    logging.info(f"Map file created with bounds: {location} in {ti} seconds")
    response = json.dumps(test2, sort_keys = False, indent = 2)
    return response


#Creates a background scheduled task for the map update method
sched = BackgroundScheduler()
sched.daemonic = True
sched.start()

sched.add_job(update, 'cron', day='1st tue', hour='2', misfire_grace_time=None)

sched.print_jobs()

logging.basicConfig(filename='log.log',format='%(asctime)s %(message)s', level=logging.DEBUG)
