# this is a temporay hack specific to my setup.
# it turns off the PV in for both MPPT controllers whenever the voltage is too high on any cell. 


import sys
sys.path.insert(0, './lib')
from tesla_bms import BMSBus
from tesla_bms import BMSBoard
from relay import Relay

import time

MAX_CELL_VOLT = 3.82
MAX_CELL_VOLT_IN = 3.78

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

  def record_row(self,row):
    self.stats.write(",".join([str(x) for x in row]))   
    #print(list)

log = MyLog()
bus = BMSBus('A907CBEU',log)
mppt = Relay(2)

print("Found {} boards.".format(len(bus.boards)))

mppt_status = 0

while True:
  print("\nChecking modules at {}, will stop all charging if any voltage is above {}...".format(time_stamp(), MAX_CELL_VOLT))
  if mppt_status == 1:
    print("Charging is currently ON.")
  else:
    print("Charging is currently turned OFF to protect the batteries.")
  for board in bus.boards:
    board.update()
    log.record_row(board.csv_list())
    if board.address == 14:
      print("Spare battery:")
    print(board)
  global_max_volt = max([max(board.cellVolt) for board in bus.boards])
  global_max_t = max([max(board.temperatures) for board in bus.boards])
  if mppt_status == 1: 
    if global_max_volt > MAX_CELL_VOLT:
      print("--> STOPPING MPPT CHARGERS until all voltages are below {}".format(MAX_CELL_VOLT_IN))
      mppt_status = 0
    elif global_max_t > MAX_TEMP:
      print("--> STOPPING MPPT CHARGERS until temperatures are below {}".format(MAX_TEMP))
      mppt_status = 0
    else:
      print("All good, keeping charger on.")
  else:
    if global_max < MAX_CELL_VOLT_IN and global_max_t < MAX_TEMP:
      print("--> Restarting MPPT CHARGERS because max is below {} and temp is ok too.".format(MAX_CELL_VOLT_IN))
      mppt_status = 1
    else:
      print("Still not good, keeping charger off.")
  mppt.set(mppt_status)  
  time.sleep(2)
