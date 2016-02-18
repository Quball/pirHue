# Importer RPi.GPIO for kontroll av GPIO pins
import RPi.GPIO as GPIO
# Importer time for å kunne vente i x antall sekunder
import time
# Importer requests for å kommunisere med API
import requests

# Fortell hvilken pin sensor input er koblet til
sensor = 4

# Fortell hvilken tellemåte jeg har brukt for å telle pins
GPIO.setmode( GPIO.BCM )
# Sett opp min input pin som input
GPIO.setup( sensor, GPIO.IN, GPIO.PUD_DOWN )

# Setter initial states
previous_state = False
current_state = False

### Denne delen er for å kommunisere med Hue API

# IP-adressen til Hue Bridge
hueIp = "[REDACTED]"

# Rasperry brukernavn på bridge
hueUser = "[REDACTED]"

# URL til API-et
hueApi = "http://" + hueIp + "/api/" + hueUser

### Slutt på API-delen

# Evig løkke for å sjekke sensoren
try:
        while 1:
                # Vent 0.1 sekund
                time.sleep( 0.1 )
                # Forrige er det som var nåværende i forrige runde
                previous_state = current_state
                # Nåværende state hentes fra pin
                current_state = GPIO.input( sensor )
                # Hvis det har skjedd en endring
                if current_state != previous_state:
                        # Hvis current_state er FALSE, skru av lyset
                        # Hvis current_state er TRUE, skru på lyset
                        if current_state:
                                print( "Skrur på lyset" )
                                putResponse = requests.put( hueApi + "/lights/3/state", '{ "on": true }' )
                        else:
                                print( "Skrur av lyset om 5 sekunder" )
                                waitForRise = GPIO.wait_for_edge( sensor, GPIO.RISING, timeout = 60000 )
                                if waitForRise is None:
                                        print( "Tiden er ute, skrur av lyset" )
                                        putResponse = requests.put( hueApi + "/lights/3/state", '{ "on": false }' )
                                else:
                                        print( "Skrur ikke av lyset allikevel" )
                                        pass
except KeyboardInterrupt:
        print( "\nAvslutter" )
        GPIO.cleanup()
