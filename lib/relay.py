import RPi.GPIO as GPIO
import time

class Relay:

  RELAY_BCM = [None,4,22,6,26]

  def __init(self,id,log = None):
    self.id = id
    self.log = log
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(RELAY_BCM[self.id], GPIO.OUT)

  def set(self,zero_or_one):
    GPIO.output(RELAY_BCM[self.id],zero_or_one)
    if self.log:
      self.log("info","Turned relay {} to {}.".format(self.id,zero_or_one))

for i in [1,2,3,4]:
  r = Relay(i)
  r.set(1)
  time.sleep(1)
  r.set(0)

