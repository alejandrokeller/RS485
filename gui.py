#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# listens to a TCP broadcast and displays data using Ppyqt widgets
# provides also a buttons interface for interacting with the 
# measurement instrument

from PyQt5 import QtGui, QtCore, QtWidgets
import PyQt5 as pg
import socket
import sys, os
import numpy as np
import pandas as pd
import datetime
import json
import configparser

base_path = os.path.abspath(os.path.dirname(sys.argv[0]))

def send_string(line, server_address, sock = 0):
    # Sends a string to through a TCP socket

    # Send data
    try:
        if not sock:
            # Create a TCP/IP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(server_address)
            
        sock.sendall(line)
    except socket.error:
##        print("nobody listening", file = sys.stderr)
        sock.close()
##        print('closing socket', file = sys.stderr)
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
#        pg.setConfigOptions(antialias=False)
#        pg.setConfigOption('foreground', 'w')

        #init data structure
        self.numSamples = 1200 
        self.datastring = ""

        self.keys = [
            "T",
            "Moist",
            "Count"
            ]
        
        self.units = [
            "°C",       # T
            "vol%",     # Moist
            "-"         # Count
            ]

        zeroDict = []
        zeroDict[self.keys[1]] = 0.0
        zeroDict[self.keys[2]] = 0.0
        zeroDict[self.keys[3]] = 0

#        self.t = np.linspace(datetime.now() - datetime.timedelta(minutes=10), datetime.now(), self.numSamples)
        self.t = np.linspace(-self.deltaT*self.numSamples, 0, self.numSamples)


        self.unitsDict = dict(zip(self.keys, self.units))
        self.df = pd.DataFrame(columns=self.keys)
        self.df = pd.concat([self.df, pd.DataFrame([zeroDict]*self.numSamples)],ignore_index=True)

        # setup plots
        self.pen = pg.mkPen('y', width=1)

###        self.Tplot = self.win.addPlot(row=0, col=0, title="")
        self.Tplot = pg.PlotWidget()
        self.Tplot.addLegend()
#        self.Tplot.setRange(yRange=[0, 900])
        self.Tplot.setLabel('left', "Temperature", units='°C')
        self.Tplot.setLabel('bottom', "t")
        self.Tplot.showGrid(False, True)
        self.Tcurve = self.Tplot.plot(self.t, self.df['T'].astype(str).astype(float), pen=self.pen)

        self.Mplot = pg.PlotWidget()
        self.Mplot.setRange(yRange=[50, 100])
        self.Mplot.setLabel('left', "Moist.", units='vol%')
        self.Mplot.setLabel('bottom', "t")
        self.Mplot.showGrid(False, True)
        self.Mcurve = self.Mplot.plot(self.t, self.df['Moist'], pen=self.pen)

#####################################################################

        ## Define a top level widget to hold the controls
        self.widgets = QtWidgets.QWidget()
        self.widgets.setWindowTitle("RS485 Logger")
        self.widgets.showFullScreen()

        self.lblCounts    = QtWidgets.QLabel("Counts: ")

        ## Create a QVBox layout to manage the plots
        self.plotLayout = QtWidgets.QVBoxLayout()

        self.plotLayout.addWidget(self.Mplot)
        self.plotLayout.addWidget(self.Tplot)
        self.plotLayout.addWidget(self.lblCounts)

        ## Create a QHBox layout to manage the plots
        self.centralLayout = QtWidgets.QHBoxLayout()
        self.centralLayout.addLayout(self.plotLayout)

        ## Display the widget as a new window
        self.widgets.setLayout(self.centralLayout)
        self.widgets.show()

    def update(self):

        try: 
            self.datastring = self.connection.recv(1024)
            dataDict = json.load(self.datastring)

            if self.datastring:
               #Eliminate first element
                self.df = self.df[1:self.numSamples]
                newData = self.df.iloc[[-1]].to_dict('records')[0]
                for k in self.keys:
                    try:
                        newData[k] = dataDict[k]['val']
                    except:
                        print("could not extract ", k, " value from ", dataDict)

                self.df = pd.concat([self.df, pd.DataFrame([newData])],ignore_index=True)

                self.Tcurve.setData(self.t, self.df['T'])
                self.Mcurve.setData(self.t, self.df['Moist'])

                self.lblCounts.setText("Counts: {})".format(newData['Count']))
                
        except Exception as e:
            print(e, file=sys.stderr)
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
    timer.start(vis.deltaT*1000)

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtWidgets.QApplication.instance().exec_()
