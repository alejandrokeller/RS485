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
5. Modify `/logger/config.ini`:
   * `PORT: '/dev/ttyUSB0'` (or the serail address from step 3)
   * `ADDRESS: 3` (or the MODBUS address of the sensor)
   * `LOGS_PATH: '/home/pi/logger/logs'` (or the directory created in step 4)
   * `DATA_PATH: '/home/pi/logger/data'` (or the directory created in step 4)
   * `HOST_NAME: '127.0.0.1'` (The ip used for the gui intgerface. Leave it like this if the logger and the gui are on the same computer)
   * `HOST_PORT: 10000` (The port for data transmission to the gui. 10000 is usually free. Some firewalss may block this port if transmitting to another computer. Check your system documentation)
   * `BUFFER: 120` (Lines to be captured before writting to the data file. Example: 120 for a system with 2 Hz rate to write only once a minute)
   * `DATAFILE: 'rs485data'` (base name for datafile. Date and time of creation will be appended)
   * `EXTENSION: '.csv'` (extension for the datafile. Per default the system creates columns separated with tab)

## Usage
comming soon...

## Support
Please contact me under alejandro.keller@fhnw.ch for feedback or issues with this repository.
