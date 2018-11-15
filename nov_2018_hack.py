# this is a temporay hack specific to my setup.
# it turns off the PV in for both MPPT controllers whenever the voltage is too high on any cell. 


import sys
sys.path.insert(0, './lib')
from tesla_bms import BMSBus
from tesla_bms import BMSBoard
from relay import Relay

import time

MAX_CELL_VOLT = 3.9
MAX_TEMP = 80

def time_stamp():
  return(time.strftime("%Y-%m-%d-%H.%M.%S", time.gmtime()))

class MyLog:
  
  def __init__(self):
    self.out = open("log/{}.txt".format(time_stamp()), "w")
    self.stats = open("log/{}.csv".format(time_stamp()), "w")

  def log(self,cat,s):
    line = "{}, {}, {}\n".format(time_stamp(),cat,s)
    self.out.write(line)    
    if not cat == "debug" and not cat == "info":
       print(line)

  def record_row(self,s):
    self.stats.write(line)   


log = MyLog()
bus = BMSBus('A907CBEU',log)
mppt = Relay(2)

print("Found {} boards.".format(len(bus.boards)))

while True:
  print("\nChecking modules at {}, will stop all charging if any voltage is above {}...".format(time_stamp(), MAX_CELL_VOLT))
  for board in bus.boards:
    board.update()

    log.record_row(board.csv_row)
    
    if board.address == 14:
      print("Spare battery:")
    print(board)
    if max(board.cellVolt) > MAX_CELL_VOLT:
      print("--> STOPPING MPPT CHARGERS until all voltages are below {}".format(MAX_CELL_VOLT))
      mppt.set(0)
    elif max(board.temperatures) > MAX_TEMP:
      print("--> STOPPING MPPT CHARGERS until temperatures are below {}".format(MAX_TEMP))
      mppt.set(0)
    else:
      mppt.set(1)
  time.sleep(2)
