import sys
import io
import json
from math import sin, cos, sqrt, atan2, radians
import xml.etree.ElementTree as ET


def get_one_way_from(all_attrib):
    if 'oneway' in all_attrib:
        if all_attrib['oneway'] == 'yes':
            return True
        else:
            return False
    else:
        return False


def get_avg_speed_from(all_attrib):
    if 'maxspeed' in all_attrib:
        try:
            maxspeed = int(''.join(filter(str.isdigit ,all_attrib['maxspeed'])))
        except:
            maxspeed = None

    else:
        maxspeed = None
    if 'minspeed' in all_attrib:
        try:
            minspeed = int(''.join(filter(str.isdigit ,all_attrib['minspeed'])))
        except:
            minspeed = None
    else:
        minspeed = None
    if maxspeed:
        if minspeed:
            return ((maxspeed + minspeed) * 1.6) / 2
        else:
            return maxspeed * 1.6
    if minspeed:
        return minspeed * 1.6
    return 30 * 1.6


def distance(lat1,lon1,lat2,lon2):
    R = 6373.0                                      # raduis of earth
    lat1 = radians(lat1)                            # convert to radians
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlon = lon2 - lon1                              # take the differnce
    dlat = lat2 - lat1                              # apply the formula

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    dist = R * c
    return dist*1000                                # to meters


# remove chain a->b->c where a and b have degree 1.
# once identified in a chain, neither a or c will be deleted again
# returns whether anything was deleted (True) or not (False)
def del_chain1(d_nodes, adj_nodes):
    retval = False
    
    # compute indegrees
    indegrees = {}
    for ele in d_nodes:
        for idx in adj_nodes[ele]:
            dest = idx[0] 
            if dest not in indegrees:
                indegrees[dest] = 1
            else:
                indegrees[dest] = indegrees[dest] + 1
                
    # Compressing degree 1 path

    marked = set()
    nodestodelete = set()
    for ele in d_nodes:
        if len(adj_nodes[ele]) == 1:
            intermediary = adj_nodes[ele][0][0]
            if len(adj_nodes[intermediary]) == 1 and indegrees[intermediary] == 1:
                end = adj_nodes[intermediary][0][0]

                # there is a path "ele -> intermediary -> end" where intermediary has no other edges (incoming or outgoing)
                if ele not in marked and intermediary not in marked and end not in marked:

                    # there is a path "ele -> intermediary -> end"
                    # where intermediary has no other edges (incoming
                    # or outgoing) and neither of the three is
                    # marked. Ready to adjust the graph structure.
                    
                    # mark to prevent two remove in one pass
                    marked.add(ele)
                    marked.add(intermediary)
                    marked.add(end)

                    # intermediary should be deleted from nodes and adj_nodes
                    nodestodelete.add (intermediary)

                    # add the compressed edge and remove the edge to intermediary
                    time_to_adj = adj_nodes[ele][0][1] + adj_nodes[intermediary][0][1];

                    # the following two lines are ok because ele is of out degree one.
                    adj_nodes[ele] = list()                        #reinitialize the set
                    adj_nodes[ele].append((end,time_to_adj))       #add as an edge
                    
                    retval = True
                    
    for ele in nodestodelete:
        adj_nodes.pop(ele)
        d_nodes.pop(ele)

    return retval
    

# remove chain a<->b<->c where a and b have degree 1.
# once identified in a chain, neither a or c will be deleted again
# returns whether anything was deleted (True) or not (False)
def del_chain2(d_nodes, adj_nodes):
    retval = False
    
    # compute indegrees
    indegrees = {}
    for ele in d_nodes:
        for idx in adj_nodes[ele]:
            dest = idx[0] 
            if dest not in indegrees:
                indegrees[dest] = 1
            else:
                indegrees[dest] = indegrees[dest] + 1
                
    # Compressing degree 1 path
    marked = set()
    nodestodelete = set()
    for ele in d_nodes:
        if ele in marked:
            continue;
        
        if len(adj_nodes[ele]) == 2:
            before = adj_nodes[ele][0][0]
            after = adj_nodes[ele][1][0]

            if before == after:
                # print ("What is going on?") # probably we compressed a disconnected traffic circle
                continue
            
            if before in marked:
                continue
            if after in marked:
                continue

            if ele not in indegrees:
                continue
            
            if indegrees[ele] != 2:
                continue

            # there is an unmarked path "before <- ele -> after" where neither of the three are marked and ele is of indegree 2

            # does before has ele in its neighbor?
            foundbefore = False
            for edge in adj_nodes[before]:
                if edge[0] == ele:
                    beforeedge = edge
                    foundbefore = True

            if not foundbefore:
                continue
            

            # does before has ele in its neighbor?
            foundafter = False
            for edge in adj_nodes[after]:
                if edge[0] == ele:
                    afteredge = edge
                    foundafter = True

            if not foundafter:
                continue

            # there is an unmarked path "before <-> ele <-> after" where neither of the three are marked and ele is part of no other path

            newedgelenth = beforeedge[1]+afteredge[1]

            # mark to prevent two remove in one pass
            marked.add(before)
            marked.add(ele)
            marked.add(after)
            
            # ele should be deleted from nodes and adj_nodes
            nodestodelete.add (ele)

            # remove the before->ele edge
            adj_nodes[before].remove(beforeedge)

            # remove the after->ele edge
            adj_nodes[after].remove(afteredge)

            # add the before->after edge
            adj_nodes[before].append((after, newedgelenth))
            
            # add the after->before edge
            adj_nodes[after].append((before, newedgelenth))

            retval = True
            
    for ele in nodestodelete:
        adj_nodes.pop(ele)
        d_nodes.pop(ele)

    return retval


