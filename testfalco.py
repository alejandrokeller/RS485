import configparser, os, sys

# Script directory
base_path = os.path.abspath(os.path.dirname(sys.argv[0]))

# Script directory
sys.path.append(base_path + '/drivers/')
import falco

# READ ini file
config_file = base_path + '/config.ini'
if os.path.exists(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    
    falco_port          = eval(config['GENERAL_SETTINGS']['PORT'])
    falco_address       = eval(config['GENERAL_SETTINGS']['ADDRESS'])
else:
    print( "Could not find the configuration file: {}".format(config_file) , file = sys.stderr)
    exit()
    
#Set up instrument
print( "Connecting to falco sensor at port {} and address {}".format(
                                      falco_port, falco_address),
                                      file = sys.stderr)
sensor = falco.Falco(falco_port,falco_address)

#Print the values
print('The voc concentration is: {:.1f} {} ({:.1f} mV)'.format(
    sensor.get_voc(), sensor.get_unit(), sensor.get_voltage()))
print('The temperature is: {:.1f} deg C'.format(sensor.get_temperature()))

