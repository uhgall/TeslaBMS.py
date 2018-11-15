# this is a temporay hack specific to my setup.
# it turns off the PV in for both MPPT controllers whenever the voltage is too high on any cell. 


import sys
sys.path.insert(0, './lib')
from tesla_bms import BMSBus
from tesla_bms import BMSBoard

import time

MAX_CELL_VOLT = 3.0
MAX_TEMP = 80

class MyLog:
  
  def __init__(self):
    self.out = open("log/{}.txt".format(self.time_stamp()), "w")

  def log(self,cat,s):
    line = "{}, {}, {}".format(s)
    self.out.write(line)    

  def time_stamp(self):
    return(time.strftime("%Y-%m-%d-%H.%M.%S", time.gmtime()))

log = MyLog()
bus = BMSBus('A907CBEU',log)

print("Found {} boards.".format(len(bus.boards)))

while True:
  for board in self.boards:
    board.update()
    print(board)
    mppt = 1 # on 
    if max(board.cellVolt) > MAX_CELL_VOLT:
      print("--> STOPPING MPPT CHARGERS until all voltages are below {}".format(MAX_CELL_VOLT))
      mppt = 0
    if max(board.temperatures) > MAX_TEMP:
      print("--> STOPPING MPPT CHARGERS until temperatures are below {}".format(MAX_TEMP))
      mppt = 0
    relay(1,mppt)
  time.sleep(10)