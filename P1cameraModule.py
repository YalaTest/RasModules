#!/usr/bin/python
import cv2
import numpy as np
from picamera.array import PiRGBArray
from picamera import PiCamera
import time, math, bitstream

def read_drone_data():
    altitude = 40 #meters uint8 #TODO FROM DRONE
    drone_coords = (37.410423, -122.059962) #TODO FROM DRONE
    heading = 282 #degrees clockwise from north TODO FROM THE DRONE
    return altitude, drone_coords, heading

def find_canny_thresholds(altitude):
    minVal = 100
    maxVal = 200
    return minVal, maxVal

def create_decision_grid(altitude, fov_h, rows, cols, landing_area_x, landing_area_y):
    pixle_size = ((altitude * math.tan(math.radians( fov_h / 2 ))) / ( cols / 2 )) #number of meters per pixle
    grid_pix_x = int(landing_area_x / pixle_size)
    grid_pix_y = int(landing_area_y / pixle_size)
    grid_cols = int(cols / grid_pix_x)
    grid_rows = int(rows / grid_pix_y)
    decision_grid = np.zeros((grid_rows, grid_cols), dtype=np.uint8)
    return decision_grid, grid_cols, grid_rows, grid_pix_x, grid_pix_y

def camera(fov_v, fov_h, threshold, landing_area_x, landing_area_y):
    #make the bitstream for the radio message
    radio_stream = bitstream.BitStream()

    # init camera and get a reference to the raw capture
    camera = PiCamera()
    camera.resolution = (640, 480)
    camera.framerate = 32
    rawCapture = PiRGBArray(camera, size=(640, 480))

    #time for the camera to warm up which is apparently a thing, and we'd probably only have to do it once rather than every picture
    time.sleep(0.1)

    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        #get the data from the drone
        altitude, drone_coords, heading = read_drone_data()

        #get an image from the camera
        edges = frame.array #TODO FROM CAMERA
        rawCapture.truncate(0)

        #do edge detection on the image
        minVal, maxVal = find_canny_thresholds(altitude)  #TODO something about these minVal, maxVal based on altitude
        edges = cv2.Canny(edges, minVal, maxVal)
        rows, cols = edges.shape

        #create the decision grid
        decision_grid, grid_cols, grid_rows, grid_pix_x, grid_pix_y = create_decision_grid(altitude, fov_h, rows, cols, landing_area_x, landing_area_y)

        #create the radio message to be sent
        radio_stream.write(altitude, np.uint8) #1 byte total
        radio_stream.write(heading, np.uint16) #3 bytes total
        radio_stream.write((grid_rows, grid_cols), np.uint16) #7 bytes total
        radio_stream.write(drone_coords, float) #23 bytes total

        for row in xrange(grid_rows):
            for col in xrange(grid_cols):
                decision_grid[row][col] = len(np.where(edges[row*grid_pix_y:row*grid_pix_y+grid_pix_y, col*grid_pix_x:col*grid_pix_x+grid_pix_x] > 0)[0])
                if decision_grid[row][col] >= threshold:
                    radio_stream.write(1, bool)
                else:
                    radio_stream.write(0, bool)

        #radio can only handle a byte as the smallest unit of information, so we have to pad the signal
        pad = 8 - ((grid_rows * grid_cols) % 8)
        if pad == 8:
            pad = 0
        for i in xrange(pad):
            radio_stream.write(0, bool)

        message = radio_stream.read(str, 23 + (grid_rows*grid_cols + pad)/8)

        #TODO SEND (message, decision_grid, drone_coords, heading) to P2-RADIO

fov_v = 40 #vertical field of view degrees
fov_h = 53 #horizontal field of view degrees
threshold = 3 #number of edges that have to be in the LZ for it to be not land
landing_area_x = 1 #meters TODO have these send as agruments
landing_area_y = 1 #meters TODO have these send as agruments
camera(fov_v, fov_h, threshold, landing_area_x, landing_area_y)
