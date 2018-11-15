from pylibftdi import Device
import time
import math

#define REG_DEV_STATUS      1
REG_GPAI = 1
#define REG_VCELL1          3
#define REG_VCELL2          5
#define REG_VCELL3          7
#define REG_VCELL4          9
#define REG_VCELL5          0xB
#define REG_VCELL6          0xD
#define REG_TEMPERATURE1    0xF
#define REG_TEMPERATURE2    0x11
#define REG_ALERT_STATUS    0x20
#define REG_FAULT_STATUS    0x21
#define REG_COV_FAULT       0x22
#define REG_CUV_FAULT       0x23
REG_ADC_CTRL  =       0x30
REG_IO_CTRL   =       0x31
REG_BAL_CTRL  =       0x32
REG_BAL_TIME  =       0x33
REG_ADC_CONV  =       0x34
REG_ADDR_CTRL =       0x3B

#define MAX_MODULE_ADDR     0x3E
#define EEPROM_VERSION      0x10    //update any time EEPROM struct below is changed.
#define EEPROM_PAGE         0

REG_ALERT_STATUS = 0x20

def hex(arr):
    return(''.join(' {:02x}'.format(x) for x in arr))

def tempCalc(b1,b2):
    # tempTemp = (1.78f / (     (buff[17] * 256 + buff[18] + 2)   / 33046.0f) - 3.57f);
    t = 1000 * (1.78*float(33046) / (int(b1) * 256 + int(b2) + 2)  - 3.57)
    if t <= 0:
        error("Bad temperature reading: b1={}, b2={}, val = {}".format(b1,b2,t))
    # tempCalc =  1.0f / (0.0007610373573f + (0.0002728524832 * logf(tempTemp)) + (powf(logf(tempTemp), 3) * 0.0000001022822735f));            
    t = 1 / (0.0007610373573 + 0.0002728524832 * math.log(t) + 0.0000001022822735 * (math.log(t)**3))
    return(t - 273.15)          

def genCRC(data):
    generator = 7
    crc = 0
    for b in data:
        crc = crc ^ b 
        for i in range(8):
            if (crc & 0x80) != 0:
                crc = ((crc << 1) ^ generator) & 255
            else:
                crc <<= 1
    # Note: genCRC([x1, x2, ... xn]) == 0 iff genCRC([x1,x2,...xn-1]) == xn
    return(crc) 

class BMSBoard:
    def __init__(self, bus, address,logger):
        self.logger = logger
        self.bus = bus
        self.address = address
        self.log("debug","Created BMSBoard {}.".format(address))

    def log(self,cat,s):
        self.logger.log(cat,s)

    def __str__(self):
        s = "BMS Board {:2d} ".format(self.address)
        s += "Alerts: {}, Faults: {} ".format(self.alerts, self.faults)
        s += " (Over Voltage: {}, Under: {})".format(self.cov_faults, self.cuv_faults)
        s += ", Voltages = "+"".join("{0:.4f}V ".format(v) for v in self.cellVolt)
        s += ", Temps = {0:.2f}C {1:.2f}C".format(self.temperatures[0],self.temperatures[1])
        return s

    def csv_list(self):
        list = [self.address, self.alerts, self.faults, self.cov_faults, self.cuv_faults]
        list.append()

    def update(self):
        self.readStatus()
        self.readModuleValues()
        self.log("info", "Board {} status: {}".format(self.address,self))

    def send_and_receive_reply(self, command, param, isWrite = False):
        return(self.bus.send_and_receive_reply_to(self.address,command, param, isWrite))

    def readStatus(self):
        r = self.send_and_receive_reply(REG_ALERT_STATUS,4)
        self.alerts,self.faults,self.cov_faults, self.cuv_faults = r[3:7]

    def readModuleValues(self):
        # ADC Auto mode, read every ADC input we can (Both Temps, Pack, 6 cells)
        self.send_and_receive_reply(REG_ADC_CTRL, 0b00111101, True)
        # enable temperature measurement VSS pins
        self.send_and_receive_reply(REG_IO_CTRL, 0b00000011, True)
        # start all ADC conversions        
        self.send_and_receive_reply(REG_ADC_CONV, 1, True)
        r = self.send_and_receive_reply(REG_GPAI,0x12)
        if (len(r) != 22):
            self.log("error","readModuleValues expected 22 bytes but got {}".format(len(r)))
        else:
            # payload is 2 bytes gpai, 2 bytes for each of 6 cell voltages, 
            # 2 bytes for each of two temperatures (18 bytes of data)
            self.moduleVolt = (r[3] * 256 + r[4]) * 0.002034609
            self.cellVolt = [(r[5 + (i * 2)] * 256 + r[6 + (i * 2)]) * 0.000381493 for i in range(6)]
            self.temperatures = [tempCalc(r[17],r[18]),tempCalc(r[19],r[20])]
