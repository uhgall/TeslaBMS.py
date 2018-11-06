from pylibftdi import Device
device = Device('A907CBEU')
device.baudrate = 612500
device.open()
device.write('?\r')             #send an identity query command.
                                #This device needs \r to end command.
device.readlines()              #Return data in buffer
device.close()                  #Close the device