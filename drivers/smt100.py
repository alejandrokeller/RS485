import minimalmodbus

class SMT100( minimalmodbus.Instrument ):
    """Instrument class for ION Falco VOC Measurement Device.

    Args:
        * portname (str): port name
        * slaveaddress (int): slave address in the range 1 to 247

    """

    def __init__(self, portname, slaveaddress):
        minimalmodbus.Instrument.__init__(self, portname, slaveaddress, mode=minimalmodbus.MODE_RTU)
        
        #Make the settings explicit
        self.serial.baudrate = 9600        # Baud
        self.serial.bytesize = 8
        self.serial.parity   = minimalmodbus.serial.PARITY_EVEN
        self.serial.stopbits = 1
        self.serial.timeout  = 1          # seconds

        # Good practice
        self.close_port_after_each_call = True
        self.clear_buffers_before_each_transaction = True
        
        print("SMT initialized in port {}:{}".format(portname, slaveaddress))

    def get_temp(self):
        """Return the soil temperature in degC. 16 bit unsignet int, 1 Register"""
        temperature = self.read_register(0)/100.0 - 100.0

        return round(temperature,1)

    def get_moist(self):
        """Return the soil moisture reading in vol%. 16 bit unsignet int, 1 Register"""
        response = self.read_register(1)/100.0

        return round(response,1)

    def get_perm(self):
        """Return the soil permittivity reading in arb. units. 16 bit unsignet int, 1 Register"""
        return self.read_register(2)

    def get_count(self):
        """Return the led brightness in arb. units. 16 bit unsignet int, 1 Register"""
    
        return self.read_register(3)

    def readline(self):
        """Return a list of dictionaries with current data.

        dictionary keys are:
            'var' -> variable name string
            'val' -> value
            'unit' -> unit string when applicable, otherwise '-'
        """
        response = [
            {'var': 'T',
            'val': self.get_temp(),
            'unit': 'degC'},
            {'var': 'Moist',
            'val': self.get_moist(),
            'unit': 'vol%'},
#             {'var': 'Perm',
#             'val': self.get_perm(),
#             'unit': '-'},
            {'var': 'Count',
            'val': self.get_count(),
            'unit': '#'}
        ]

        return response
