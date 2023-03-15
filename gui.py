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
    def __init__(self, host_name='localhost', host_port=10000, json_config=False):
        
        # init socket
        self.host_name = host_name
        self.host_port = host_port
        self.initSocket()

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
        if not json_config:
            json_config=basepath+'/config.json'

        with open(json_config, "r") as jsonfile:
            json_data = json.load(jsonfile)
            log_message("GUI","Imported configuration: {}".format(json_config))

        self.keys = json_data['variables']
        self.keys.append(self.timeKey)
        self.plotVariable = json_data['plots']
        self.tabLabel = json_data['tabslabels']
        self.infoText = json_data['infotext']
            
        # pen styles
        self.pen = [
            pg.mkPen('y', width=1),
            pg.mkPen('y', width=1, style=QtCore.Qt.DashLine),
            pg.mkPen('r', width=1),
            pg.mkPen('r', width=1, style=QtCore.Qt.DashLine)
        ] 
        
        # dataframe that will hold the data
        self.df = pd.DataFrame(columns=self.keys)

        # setup plots
        self.curve = {}
        lastTab  = max(self.plotVariable, key=lambda x:x['tab'])
        self.plot = []        
        lastPlot = max(self.plotVariable, key=lambda x:x['plot'])
        
        for t in range(lastTab['tab'] + 1):
            self.plot.append([])
            for p in range(lastPlot['plot'] + 1):
                self.plot[t].append(pg.PlotWidget(
                    axisItems={'bottom':TimeAxisItem(orientation='bottom')}))
                #self.plot[t].setRange(yRange=[50, 100])
                self.plot[t][p].addLegend()
                self.plot[t][p].setLabel('bottom', "Time")
                self.plot[t][p].showGrid(False, True)
                
        for index in range(len(self.plotVariable)):
            p = self.plotVariable[index]['plot']
            t = self.plotVariable[index]['tab']
            lbl = self.plotVariable[index].get('label')
            if not lbl:
                lbl = self.plotVariable[index]['var']
            self.curve[index] = self.plot[t][p].plot([], [],
                                        pen=self.pen[self.plotVariable[index]['pen']],
                                        name=lbl)

#####################################################################

        ## Define a top level widget to hold the controls
        self.widgets = QtWidgets.QWidget()
        self.widgets.setWindowTitle("RS485 Logger")
        self.widgets.showFullScreen()

        # text field to hold info from another variable
        self.lblTextData    = QtWidgets.QLabel("")

        ## Creata tabs to manage plots
        self.tabWidget = QtWidgets.QTabWidget()
        self.tabContentWidget = []
        self.tabLayout = []

        ### Create the tabs and plot layouts
        lastTab = max(self.plotVariable, key=lambda x:x['tab'])
        for index in range(lastTab['tab'] + 1):
            self.tabLayout.append(QtWidgets.QVBoxLayout())
            self.tabContentWidget.append(QtWidgets.QWidget())
            if index < len(self.tabLabel):
                lbl = self.tabLabel[index]
            else:
                lbl = "Tab &{}".format(index+1)
            self.tabWidget.addTab(self.tabContentWidget[index], lbl)
            self.tabContentWidget[index].setLayout(self.tabLayout[index])

        ## add the plots
        for index in range(len(self.plotVariable)):
            p = self.plotVariable[index]['plot']
            t = self.plotVariable[index]['tab'] 
            self.tabLayout[self.plotVariable[index]['tab']].addWidget(
                self.plot[t][p])

        ## Create a QHBox layout for buttons and other info
        self.infoLayout = QtWidgets.QHBoxLayout()
        self.infoLayout.addWidget(self.lblTextData)

        ## Create a QVBox layout to manage the tabs and other info
        self.centralLayout = QtWidgets.QVBoxLayout()
        self.centralLayout.addWidget(self.tabWidget)
        self.centralLayout.addLayout(self.infoLayout)


        ## Display the widget as a new window
        self.widgets.setLayout(self.centralLayout)
        self.widgets.show()

    def update(self):

        try:
            # wait for new data to arrive
            self.datastring = self.connection.recv(1024).decode()
            if not self.datastring:
                log_message("GUI", "Nothing received!")
                log_message("GUI", "Trying to reconnect.")
                self.connection, self.client_address = self.sock.accept() # Wait for a connection
                log_message("GUI",'connection from {}'.format(self.client_address))


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
                           log_message("GUI","could not extract {} value from {}".format(k, dataDict))
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
                for index in range(len(self.plotVariable)):
                    self.curve[index].setData(self.df[self.timeKey], self.df[self.plotVariable[index]['var']])

                # modify y-axis to show variable name and units
                if self.firstLoop:
                    for index in range(len(self.plotVariable)):
                        p = self.plotVariable[index]['plot']
                        t = self.plotVariable[index]['tab']
                        self.plot[t][p].setLabel('left',
                            self.plotVariable[index]['var'],
                            units=recvUnit[self.plotVariable[index]['var']])
                        
                    self.firstLoop = False

                # format the text field(s)
                infoData = []
                for v in self.infoText['variables']:
                    infoData.append(newData[v])
                self.lblTextData.setText(
                    self.infoText['text'].format(*infoData))

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
    def initSocket(self):
        # init socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create a TCP/IP socket
        self.server_address = (self.host_name, self.host_port)
        log_message("GUI",'starting up on {}'.format(self.server_address))
        self.sock.bind(self.server_address) # Bind the socket to the port
        self.sock.listen(1) # Listen for incoming connections
        log_message("GUI",'waiting for a connection')
        self.connection, self.client_address = self.sock.accept() # Wait for a connection
        log_message("GUI",'connection from {}'.format(self.client_address))

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
        json_config = eval(config['GUI']['JSON_CONFIG'])
    else:
        log_message("GUI","Could not find the configuration file: {}".format(config_file))
        exit()


    vis = Visualizer(host_name=host_name, host_port=host_port, json_config=json_config)

    timer = QtCore.QTimer()
    timer.timeout.connect(vis.update)
    timer.start()

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtWidgets.QApplication.instance().exec_()
