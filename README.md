This repo contains a MQTT PHD2 telescope 
guiding client.
Instead of using the PHD2 GUI to guide your telescope, you
can now guide it over MQTT using the program in this repo, mqphd2.  

### Introduction

How does this work?  PHD2 itself provides a network "socket"
for remote control of the program.  mqphd2 in effect relays commands 
sent over MQTT to PHD2 by way of this socket.

### mqphd2

Commands to mqphd2 are sent over a command MQTT topic.  By default
this topic is named "f/tx".  Responses and status messages
from PHD2 are then relayed back using the topic "f/#" with 
\# replaced with the response type.  That is, error messages are sent over 
the topic "f/error", command results are sent over "f/result", and 
event messages are sent over "f/event"

mqphd2 provides the following MQTT command topic commands:

```
c        # connect to the telescope
e [1000] # set exposure time in millisecond
s        # stop capture
l        # start looping
fs       # find star
p        # pause
u        # unpause
g        # start guiding (passes settle object)
d [10]   # start dithing by given amount (passes settle object)
k        # shutdown phd2
run      # start phd2 if not yet running

to [60]  # set settle object timeout value
st [10]  # set settle object time to settle value
sp [1.5] # set settle object pixels to settle value

gc       # get whether telescope is connected
ge       # get exposure time
gs       # get PHD2 state
gd       # get valid exposure durations
gp       # get whether paused
ga       # get calibration

cc       # clear calibration
fc       # flip calibration
```

The program supports the following command line options:


```
$ python3 mqphd2.py --help
usage: mqphd2.py [-h] [--broker BROKER] [--broker-port BROKER_PORT]
                 [--broker-keepalive BROKER_KEEPALIVE] [--topic TOPIC]
                 [--host HOST] [--port PORT] [--shell SHELL] [--norun]

optional arguments:
  -h, --help            show this help message and exit
  --broker BROKER       broker host (default: 0.0.0.0)
  --broker-port BROKER_PORT
                        broker port (default: 1883)
  --broker-keepalive BROKER_KEEPALIVE
                        broker keepalive seconds (default: 60)
  --topic TOPIC         broker topic for command (default: f/tx)
  --host HOST           PHD2 remote host (default: localhost)
  --port PORT           PHD2 remote port (default: 4400)
  --shell SHELL         PHD2 shell command (default: xvfb-run -s '-screen 0
                        800x600x8' phd2)
  --norun               do not run PHD2 on start (default: False)
```


Note, the program xvfb-run lets you run GUI programs on a
headless computer, like a Raspberry Pi running Raspbian Lite.

### mqclient and mqblue

Two additional programs are provided, one is called 
mqclient and the other mqblue.  These programs located in
the repo at https://github.com/roseengineering/bluesoapysuite.

mqclient is a simmple command line program for communicating
over the MQTT command topic.

The other is called mqblue, it lets you communicate over
MQTT using bluetooth.  It works with the Raspberry Pi
and your phone.

### Example

Here is an example run

```
f/tx c                    # connect
f/event ConfigurationChange
f/result 0
f/tx gc                   # check if connected
f/result true
f/tx ga                   # check if calibrated
f/result false
f/tx fs                   # find star
f/error could not find star
f/tx l                    # start looping
f/result 0
f/event LoopingExposures
f/event LoopingExposures
f/tx fs                   # find star
f/event LockPositionSet
f/event LoopingExposures
f/event StarSelected
f/result [338.91, 447.21]
f/event LoopingExposures
f/event LoopingExposures
f/tx gs                    # get application state
f/result Selected
f/tx g                     # start guiding
f/event StartCalibration AO-Simulator
f/result 0
f/tx gs                    # get application state
f/result Calibrating
f/event Left Calibration: 22
...
f/event Left Calibration: 1
f/event Up Calibration: 22
...
f/event Up Calibration: 1
f/event ConfigurationChange
f/event StartCalibration On Camera
f/event West step 1, dist= 0.0
f/event West step 2, dist= 3.9
f/tx e 2000                # set exposure time to 2 sec
f/result 0
f/event West step 3, dist= 7.7
f/event West step 4, dist=11.5
f/tx gd                    # get valid exposure durations (ms)
f/result [10, 20, 50, 100, 200, 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 6000, 7000, 8000, 9000, 10000, 15000, 30000]
f/event West step 5, dist=15.2
f/event West step 6, dist=19.1
f/event West step 7, dist=23.0
f/event East step 6, dist=26.8
f/tx l                     # stop guiding
f/event CalibrationFailed
f/event GuidingStopped
f/event SettleDone
f/event LockPositionLost
f/result 0
f/event LoopingExposures
f/event LockPositionSet
f/event StarSelected
f/event LoopingExposures
f/event LoopingExposures
f/tx d                     # start dithering
f/event StartCalibration On Camera
f/result 0
f/event StartCalibration On Camera
f/event West step 1, dist= 0.0
f/event West step 2, dist= 4.0
f/event West step 3, dist= 7.7
...
```


