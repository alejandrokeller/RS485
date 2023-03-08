import falco

PORT='/dev/ttyACM0'

#Set up instrument
sensor = falco.Falco(PORT,1)

#Pront the values
print('The temperature is: %.1f deg C\r' % sensor.get_temperature())
print('The voc concentration is: %.1f ppm (%.1f mV)\r'.format(sensor.get_voc(), sensor.get_voltage()))
