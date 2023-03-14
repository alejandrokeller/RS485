#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# listens to a TCP broadcast and displays data using Ppyqt widgets

from PyQt5 import QtGui, QtCore, QtWidgets
import pyqtgraph as pg
import socket
import sys, os
import numpy as np
import pandas as pd
import datetime, time
import json
import configparser

from utils import TimeAxisItem, timestamp, log_message

# path where the config.ini file is located
base_path = os.path.abspath(os.path.dirname(sys.argv[0]))

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
        self.app.aboutToQuit.connect(self.closeSocket) # exit Handle that closes the communication socket

        #init data structure
        self.firstLoop = True
        self.numSamples = 1200 
        self.datastring = ""
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
        
        # dataframe that will hold the data
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

        ## add the plots
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
            # wait for new data to arrive
            self.datastring = self.connection.recv(1024).decode()

            # if more than one datapoint was received keep only the first one.
            # Only affects the GUI. All points are saved by logger.py 
            two_points = self.datastring.find('][')
            if two_points > 0:
                    self.datastring = self.datastring[0:two_points+1]

            # decode json string into a value and a units dictionaries
            recvData = {}
            recvUnit = {}
            if self.datastring:
                dataDict = json.loads(self.datastring)
                for v in dataDict:
                        recvData[v['var']] = v['val']
                        recvUnit[v['var']] = v['unit']

            # reduce the data to the subset required by the GUI
            # then update the dataframe and the front end
            if recvData:
                newData = {}
 
                for k in self.keys:
                    if k != self.timeKey:
                        try:
                           newData[k] = recvData[k]
                        except:
                           print("could not extract ", k, " value from ", dataDict)
                    else:
                        # add the time as variable using the local time
                        newData[k] = timestamp()

                # reshape dataframe to a maximum of self.numSamples points
                dfRowCount = len(self.df.index)
                if dfRowCount >= self.numSamples:
                    self.df = self.df.tail(self.numSamples-1)
                    self.df = pd.concat([self.df, pd.DataFrame([newData])],ignore_index=True)
                elif dfRowCount == 0:
                    self.df = pd.DataFrame.from_dict([newData])
                else:
                    self.df = pd.concat([self.df, pd.DataFrame([newData])],ignore_index=True)

                # update the plots
                for v in self.plotVariable:
                    self.curve[v].setData(self.df[self.timeKey], self.df[v])

                # modify y-axis to show variable name and units
                if self.firstLoop:
                    for v in self.plotVariable:
                        self.plot[v].setLabel('left', v, units=recvUnit[v])
                    self.firstLoop = False

                # format the text field(s)
                self.lblTextData.setText("Temperature: {} {}".format(newData['T'],recvUnit['T']))

        except KeyboardInterrupt:
            log_message("GUI", "aborted by user!")
            self.sock.close()
            exit()

        except:
            log_message("GUI", "    --- error type: " + str(sys.exc_info()[0]))
            log_message("GUI", "    --- error value: " + str(sys.exc_info()[1]))
            exec_tb = sys.exc_info()[2]
            fname = os.path.split(exec_tb.tb_frame.f_code.co_filename)[1]
            log_message("GUI", "    --- error File: {}".format(fname))
            log_message("GUI", "    --- error line: {}".format(exec_tb.tb_lineno))
            
##            raise

    def closeSocket(self):
        log_message("GUI", "Window is clossing!")
        log_message("GUI", "Closing the active socket")
        self.sock.close()
        log_message("GUI", "bye...")

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
    timer.start()

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtWidgets.QApplication.instance().exec_()
