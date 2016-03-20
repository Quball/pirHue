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

# Get the current state of the light. Returns True or False
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

# This is the callback function. It's called whenever an edge is detected
def callbackFunc( sensor ):
    print ( "In callbackFunc" )
    if GPIO.input( sensor ) and not getHueState(): # Movement and light is off
        print( "Turning the light on" )
        putResponse = requests.put( hueApi + "/lights/3/state", '{ "on": true }' )
    elif not GPIO.input( sensor ) and getHueState(): # No movement and light is on
        print( "No movement; waiting for rising edge" )
        waitForRise = GPIO.wait_for_edge( sensor, GPIO.RISING, timeout = 2000 ) # This doesn't work: Can't have two edge detections on the same channel
        if waitForRise is None:
            print( "No rising edge; turning off" )
            putResponse = requests.put( hueApi + "/lights/3/state", '{ "on": false }' )
        else:
            print( "Rising edge; keeping the light on" )

# Add event detect
GPIO.add_event_detect( sensor, GPIO.BOTH )

# Add event callback
GPIO.add_event_callback( sensor, callbackFunc )

# The try/except can be removed before release. In release I detect signal handler
try:
    while 1:
        print( ".", end = "", flush = True )
        time.sleep( 2 )
except KeyboardInterrupt:
    print( "Cleaning up" )
    GPIO.cleanup()
