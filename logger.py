#!/usr/bin/env python

import os, sys
import datetime, time
import configparser
import json
import minimalmodbus

## Import instrument driver
from falco import Falco

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

def log_message(module, msg):
        """
        Logs a message with standard format
        """
        timestamp = time.strftime("%Y.%m.%d-%H:%M:%S ")
        log_message = "- [{0}] :: {1}"
        log_message = timestamp + log_message.format(module,msg)
        print(log_message, file=sys.stderr)


## Start logging script
base_path = os.path.abspath(os.path.dirname(sys.argv[0]))
sys.path.append(base_path + '/')

## place holder for send_string
#from gui import send_string
def send_string(line, server_address, sock = 0):
   return 0

# READ ini file
config_file = base_path + '/config.ini'
if os.path.exists(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    
    falco_port          = eval(config['GENERAL_SETTINGS']['PORT'])
    falco_address       = eval(config['GENERAL_SETTINGS']['ADDRESS'])
    data_path           = eval(config['GENERAL_SETTINGS']['DATA_PATH']) + '/'
    
    server_name         = eval(config['TCP_INTERFACE']['HOST_NAME'])
    server_port         = eval(config['TCP_INTERFACE']['HOST_PORT'])
    
    header_file_name    = eval(config['LOGGER']['HEADER'])
    buffersize          = eval(config['LOGGER']['BUFFER'])
    basefilename        = eval(config['LOGGER']['DATAFILE'])
    extension           = eval(config['LOGGER']['EXTENSION'])
else:
    print( "Could not find the configuration file: {}".format(config_file) , file = sys.stderr)
    exit()

# Connect the socket to the port where the server is listening
server_address = (server_name, server_port)
sock = 0
log_message("LOGGER", 'starting up on %s port %s' %server_address)

# Prepare Header string
try:
   data = falco.readline()
   
except minimalmodbus.ModbusException:
       log_message("LOGGER", "cannot read data-line. Restarting port and waiting 5 seconds...")

       time.sleep(5)

# Variables
counter = 0
sensor = falco(falco_port, falco_address)
filename = basefilename + extension
filedate = False
x=''

while 1:
    try:
      data = falco.readline()
      json_string = json.dumps(data)
      daytime = time.strftime("%H:%M:%S")
      data_string = daytime
      columns_string = 'daytime'
      units_string = 'hh:mm:ss'
      for dic in data:
         data_string += '\t' + dic['val'])
         columns_string += '\t' + dic['var'])
         units_string   += '\t' + dic['unit'])
      header_string = columns_string + '\n' + units_string

    except minimalmodbus.ModbusException:
       log_message("LOGGER", "cannot read data-line. Waiting 5 seconds...")
       time.sleep(5)

    except KeyboardInterrupt:
       log_message("LOGGER", "aborted by user!")
       #device.close_port()
       log_message("LOGGER", "Writing data...")
       fo = open(f, "a")
       fo.write(x)
       fo.close()
       log_message("LOGGER", "bye...")
       break

    except:
       log_message("LOGGER", "something went wrong... Waiting 5 seconds...")
       log_message("LOGGER", "    --- error type: " + str(sys.exc_info()[0]))
       log_message("LOGGER", "    --- error value: " + str(sys.exc_info()[1]))
       log_message("LOGGER", "    --- error traceback: " + str(sys.exc_info()[2]))

       time.sleep(5)

    if data_string <> "":
       x+=daytime + '\t' + data_string

       # transmit TCP data
       sock = send_string(json_string, server_address, sock)
    counter+=1;
    newdate = datetime.datetime.now()

    # Start a new datafile if none available
    if not filedate:
       f = create_data_file(data_path, header=header_string, name=filename)
       log_message("LOGGER", "Writing to Datafile: " + f)
       filedate = newdate

    # Create a new file at midnight
    if newdate.day <> filedate.day:
       fo = open(f, "a")
       fo.write(x)
       fo.close()
       x=''
       counter=0
       filedate = newdate
       f = create_data_file(data_path, header=header_string, name=basefilename)
       log_message("LOGGER", "Writing to Datafile: " + f)
    elif counter >= buffersize:
       fo = open(f, "a")
       fo.write(x)
       fo.close()
       x=''
       counter=0
