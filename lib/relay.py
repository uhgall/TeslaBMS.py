import RPi.GPIO as GPIO
import time

RELAY_BCM = [None,4,22,6,26]

class Relay:

  def __init__(self,id,log = None):
    self.id = id
    self.log = log
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(RELAY_BCM[self.id], GPIO.OUT)

  def set(self,zero_or_one):
    GPIO.output(RELAY_BCM[self.id],zero_or_one)
    if self.log:
      self.log("info","Turned relay {} to {}.".format(self.id,zero_or_one))

def test_relays():
  for i in [1,2,3,4]:
    r = Relay(i)
    r.set(1)
    time.sleep(1)
    r.set(0)
    time.sleep(1)

