# Import RPi.GPIO to use the GPIO pins
import RPi.GPIO as GPIO
# Import time enable sleeping
import time
# Import reqests to communicate with the Hue API
import requests

# The number of the pin that the input is connected to
sensor = 4

# Set the mode that is used to count the pins on the board
GPIO.setmode( GPIO.BCM )
# Initialize the pin as an input pin. Set the starting state to DOWN (false)
GPIO.setup( sensor, GPIO.IN, GPIO.PUD_DOWN )

# Set initial states
previous_state = False
current_state = False

### This part is all about communicating with the API

# IP adress of the Hue Bridge
hueIp = "192.168.1.100"

# The raspberry's user name on the bridge
hueUser = "231b420d85be57e665ac3f57a8bd563"

# URL for the API
hueApi = "http://" + hueIp + "/api/" + hueUser

### End of the API part

try:
	# Infinite loop to check the sensor (polling)
        # While 1 is supposedly faster than while True
	while 1:
                # Wait 0.1 second
                time.sleep( 0.1 )
                # Forrige er det som var nåværende i forrige runde
                # Previous state is what current state used to be
		previous_state = current_state
		# Get current state from the sensor
                current_state = GPIO.input( sensor )
                # If there has been a change
                if current_state != previous_state:
			# If current_state is True: Turn on the light
                        if current_state:
                                print( "Turning on the light" )
                                putResponse = requests.put( hueApi + "/lights/3/state", '{ "on": true }' )
                        # If current_state is False
			else:
				# Wait for 60 seconds to see if there is any movement
                                print( "Turning off the light in 60 seconds" )
				# Wait for a rising edge (0 -> 1), but time out after 60 seconds
                                waitForRise = GPIO.wait_for_edge( sensor, GPIO.RISING, timeout = 60000 )
                                # wait_for_edge returns None if it times out
				if waitForRise is None:
                                        print( "Time's up, turning off the light" )
                                        putResponse = requests.put( hueApi + "/lights/3/state", '{ "on": false }' )
                                # A rising edge was detected, abort
				# This part can be removed in a more final version
				else:
                                        print( "Movement detected; keeping the light on" )
                                        pass
# If someone hits CTRL+C: Exit
except KeyboardInterrupt:
        print( "\nExitting" )
        GPIO.cleanup()
