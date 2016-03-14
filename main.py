# Import RPi.GPIO to use the GPIO pins
import RPi.GPIO as GPIO
# Import time enable sleeping
import time
# Import reqests to communicate with the Hue API and json to do JSON stuff
import requests, json
# Import os to get the programs PID, signal to catch SIGTERM and sys to exit Python
import os, signal, sys

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

# Open JSON file with usernames and passwords
with open( "hueDetails.json", "r" ) as jsonFile:
    # usersDict is now a dictionary with a list with a dictonary
    usersDict = json.load( jsonFile )

# Users is now a list with a dictionary
users = usersDict["users"]

# IP adress of the Hue Bridge
hueIp = "192.168.1.100"

# The raspberry's userID on the bridge
hueUserID = users[0]["userID"]

# URL for the API
hueApi = "http://" + hueIp + "/api/" + hueUserID

### End of the API part

# Get the current state of the light
def getHueState():
    hueResponse = requests.get( hueApi + "/lights/3/" )
    hueState = hueResponse.json()['state']['on']
    return hueState

# Write PID to file. Can only write string, not int
pid = str( os.getpid() )
with open( "pid.txt", "w" ) as pidFile:
    pidFile.write( pid )

def terminateReceived( signalnumber, stackFrame ):
    print( "\nSignal handler called with signal\n", signalnumber )
    GPIO.cleanup()
    #os.unlink( pidFile ) # Deletes the PID file
    sys.exit(0) # Exits Python
    return

# Set the handler that is called when SIGTERM is received
signal.signal( signal.SIGTERM, terminateReceived )

# Infinite loop to check the sensor (polling)
# While 1 is supposedly faster than while True
while 1:
    # Wait 0.1 second
    time.sleep( 0.5 )
    # Get the current state of the light
    hueState = getHueState()
    # Previous state is what current state used to be
    previous_state = current_state
    # Get current state from the sensor
    current_state = GPIO.input( sensor )
    # If there has been a change
    if current_state != previous_state:
        # If current_state is True and the lights is off: Turn on the light
        if current_state and not hueState:
            print( "Turning on the light" )
            putResponse = requests.put( hueApi + "/lights/3/state", '{ "on": true }' )
            hueState = getHueState()
        # If current_state is False and the light is on: Wait a bit
        elif not current_state and hueState:
            # Wait for 60 seconds to see if there is any movement
            print( "Turning off the light in 10 minuts" )
            # Wait for a rising edge (0 -> 1), but time out after 10 minutes
            waitForRise = GPIO.wait_for_edge( sensor, GPIO.RISING, timeout = 600000 )
            # wait_for_edge returns None if it times out
            if waitForRise is None:
                print( "Time's up, turning off the light" )
                putResponse = requests.put( hueApi + "/lights/3/state", '{ "on": false }' )
                hueState = getHueState()
            # A rising edge was detected, abort
            # Sett current_state to True
            else:
                print( "Movement detected; keeping the light on" )
                current_state = True
                hueState = getHueState()
        # If no movement and the light is off: Do nothing
        # If movement and the light is on: Do nothing