def main(input_filename, shrink=0, name=None):
    f = io.open(input_filename,encoding='utf-8')           # open file
    tree = ET.parse(f)                                  # parse xml file
    root = tree.getroot()                               # get tree root
    d_nodes = {}                                        # dict to store all nodes
    adj_nodes = {}                                      # to keep adj list
    for node in root.findall("node"):                   # get all nodes
        index = int(node.get('id'))                     # get the index
        d_nodes[index] = (float(node.get('lat')),float(node.get('lon')))
        adj_nodes[index] = list()                        # initialize the set

    for way in root.findall('way'):                     # get all ways
        tags = way.findall('tag')
        all_attrib = {ele['k']:ele['v'] for ele in [x.attrib for x in tags]}
        avg_speed = get_avg_speed_from(all_attrib)
        oneway = get_one_way_from(all_attrib)
        last = 0                                        # one node will point to other
        for nd in way.findall('nd'):                    # get all links on each way
            if last is 0:                               # this is first node
                last = int(nd.get('ref'))               # initialize and forget
                if last not in d_nodes:
                    last = 0
                continue
            else:                                       # otherwise
                if int(nd.get('ref')) not in d_nodes:
                    continue
                adj_index = int(nd.get('ref'))          # get list of current element
                dist_to_adj = distance( d_nodes[last][0],
                                        d_nodes[last][1],
                                        d_nodes[adj_index][0],
                                        d_nodes[adj_index][1] )
                time_to_adj = dist_to_adj / avg_speed
                time_to_adj = time_to_adj * 60          # in minutes
                adj_nodes[last].append((adj_index,time_to_adj))         # add as an edge
                if not oneway:
                    adj_nodes[adj_index].append((last,time_to_adj))         # add as an edge
                last = adj_index                        # update last

    again = True
    iter = 0
    while again and iter < shrink:
        again = del_chain1(d_nodes, adj_nodes)
        iter = iter +1


    iter = 0
    again = True
    while again and iter < shrink:
        again = del_chain2(d_nodes, adj_nodes)
        iter = iter +1

    """
    #formating two column
    with open(output_filename,"w") as f:
        for ele in adj_nodes:
            for (node,dist) in adj_nodes[ele]:
                f.write("{0} {1} {2}\n".format(ele,node,dist))
    with open(output_filename + ".meta", "w") as f:
        for ele in d_nodes:
            f.write("{0} {1} {2}\n".format(ele, d_nodes[ele][0], d_nodes[ele][1]))
    """
    
    # JSON Formatting
    out = {}
    meta = {}
    lat_min, lat_max, lon_min, lon_max = (None, None, None, None)

    out_edges = []
    for ele in adj_nodes:
        for (node,dist) in adj_nodes[ele]:
            out_edges.append([ele, node, dist])

    out_vert = []
    for ele in d_nodes:
        this_lat = d_nodes[ele][0]
        this_lon = d_nodes[ele][1]
        if lat_min is None or lat_min > this_lat:
            lat_min = this_lat
        if lat_max is None or lat_max < this_lat:
            lat_max = this_lat
        if lon_min is None or lon_min > this_lon:
            lon_min = this_lon
        if lon_max is None or lon_max < this_lon:
            lon_max = this_lon

        out_vert.append([ele, this_lat, this_lon])

    out['nodes'] = out_vert
    out['edges'] = out_edges
    meta['lat_min'] = lat_min
    meta['lat_max'] = lat_max
    meta['lon_min'] = lon_min
    meta['lon_max'] = lon_max

    if name is not None:
        meta['name'] = name

    out['meta'] = meta
    return json.dumps(out)


if __name__=="__main__":
    shrink = 0
    name = None
    if len(sys.argv) > 2:
        name = sys.argv[2]
    if len(sys.argv) > 3:
        shrink = int(sys.argv[3])
    print(main(sys.argv[1], shrink, name))