#       # //turning the temperature wires off here seems to cause weird temperature glitches
        # r = self.send_and_receive_reply(REG_IO_CTRL,0,True) #//turn off temperature measurement pins

    def balance_cells_above_voltage(self,v):
        # This code is translated from the cpp code to my python API
        # It's not even clear to me what "balancing" means here... what happens with a cell when it's being "balanced"? 
        # Does it just mean that during charging, some of the current bypasses the cell? 
        # ie, a more accurate term would be "bypass_cells" or "shunt_cells" ?
        # If so, then I think thius code can't work, because most of the batteries would always be "balancing".
        # The reason is that it's comparing floats, with no tolerance. Almost all cells will always be below the max. 
        # It should just be bypassing the cell with the HIGHEST voltage, no? 
        bitmask = 0
        for i in range(0,5):
            if self.voltages[i] > v:
                bitmask += 2**i
        # //5 second balance limit, if not triggered to balance it will stop after 5 seconds
        cpp_ignores_reply = self.send_and_receive_reply(REG_BAL_TIME,5,true) 

        # //write balance state to register
        cpp_ignores_reply = self.send_and_receive_reply(REG_BAL_CTRL,bitmask,true) 


        # UG: cpp code does this - reading only. But, then again ignoring the reply
        cpp_ignores_reply = self.send_and_receive_reply(REG_BAL_TIME,1,false) 
        cpp_ignores_reply = self.send_and_receive_reply(REG_BAL_CTRL,1,false) 



class BMSBus:

    def __init__(self,device_name,logger):
        self.logger = logger
        self.device = Device(device_name)
        self.log("info", "Initializing BMSBus on Device {}".format(device_name))
        self.device.baudrate = 612500
        self.device.open()
        self.findBoards()

    def log(self,cat,s):
        self.logger.log(cat,s)

    def findBoards(self):
        self.boards = []
        for i in range(1,62):
            r = self.send_and_receive_reply_to(i,0,1)
            if r[0] == 2*i and r[1] == 0 and r[2] == 1 and len(r) == 3:
                pass # this just means this board does not exist
            elif len(r) != 5:
                self.log("error", "Unexpected response to init (0,1,{}): {}".format(i,hex(r)))
            else:
                self.log("debug","BMSBoard {} responded to init with {}".format(i,hex(r)))
                self.boards.append(BMSBoard(self,i,self.logger))
            time.sleep(0.005)
        for board in self.boards:
            board.update()

    def send_and_receive_reply_to(self,destination, command, param, isWrite = False):
        dest = 2*destination +1 if isWrite else 2*destination
        payload = bytearray([dest, command, param])
        if isWrite:  # original code was doing weird things that I think amounted to nothing. So I simplified.
            crc = genCRC(payload)
            # isWrite, therefore adding CRC = {}".format(crc))
            payload.append(crc)
        self.device.write(payload)
        self.log("debug", "Sent: {}".format(hex(payload)))
        time.sleep(0.02)
        reply = bytearray(self.device.read(100))
        if isWrite and genCRC(reply) != 0:
            self.log("error","CRC error: Reply to {} was {}".format(hex(payload), hex(reply)))
        return(reply)


# def test_crc():
#     a = [10,10,10,51]
#     print(genCRC(a))

#test_crc()

