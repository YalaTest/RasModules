#!/usr/bin/python
import bitstream, sys, serial, glob
import numpy as np

def find_ports():
    # check ports for each system
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(10)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')
    result = []
    for port in ports:
        try:
            s = serial.Serial(port, timeout=1)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
        # print(result)
    return result

def read_radio_and_send_to_P3(serial_port):
    radio_stream = bitstream.BitStream()
    #states
    READ_ALTITUDE = 0
    READ_HEADING_GRID = 1 
    READ_DRONE_COORDS = 2
    READ_GRID = 3
    END_STATE = 4

    read_state = READ_ALTITUDE
    message_pad = 0
    message_heading_grid = (0, 0, 0)

    while(True):
        data = serial_port.read(serial_port.inWaiting())
        radio_stream.write(data, str)
        if (read_state == READ_ALTITUDE) and (len(radio_stream) >= 8):
            message_altitude = radio_stream.read(np.uint8, 1)
            read_state = READ_HEADING_GRID
        elif (read_state == READ_HEADING_GRID) and (len(radio_stream) >= 48):
            message_heading_grid = radio_stream.read(np.uint16, 3)
            message_pad = 8 - ((int(message_heading_grid[1]) * int(message_heading_grid[2])) % 8)
            if message_pad == 8:
                message_pad = 0
            read_state = READ_DRONE_COORDS
        elif (read_state == READ_DRONE_COORDS) and (len(radio_stream) >= 128):
            message_drone_coords = radio_stream.read(float, 2)
            read_state = READ_GRID
        elif (read_state == READ_GRID) and (len(radio_stream) >= int(message_heading_grid[1])*int(message_heading_grid[2]) + message_pad):
            message_decision_grid = np.zeros((message_heading_grid[1], message_heading_grid[2]), dtype=np.uint8)
            for row in xrange(message_heading_grid[1]):
                for col in xrange(message_heading_grid[2]):
                    message_decision_grid[row][col] = radio_stream.read(bool, 1)[0]
            for row in xrange(message_pad):
                radio_stream.read(bool, 1)
            read_state = END_STATE
        elif read_state == END_STATE:
            #TODO SEND THE (message_decision_grid, message_drone_coords, message_heading_grid) to P3-GRID
            read_state = READ_ALTITUDE
            break

def read_from_P1_send_over_radio_and_send_to_P3(): #TODO this function will have some arguments
    while(True):
        #TODO GET (message, decision_grid, drone_coords, heading) FROM P1-CAMERA
        #TODO SEND message OUT OVER THE RADIO
        #TODO SEND (decision_grid, drone_coords, heading) TO P3-GRID
        break

def radio():
    while(True):
        try:
            radio_port = find_ports()
            serial_port = serial.Serial(radio_port[0], 57600)
            serial_port.flushInput()
            serial_port.flushOutput()
            while(True):
                if serial_port.inWaiting() > 0:
                    read_radio_and_send_to_P3(serial_port)
                if False: #TODO SOME if multiprocess.buffer > 0:
                    read_from_P1_send_over_radio_and_send_to_P3()#TODO this function will have some arguments
        except serial.SerialException, IndexError:
            print "RADIO ISSUE: SOMETHING IS SCREWED"
            continue

radio()
