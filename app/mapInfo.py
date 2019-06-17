'''
Created on Jun 4, 2019

@author: Jason (Jay) Strahler
'''

import json
import os

#Returns the min and max lon and lat for a given map file
#This will allow us to pull the correct map based on passed dimension values
def minMax(filename):

    try:
        with open(filename, 'r') as f:
            loaded = json.load(f)
            loaded = json.loads(loaded)
            minLon = None
            maxLon = None
            minLat = None
            maxLat = None

            for val in loaded['nodes']:
                if (minLon is None or minLon > val[2]):
                    minLon = val[2]

                elif (maxLon is None or maxLon < val[2]):
                    maxLon = val[2]


                if (minLat is None or minLat > val[1]):
                    minLat = val[1]

                elif (maxLat is None or maxLat < val[1]):
                    maxLat = val[1]

    except:
        print("Error reading map file")


    return [minLon, minLat, maxLon, maxLat]

def mapListUpdate():
    filenames= os.listdir ("app/reduced_maps/named_places") # get all files' and folders' names in the current directory

    result = []



    return result
