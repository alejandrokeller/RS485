import minimalmodbus

class Falco( minimalmodbus.Instrument ):
    """Instrument class for ION Falco VOC Measurement Device.

    Args:
        * portname (str): port name
        * slaveaddress (int): slave address in the range 1 to 247

    """

    def __init__(self, portname, slaveaddress):
        minimalmodbus.Instrument.__init__(self, portname, slaveaddress, mode=minimalmodbus.MODE_RTU)
        
        #Make the settings explicit
        self.serial.baudrate = 19200        # Baud
        self.serial.bytesize = 8
        self.serial.parity   = minimalmodbus.serial.PARITY_NONE
        self.serial.stopbits = 1
        self.serial.timeout  = 1          # seconds

        # Good practice
        self.close_port_after_each_call = True
        self.clear_buffers_before_each_transaction = True

    def get_voc(self):
        """Return the Gas concentration. 32 bit float, 2 Registers"""
        return self.read_register(102, 1)

    def get_voltage(self):
        """Return the sensor voltage in mV. 32 bit float, 2 Registers"""
        return self.read_register(106, 1)

    def get_temperature(self):
        """Return the sensor temperature in degC. 16 bit signet int, 1 Register"""
        return self.read_register(108, 1)

    def get_led(self):
        """Return the led brightness. 16 bit unsignet int [0-100], 1 Register"""
        return self.read_register(182, 1)

    def get_version(self):
        """Return the hardware version. 16 bit unsignet int [1-255], 1 Register"""
        return self.read_register(1003, 1)

    def get_unit(self):
        """Return the measurement unit. char ['p' or 'g'], 1 Register"""
        return self.read_register(1005, 1)

    def get_rf(self):
        """Return the response factor. 32 bit float [0.1 - 10.0], 2 Registers"""
        return self.read_register(1010, 1)

    def get_range(self):
        """Return the sensor range. 16 bit unsignet int [10, 50, 1000, 3000], 1 Register"""
        return self.read_register(1012, 1)

    def get_range(self):
        """Return the sensor range. 16 bit unsignet int [10, 50, 1000, 3000], 1 Register"""
        return self.read_register(1012, 1)

    def get_cal100(self):
        """Return the cal 100 value. 16 bit unsignet int [0 - 65535 (Default value 500) ], 1 Register"""
        return self.read_register(1060, 1)

    def get_cal3000(self):
        """Return the cal 3000 value. 16 bit unsignet int [0 - 65535 (Default value 3000) ], 1 Register"""
        return self.read_register(1061, 1)

    


