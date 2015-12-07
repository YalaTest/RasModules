#!/usr/bin/python
import numpy as np
import math, bitstream

landing_area_x = 1 #meters TODO have these sent in as agruments
landing_area_y = 1 #meters TODO have these sent in as agruments
total_flight_area = np.zeros((1000, 1000), dtype=np.uint8) #we can make this whatever size we want TODO have the size sent in as an argument or as a function of something?
total_votes = np.zeros((1000, 1000), dtype=np.uint8)

#find the (0,0) lat/lon for any grid assuming you start in the center of that grid
def find_grid_origin(grid, center, lat_deg_per_index_row, lon_deg_per_index_col):
    if grid.shape[0] % 2:
        origin_lat = center[0] - (grid.shape[0]/2+1)*lat_deg_per_index_row + lat_deg_per_index_row * 0.5
    else:
        origin_lat = center[0] - (grid.shape[0]/2)*lat_deg_per_index_row
    if grid.shape[1] % 2:
        origin_lon = center[1] - (grid.shape[1]/2+1)*lon_deg_per_index_col  + lon_deg_per_index_col * 0.5
    else:
        origin_lon = center[1] - (grid.shape[1]/2)*lon_deg_per_index_col
    return (origin_lat, origin_lon)


grid_center = (37.410221, -122.059562) #start location of drone 0 TODO FROM THE DRONE 0 FIGURE OUT HOW TO INITALIZE THIS VALUE

#Latitude:  1 deg = 110.54 km
#Longitude: 1 deg = 111.320*cos(latitude) km
#These are my (1,1) coords that need to be rotated based on the heading (360 - heading)
lat_degrees_per_LZ_y = landing_area_y * (1 / (110.54 * 1000))
lon_degrees_per_LZ_x = landing_area_x * (1 / (111.320 * math.cos(grid_center[0]) * 1000))

grid_origin = find_grid_origin(total_flight_area, grid_center, lat_degrees_per_LZ_y, lon_degrees_per_LZ_x)

#TODO LOOP HERE
#TODO THESE VALUES COME FROM P2-RADIO
grid_cols = 39
grid_rows = 29 
decision_grid = np.zeros((grid_rows, grid_cols), dtype=np.uint8)
drone_coords = (37.410423, -122.059962)
heading = 282 #heading in degrees 0 - 360 uint16

pic_coords = find_grid_origin(decision_grid, drone_coords, lat_degrees_per_LZ_y, lon_degrees_per_LZ_x) #TODO THIS IS WRONG FIX IT WITH THE TRIG THAT WE DID

#This is the magic that rotates the picture grid and aligns it with the master landing grid called total_flight_area TODO CHANGE THAT NAME IT'S BAD
grid_rotation = 360 - heading
for row in xrange(grid_rows):
    for col in xrange(grid_cols):
        shifted_lon_x = (col*lon_degrees_per_LZ_x) * math.cos(grid_rotation) - (row*lat_degrees_per_LZ_y) * math.sin(grid_rotation) + pic_coords[1]
        shifted_lat_y = (col*lon_degrees_per_LZ_x) * math.sin(grid_rotation) + (row*lat_degrees_per_LZ_y) * math.cos(grid_rotation) + pic_coords[0]
        try:
            total_flight_area[abs(int((grid_origin[0] - shifted_lat_y) / lat_degrees_per_LZ_y)), abs(int((grid_origin[1] - shifted_lon_x) / lon_degrees_per_LZ_x))] += not not decision_grid[row, col]
            total_votes[abs(int((grid_origin[0] - shifted_lat_y) / lat_degrees_per_LZ_y)), abs(int((grid_origin[1] - shifted_lon_x) / lon_degrees_per_LZ_x))] += 1
        except IndexError:
            continue

