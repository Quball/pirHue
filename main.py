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

def terminateReceived( signalnumber, stackFrame ):
    GPIO.cleanup()
    #os.unlink( pidFile ) # Deletes the PID file
    sys.exit(0) # Exits Python
    return

# Set the handler that is called when SIGTERM is received
signal.signal( signal.SIGTERM, terminateReceived )

# Write PID to file. Can only write string, not int
pid = str( os.getpid() )
with open( "pid.txt", "w" ) as pidFile:
    pidFile.write( pid )

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

def waitForRise( waitingTime ):
    """
    Waits for a rising edge
    Returns True if a rising edge is detected, False otherwise
    Parameter waitingTime defines how many milliseconds the
    function waits before timing out
    """
    global sensor
    # A channel can only have one event detection.
    # Need to remove the original one so that I can add one that waits for rising edges
    # This event detection is only used in this function
    GPIO.remove_event_detect( sensor )
    # Waits for a rising edge. Times out after [waitingTime] milliseconds
    waiting = GPIO.wait_for_edge( sensor, GPIO.BOTH, timeout = waitingTime )
    if waiting is None: # wait_for_edge returns None if it times out
        GPIO.remove_event_detect( sensor ) # Removes the temporary event detection
        # Adds event detection for both rising and falling edges
        GPIO.add_event_detect( sensor, GPIO.BOTH, callback = callbackFunc )
        return False # No new rising edge detected
    else:
        GPIO.remove_event_detect( sensor )
        GPIO.add_event_detect( sensor, GPIO.BOTH, callback = callbackFunc )
        return True # Rising edge detected

def getHueState():
    """
    Returns the current state of the light; True if on, False otherwise
    """
    hueResponse = requests.get( hueApi + "/lights/3/" )
    hueState = hueResponse.json()['state']['on']
    return hueState

def callbackFunc( sensor ):
    """
    Callback function, is called whenever an edge is detected
    """
    if GPIO.input( sensor ) and not getHueState(): # Movement and light is off
        putResponse = requests.put( hueApi + "/lights/3/state", '{ "on": true }' )
    elif not GPIO.input( sensor ) and getHueState(): # No movement and light is on
        if waitForRise( 600000 ):
            callbackFunc( sensor ) # If the light has been turned off externally, I need to turn it back on
        else:
            putResponse = requests.put( hueApi + "/lights/3/state", '{ "on": false }' )

# Add event detect with callback
GPIO.add_event_detect( sensor, GPIO.BOTH, callback = callbackFunc )

# Infinite loop. Does nothing
while 1:
    time.sleep( 1 )
