#!/usr/bin/env python

import os, sys
import datetime, time
import configparser
import json
import minimalmodbus
import socket

## Import function for sending data to gui.py
from utils import send_string, log_message

## Import instrument driver
from falco import Falco
from smt100 import SMT100

## Define some utility hfunctions

def create_data_file(path, header, name): 
    #This function creates column headers for a new datafile
    prefix  = time.strftime("%Y%m%d-%H%M%S-")
    date    = time.strftime("%Y-%m-%d")
    newname = path + prefix + name
    fo      = open(newname, "w")
    fo.write(date)
    fo.write('\n')
    fo.write(header)
    fo.close()

    return newname

## Start logging script ##

# directory for location of config.ini
base_path = os.path.abspath(os.path.dirname(sys.argv[0]))
#sys.path.append(base_path + '/')

# READ ini file
config_file = base_path + '/config.ini'
if os.path.exists(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    
    sensor_port          = eval(config['GENERAL_SETTINGS']['PORT'])
    sensor_address       = eval(config['GENERAL_SETTINGS']['ADDRESS'])
    data_path           = eval(config['GENERAL_SETTINGS']['DATA_PATH']) + '/'
    
    server_name         = eval(config['TCP_INTERFACE']['HOST_NAME'])
    server_port         = eval(config['TCP_INTERFACE']['HOST_PORT'])
    
    buffersize          = eval(config['LOGGER']['BUFFER'])
    basefilename        = eval(config['LOGGER']['DATAFILE'])
    extension           = eval(config['LOGGER']['EXTENSION'])
else:
    log_message("GUI", "Could not find the configuration file: {}".format(config_file))
    exit()

# Socket information in line to the port where the server is listening
server_address = (server_name, server_port)
sock = 0
log_message("LOGGER", 'starting up on %s port %s' %server_address)

# Variables
counter = 0         # counter for writing data to datafile every n cycles
filename = basefilename + extension # datafile name (date/time will be added)
filedate = False    # date of creation of current datafile
x=''                # data buffer (string) for writing to datafile every n cycles
data_string = ''    # string of new data (only last cycle)
header_string = ''  # header to be used for new datafile (refreshed every cycle)

sensor = False

while not sensor:
    try:
    #    sensor = Falco(sensor_port, sensor_address)
        sensor = SMT100(sensor_port, sensor_address)
    except:
        log_message("LOGGER",
                "Could not open adress '{}' at port '{}'".format(
                sensor_address, sensor_port))
        log_message("LOGGER", "Waiting 5 seconds...")
        time.sleep(5)

 #        exit()

while 1:
    daytime = time.strftime("%H:%M:%S")
    
    # initialize the datafile header data
    columns_string = 'daytime'
    units_string = 'hh:mm:ss'
    
    try:
      data_string += daytime

      # receive and decode new data
      data = sensor.readline()
      json_string = json.dumps(data)
      for dic in data:
         data_string += '\t' +  repr(dic['val'])
         columns_string += '\t' + dic['var']
         units_string   += '\t' + dic['unit']

      data_string += '\n' 
         
      # put together the file header
      header_string = columns_string + '\n' + units_string + '\n'
      
      if json_string:
        # transmit TCP data
        sock = send_string(json_string, server_address, sock)

        # update buffer and counter
        x+= data_string
        counter+=1;

#     except minimalmodbus.ModbusException:
#        log_message("LOGGER", "cannot read data-line. Waiting 5...")
#        time.sleep(5)

    except KeyboardInterrupt:
       log_message("LOGGER", "aborted by user!")
       log_message("LOGGER", "Writing data...")
       
       if filedate:
           fo = open(f, "a")
           fo.write(x)
           fo.close()
       else:
           log_message("LOGGER", "No data file in use...")

       if sock:
           log_message("LOGGER", "Closing socket...")
           sock.shutdown(socket.SHUT_RDWR)
           sock.close()
       log_message("LOGGER", "bye...")
       break

    except:
       log_message("LOGGER", "something went wrong... Waiting 5 seconds...")
       log_message("LOGGER", "    --- error type: " + str(sys.exc_info()[0]))
       log_message("LOGGER", "    --- error value: " + str(sys.exc_info()[1]))
       exec_tb = sys.exc_info()[2]
       fname = os.path.split(exec_tb.tb_frame.f_code.co_filename)[1]
       log_message("LOGGER", "    --- error File: {}".format(fname))
       log_message("LOGGER", "    --- error line: {}".format(exec_tb.tb_lineno))

       time.sleep(5)

    newdate = datetime.datetime.now()

    # Start a new datafile if none available
    if not filedate and header_string:
       f = create_data_file(data_path, header=header_string, name=filename)
       log_message("LOGGER", "Writing to Datafile: " + f)
       filedate = newdate
    
    if filedate:

        # Create a new file at midnight
        if newdate.day != filedate.day:
           fo = open(f, "a")
           fo.write(x)
           fo.close()
           x=''
           counter=0
           filedate = newdate
           f = create_data_file(data_path, header=header_string, name=filename)
           log_message("LOGGER", "Writing to Datafile: " + f)

        # write and clear buffer if buffersize was reached
        elif counter >= buffersize:
           fo = open(f, "a")
           fo.write(x)
           fo.close()
           x=''
           counter=0
