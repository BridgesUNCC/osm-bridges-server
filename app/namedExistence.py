'''
Created on Jun 6, 2019

@author: Jason (Jay) Strahler
'''

import os
import sys

def search(location):
    """Searches a directory for map json file, mainly used for telling users if their location has already been converted or not
    
    Parameters:
    location(str): Name of place the user is try to map
    
    Returns:
    string: String of whether or not location has been created 
    
    """
    
    
    if(type(location) == str):
        location = location.lower()
        if (os.path.isdir(f"reduced_maps/named_places/{location}")):
            return f"{location} has a map"
    else:
        if (os.path.isdir(f"reduced_maps/coords/{location[0]}/{location[1]}/{location[2]}/{location[3]}")):
            return f"{location} has a map"
    
    
    return f"No map found for {location}"




try:
    location = sys.argv[1].split(',')
    if (len(location) == 1):
        input_Value = location[0]
    else:
        input_Value = location
except:
    print("Error getting system arguments") 

print(search(input_Value))
