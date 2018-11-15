import RPi.GPIO as GPIO
import time

RELAY = [None,4,22,6,26]

# gpio 4   is relay 1
# gpio 22 is relay 2
# gpio 6 is relay 3
# gpio 26 is relay 4.

GPIO.setmode(GPIO.BCM)


r= RELAY[2]

GPIO.setup(r, GPIO.OUT)
GPIO.output(r, 1)


