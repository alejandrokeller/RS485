# RS485logger

## Description

This application is written to monitor diferent variables from an RS485 capable device.

Based on the [Waveshare USB to RS485B](https://www.waveshare.com/wiki/USB_TO_RS485_(B))

Currently supporting these sensors: 
- Truebner AquaFlex and SMT100 soil mosture sensors (see e.g. [SMT100 Instruction Manual](https://www.truebner.de/assets/download/Anleitung_SMT100_V1.1.pdf)).
- Ionscience [Falco Pumped Gas Detector series](https://ionscience.com/en/products/products-falco-fixed-voc-gas-detector-pumped-0-10ppm/).

Tested using python3.9.2 on a Raspberry Pi 4B

## Installation

1. Clone the repository. In this example we are clonning to `/logger`):   
   ```
   sudo git clone https://gitlab.fhnw.ch/alejandrokeller/rs485logger.git /logger
   ```
2. Install requirements:

   ```
   cd /logger
   sudo pip install -r requirements.txt
   ```
3. Conect the  usb to RS485B converter. In the raspberry pi, the usb to RS485B converter works using the default (already installed) driver. You can find out the converter serial port by running the following command before and after connecting the adapter:

   ```
   ls /dev/tty*
   ```
   If you want to test the device, ycou can use, e.g., [minicom](https://www.waveshare.com/wiki/Raspberry_Pi_Tutorial_Series:_Serial):

   ```
   minicom -b 9600 -D /dev/ttyUSB0
   ```
   - -D Specify the device, overriding the value given in the configuration file. The followed device, `/dev/ttyUSB0`, is the serial device specified by -D
   - The baud rate of serial is set to 115200 by default, which can be changed by `-b 9600`. You can read the detailed manual with the command man minicom

4. Create the the data and logging directories:
   ```
   mkdir  ~/logger/ ~/logger/logs
   ```
5. Create a `/logger/config.ini`. You can simply copy and modify an appropiate `config.ini` file located at in the `config_templates` to the logger directory (in this example use `/logger/config.ini` as destitantion).

   Variables in `config.ini`:
   * `PORT: '/dev/ttyUSB0'` (or the serail address from step 3)
   * `ADDRESS: 3` (or the MODBUS address of the sensor)
   * `LOGS_PATH: '/home/pi/logger/logs'` (or the directory created in step 4)
   * `DATA_PATH: '/home/pi/logger/data'` (or the directory created in step 4)
   * `HOST_NAME: '127.0.0.1'` (The ip used for the gui intgerface. Leave it like this if the logger and the gui are on the same computer)
   * `HOST_PORT: 10000` (The port for data transmission to the gui. 10000 is usually free. Some firewalss may block this port if transmitting to another computer. Check your system documentation)
   * `BUFFER: 120` (Lines to be captured before writting to the data file. Example: 120 for a system with 2 Hz rate to write only once a minute)
   * `DATAFILE: 'rs485data'` (base name for datafile. Date and time of creation will be appended)
   * `EXTENSION: '.csv'` (extension for the datafile. Per default the system creates columns separated with tab)
   * `JSON_CONFIG: '/logger/config_templates/falco/config.falco.json'` (file for formating the GUI window)

   The last variable points to a file containing the configuration of the GUI. Do not modify the example json files, as they are linked to this repository. It is better to create a new json file if you need to modify the settings. Afterwards, point the `JSON_CONFIG`variable to the newly created file.

6. Create a bash script to start logger and gui (e.g. `nano ~/Desktop/run_logger.sh`). Then write the following commands (substitute the location with the installation directory and the log file directory):
   ```
   #!/usr/bin/env bash
   python /logger/logger.py 2>> /home/pi/logger/logs/logfile.txt &
   python /logger/gui.py 2>> /home/pi/logger/logs/logfile.txt &
   ```
   Make the script executable using `chmod +x ~/Desktop/run_logger.sh`. Now you can double click on the icon to start logging and displaying the data. 
   By usig the `2>>` log messages are redirected from `stderr` and appended to a file.

## Usage
comming soon...

## JSON_CONFIG file

The `JSON_CONFIG` file defines the appearance of GUI. You can choose to have one or more tabs displaying variables in graphics. Additionally, it is posible to display information text with below the tabs. This is the example file prepared for the falco VOC instrument (i.e. `config.falco.json`):
```
{"variables": ["VOC", "Voltage", "T", "RF", "Range"],
 "plots": [
     {"var": "VOC", "tab": 0, "plot": 0, "pen": 0, "label": "VOC"},
     {"var": "Voltage", "tab": 1, "plot": 0, "pen": 1},
     {"var": "T", "tab": 1, "plot": 1, "pen": 2, "label": "Sensor Temp."}],
 "tabslabels": ["&VOC","&Other"],
 "infotext": {"text": "Sensor temperature: {} degC, Correction Factor (RF): {}, Range: {} ppm",
              "variables": ["T","RF","Range"]}}
```

The JSON dictionaries are organized as following:

* `"variables"` is a list of the variables that will be kept for displaying. 
* `"plots"` is a list of the plots (with a length defined by the `BUFFER` variable of the `config.ini`). Each plot is specified by the following dictionary:
   * `"var"`: Name of the variable to plot.
   * `"tab"`: Number of the tab where the plot will be shown.
   * `"plot"`: Number of the plot within the relevant tab (you can display several variables per plot) 
   * `"pen"`: Style of the line. Currently only 4 pens defined (0 -> solid yellow, 1 -> dash yellow, 2 -> solid red, 3 -> dash red)
   * `"label"`: (optional) Name that will be used to identify the curve. Omit this to use the variable name.
* `"tabslabels"` text to display on each tab. Numbers are asigned for the tabs withoiut names.
* `"infotext"`: Text to be display bellow the tabs. This text is used in the same way as the python format method for strings.

Here is the result of the `config.falco.json` file:
 

## Support
Please contact me under alejandro.keller@fhnw.ch for feedback or issues with this repository.
