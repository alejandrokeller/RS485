#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# listens to a TCP broadcast and displays data using Ppyqt widgets
# provides also a buttons interface for interacting with the 
# measurement instrument

from PyQt5 import QtGui, QtCore, QtWidgets
import pyqtgraph as pg
import socket
import sys, os
import numpy as np
import pandas as pd
import datetime, time
import json
import configparser

from utils import TimeAxisItem, timestamp

base_path = os.path.abspath(os.path.dirname(sys.argv[0]))

def log_message(module, msg):
        """
        Logs a message with standard format
        """
        timestamp = time.strftime("%Y.%m.%d-%H:%M:%S ")
        log_message = "- [{0}] :: {1}"
        log_message = timestamp + log_message.format(module,msg)
        print(log_message, file=sys.stderr)

def send_string(line, server_address, sock = 0):
    # Sends a string to through a TCP socket

    # Send data
    try:
        if not sock:
            # Create a TCP/IP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(server_address)
            
        sock.sendall(line.encode())
    except socket.error:
#        print("nobody listening", file = sys.stderr)
        sock.close()
#        print('closing socket', file = sys.stderr)
        sock = 0

    return sock

class Visualizer(object):
    def __init__(self, host_name='localhost', host_port=10000):
        
        # init socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create a TCP/IP socket
        self.server_address = (host_name, host_port)
        print('starting up on {}'.format(self.server_address), file=sys.stderr)
        self.sock.bind(self.server_address) # Bind the socket to the port
        self.sock.listen(1) # Listen for incoming connections
        print('waiting for a connection', file=sys.stderr)
        self.connection, self.client_address = self.sock.accept() # Wait for a connection
        print('connection from {}'.format(self.client_address), file=sys.stderr)

        # init pyqt
        self.app = QtWidgets.QApplication([])
        pg.setConfigOptions(antialias=False)
        pg.setConfigOption('foreground', 'w')

        #init data structure
        self.firstLoop = True
        self.numSamples = 1200 
        self.datastring = ""
        self.deltaT = 0.5
        self.timeKey = 'Date/Time'

        # variables to keep for front end
        self.keys = [
            "T",
            "Moist",
            "Count",
            self.timeKey
            ]

        # variables to plot (one plot per variable)
        self.plotVariable = [
            "Count",
            "Moist"
        ]

        self.df = pd.DataFrame(columns=self.keys)

        # setup plots
        self.pen = pg.mkPen('y', width=1)

        self.plot = {}
        self.curve = {}

        for v in self.plotVariable:
            self.plot[v] = pg.PlotWidget(axisItems={'bottom':TimeAxisItem(orientation='bottom')})
            #self.Mplot.setRange(yRange=[50, 100])
            self.plot[v].addLegend()
            self.plot[v].setLabel('bottom', "Time")
            self.plot[v].showGrid(False, True)
            self.curve[v] = self.plot[v].plot([], [], pen=self.pen)

#####################################################################

        ## Define a top level widget to hold the controls
        self.widgets = QtWidgets.QWidget()
        self.widgets.setWindowTitle("RS485 Logger")
        self.widgets.showFullScreen()

        # text field to hold info from another variable
        self.lblTextData    = QtWidgets.QLabel("Counts: ")

        ## Create a QVBox layout to manage the plots
        self.plotLayout = QtWidgets.QVBoxLayout()

        for v in self.plotVariable:
           self.plotLayout.addWidget(self.plot[v])
        self.plotLayout.addWidget(self.lblTextData)

        ## Create a QHBox layout to manage the plots
        self.centralLayout = QtWidgets.QHBoxLayout()
        self.centralLayout.addLayout(self.plotLayout)

        ## Display the widget as a new window
        self.widgets.setLayout(self.centralLayout)
        self.widgets.show()

    def update(self):

        try: 
            self.datastring = self.connection.recv(1024).decode()

            # if two points were read
            two_points = self.datastring.find('][')
            if two_points > 0:
                    self.datastring = self.datastring[0:two_points+1]
            recvData = {}
            recvUnit = {}
            if self.datastring:
                dataDict = json.loads(self.datastring)
                for v in dataDict:
                        recvData[v['var']] = v['val']
                        recvUnit[v['var']] = v['unit']

            if recvData:
                newData = {}
 
                for k in self.keys:
                    if k != self.timeKey:
                        try:
                           newData[k] = recvData[k]
                        except:
                           print("could not extract ", k, " value from ", dataDict)
                    else:
                        newData[k] = timestamp() #datetime.datetime.now()

                # reshape dataframe
                dfRowCount = len(self.df.index)
                if dfRowCount >= self.numSamples:
                    self.df = self.df.tail(self.numSamples-1)
                    self.df = pd.concat([self.df, pd.DataFrame([newData])],ignore_index=True)
                elif dfRowCount == 0:
                    self.df = pd.DataFrame.from_dict([newData])
                else:
                    self.df = pd.concat([self.df, pd.DataFrame([newData])],ignore_index=True)

                for v in self.plotVariable:
                    self.curve[v].setData(self.df[self.timeKey], self.df[v])

                # modify y-axis to show variable name and units
                if self.firstLoop:
                    for v in self.plotVariable:
                        self.plot[v].setLabel('left', v, units=recvUnit[v])
                    self.firstLoop = False

                self.lblTextData.setText("Temperature: {} {}".format(newData['T'],recvUnit['T']))

        except KeyboardInterrupt:
            log_message("LOGGER", "aborted by user!")
            print(self.datastring)
            exit()

        except:
            log_message("LOGGER", "    --- error type: " + str(sys.exc_info()[0]))
            log_message("LOGGER", "    --- error value: " + str(sys.exc_info()[1]))
            exec_tb = sys.exc_info()[2]
            fname = os.path.split(exec_tb.tb_frame.f_code.co_filename)[1]
            log_message("LOGGER", "    --- error File: {}".format(fname))
            log_message("LOGGER", "    --- error line: {}".format(exec_tb.tb_lineno))
            
##            raise

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys

    # READ ini file
    config_file = base_path + '/config.ini'
    if os.path.exists(config_file):
        config = configparser.ConfigParser()
        config.read(config_file)
        host_name = eval(config['TCP_INTERFACE']['HOST_NAME'])
        host_port = eval(config['TCP_INTERFACE']['HOST_PORT'])
    else:
        print("Could not find the configuration file: {}".format(config_file), file=sys.stderr)
        exit()


    vis = Visualizer(host_name=host_name, host_port=host_port)

    timer = QtCore.QTimer()
    timer.timeout.connect(vis.update)
    timer.start(round(vis.deltaT*1000))

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtWidgets.QApplication.instance().exec_()
