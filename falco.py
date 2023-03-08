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
        return self.read_float(102, 1)

    def get_voltage(self):
        """Return the sensor voltage in mV. 32 bit float, 2 Registers"""
        return self.read_float(106, 1)

    def get_temperature(self):
        """Return the sensor temperature in degC. 16 bit signet int, 1 Register"""
        return self.read_register(108, 1, signet = True)

    def get_led(self):
        """Return the led brightness. 16 bit unsignet int [0-100], 1 Register"""
        return self.read_register(182, 1)

    def get_version(self):
        """Return the hardware version. 16 bit unsignet int [1-255], 1 Register"""
        return self.read_register(1003, 1)

    def get_unit(self):
        """Return the measurement unit. char ['p' or 'g'], 1 Register
        
        This translates to p = ppm or g = mg/m3.
        """
        u = self.read_string(1005, 1, number_of_registers = 1)
        match u:
        case 'p':
            return 'ppm'
        case 'g':
            return 'mg/m3'
        case _:
            return 'ppm'   # ppm is the default case if u is not found

        # return self.read_string(1005, 1, number_of_registers = 1)

    def get_rf(self):
        """Return the response factor. 32 bit float [0.1 - 10.0], 2 Registers"""
        return self.read_float(1010, 1)

    def get_range(self):
        """Return the sensor range. 16 bit unsignet int [10, 50, 1000, 3000], 1 Register"""
        return self.read_register(1012, 1)

    def get_cal100(self):
        """Return the cal 100 value. 16 bit unsignet int [0 - 65535 (Default value 500) ], 1 Register"""
        return self.read_register(1060, 1)

    def get_cal3000(self):
        """Return the cal 3000 value. 16 bit unsignet int [0 - 65535 (Default value 3000) ], 1 Register"""
        return self.read_register(1061, 1)

    def readline(self):
        """Return a list of dictionaries with current data.

        dictionary keys are:
            'var' -> variable name string
            'val' -> value
            'unit' -> unit string when applicable, otherwise '-'
        """
        response = [
            {'var': 'VOC',
            'val': self.get_voc(),
            'unit': '-'},
            {'var': 'Unit',
            'val': self.get_unit(),
            'unit': '-'},
            {'var': 'Voltage',
            'val': self.get_voltage(),
            'unit': 'mV'},
            {'var': 'T',
            'val': self.get_temperature(),
            'unit': 'degC'},
            {'var': 'RF',
            'val': self.get_rf(),
            'unit': '-'},
            {'var': 'Range',
            'val': self.get_range(),
            'unit': '-'},
            {'var': 'Cal100',
            'val': self.get_cal100(),
            'unit': '-'},
            {'var': 'Cal3000',
            'val': self.get_cal3000(),
            'unit': '-'}
        ]

        return response



        

    


