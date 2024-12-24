import wget
import subprocess
import os
import logging
import json
from datetime import *
import time
import shutil

divider = "-----------------------------------------------------------------"


app_log = None

def init(al):
    global app_log
    app_log = al
    

def download_map(url, outfolder):
    """Uses wget to attempt downloading a map url

    Parameters:
    url(str): String of the URL that the map download is located at

    Returns:
    string: String of the directory location of the map downloaded

    """
    try:
        filename = wget.download(url, out=f"{outfolder}/")
        app_log.info("Map Download Complete")
    except:
        print("Error downloading map")
        app_log.exception("Exception occurred while downloading map")
        raise
    return filename


def flush_map_cache():
    
    #Clears the saved coordinate maps on update call
    if os.path.isdir("app/reduced_maps/coords"):
        shutil.rmtree("app/reduced_maps/coords")
        
    if os.path.isdir("app/reduced_maps/cities"):
        shutil.rmtree("app/reduced_maps/cities")
            
    os.mkdir("app/reduced_maps/coords")
    os.mkdir("app/reduced_maps/cities")
            
    os.remove("lru.txt")

    f = open("app/reduced_maps/coords/.gitkeep", 'w')
    f.close()
    f = open("app/reduced_maps/cities/.gitkeep", 'w')
    f.close()


def update():
    '''Updates and reduces the root map file'''

    filter_command = '--keep=\"amenity= or aeroway=\" --drop-version --ignore-dependencies'
    map_convert_command = '--keep=\"highway=motorway =trunk =primary =secondary =tertiary =unclassified =residential =primary_link =secondary_link =tertiary_link =trunk_link =living_street =motorway_link =path =footway =cycleway \" --drop-version'
    
    tempfolder = "app/map_files/download" #This folder will be both created AND destroyed
    
    try:
        with open("app/update.json", "r") as f:
            print("Updating maps...")
            app_log.info(f"{divider}")
            app_log.info(f"Updating map...")
            loaded = json.load(f)
            if not os.path.isdir(tempfolder):
                os.mkdir(tempfolder)
            
            for sub in loaded["maps"]:
                d = datetime.today()
                try:
                    map_title = sub["map"]

                    app_log.info(f"Downloading {map_title} map...")
                    download_map(sub["url"], tempfolder)
                    sub["last-updated"] = date.today().strftime("%Y%m%d")

                except:
                    print("Error Downloading Map")
                    app_log.exception(f"Exception occured while downloading map {map_title}")
                    break

                with open("app/update.json", 'w') as f:
                    json.dump(loaded, f, indent=4)

                #filters out info before saving
                try:
                    print("Converting maps... (step 1/5)")
                    app_log.info("Converting maps... (step 1/5)")
                    file_name = sub["file_name"]
                    command  = (f"./app/osm_converts/osmconvert64 {tempfolder}/{file_name} -o=app/o5m_main.o5m")
                    subprocess.run([command], shell=True)
                    
                    print("Filtering amenity maps... (step 2/5)")
                    app_log.info("Filtering amenity maps... (step 2/5)")
                    command = f"./app/osm_converts/osmfilter app/o5m_main.o5m {filter_command} -o=app/filteredTemp.o5m"
                    subprocess.run([command], shell=True)


                    print("Filtering main maps... (step 3/5)")
                    app_log.info("Filtering main maps... (step 3/5)")
                    command = f"./app/osm_converts/osmfilter app/o5m_main.o5m " + map_convert_command + f" -o=app/mainTemp.o5m"
                    subprocess.run([command], shell=True)

                    print("Converting main maps... (step 4/5)")
                    app_log.info("Converting main maps... (step 4/5)")

                    # #saving downloaded maps
                    # We don't need to
                    # os.mkdir(f"{tempfolder}/temp")
                    # os.rename(f"{tempfolder}/" + sub["file_name"], "{tempfolder}/temp/" + sub["file_name"])
                    command  = (f"./app/osm_converts/osmconvert64 app/mainTemp.o5m -o={tempfolder}/{file_name}")
                    subprocess.run([command], shell=True)

                    print("Converting amenity maps... (step 5/5)")
                    app_log.info("Converting amenity maps... (step 5/5)")
                    command  = (f"./app/osm_converts/osmconvert64 app/filteredTemp.o5m -o={tempfolder}/amenity-{file_name}")
                    subprocess.run([command], shell=True)

                    os.remove("app/o5m_main.o5m")
                    os.remove("app/mainTemp.o5m")
                    os.remove("app/filteredTemp.o5m")
                    print("Map convertion done.")
                except:
                    app_log.exception("Converting and filtering error")

                app_log.info("installing maps")

                if (os.path.isfile("app/map_files/" + sub["file_name"])):
                    os.remove("app/map_files/" + sub["file_name"])
                os.rename(f"{tempfolder}/{file_name}", "app/map_files/" + sub["file_name"])
                os.rename(f"{tempfolder}/amenity-{file_name}", "app/map_files/amenity-" + sub["file_name"])

            app_log.info("clearing out temp files")
            shutil.rmtree(f"{tempfolder}")

            try:
                flush_map_cache()
            except Exception as e:
                app_log.exception("Error flushing map cache. Probably non critical:")
                app_log.exception(e)                
            
            print("Maps are up-to-date")
    except Exception as e:
        app_log.exception(e)




# checks whether the map file is there, trigger immediate upadte otherwise
def check_for_emergency_map_update():
    filename = "app/map_files/north-america-latest.osm.pbf" # NA map file directory
    amenityFilename = "app/map_files/amenity-north-america-latest.osm.pbf" # NA map file directory

    if (not os.path.isfile(filename)) or (not os.path.isfile(amenityFilename)):
        print("Map file not found. Emergency map update!")
        update()

