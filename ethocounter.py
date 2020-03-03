#!/usr/bin/python3

# Daniel Elsner
# 10.03.2018

# Records a time stamp for a key press both on screen (human readable) and in a
# csv file (as milliseconds).
# It "might" conceivably be used to count events, say in behavioral observation.
# defintion agnostic, you need to remember which key indicates what...

# Usage: takes two parameters, a base name for output files and optionally a
# number to indicate the obervation time in seconds.
# After launching the script, press any key (no Umlaut etc.) to start recording.
# This key will be your starting "condition". Then keep pressing keys as you
# need to denote e.g. a behavior starting. At the end of the runtime (if given),
# the recording is cut off. Two files will be generated, one with all key press
# events and another with a summary in milliseconds, how long each "condition"
# was active.
# After it is done, the script will flash the terminal (if you are epileptic,
# do not use this script or disable the flashing by removing the line
# "curses.flash()". Not all terminals support this, but Xterm should work.

# License: MIT
# Copyright (c) 2018 Daniel Elsner
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# Provided as is. Use at your own risk.
# Millisecond detection accuracy may depend on your system
# The last key press detected may appear after the observation time,
# this is not an error and will not be counted. The script is written in a way
# that it is necessary to detect the key press to close.
# This was done for fun as a hobby project. I will not support or maintain it.

## SETTINGS

# how many fixed numbers should be in the filename - default = 4
padding = 4 # 4

import sys
import time
import curses
import glob
from collections import defaultdict
import re

# checking if there is an output file provided and if there are already observations with this basename
observation = 0

try:
    if sys.argv[1]:
        # get all files that come from this script
        for filename in glob.glob('*_ethoc.csv'):
            # and check if observations for this basename already exist and add a higher number if so
            trimmed_name = filename[:len(sys.argv[1])]
            if trimmed_name == sys.argv[1]:
                observation += 1
            else:
                pass
except:
    sys.exit("Takes 2 parameters: base name for output files and (optional) duration of observation.")



try:
    if sys.argv[2]:
        observation_time = sys.argv[2]
        run_forever = False
    else:
        run_forever = True
except:
    run_forever = True

# recording keystrokes in a dictionary
strokes = dict()

# and make a summary too
stroke_summary = defaultdict(list)

# using curses to record keyboard events
def main(waiting):
    waiting.nodelay(True)
    waiting.scrollok(True)
    key=""
    waiting.addstr("Press any key (no special character) you wish to record. It will be printed in the terminal and stored in a *.csv file with time points in milliseconds. Actual milliseconds accuracy depends on your system and may vary. No warranty, use at own risk. Pressing multiple keys at once may freeze the script. Any stats you need to do yourself ;)\n\n")
    waiting.addstr("Press any alphanumeric key to start the counter (it will record this as initial key), and Shift+P to exit manually and save the output. If you set an observation time, the script will exit automatically.")
    # first loop just to wait until the run is supposed to start
    while True:
        try:
            key = waiting.getkey()
            if re.match("(^[A-Za-z0-9])", str(key)):
                waiting.addstr("\n Detected initial key:")
                waiting.addstr(str(key))
                if key:
                    break
            else:
                waiting.addstr("\n Please only use letters or numbers.")

        except:
            pass
    # records the starting Unix time in ms, will be substracted from key press times
    starttime = time.time()
    millis = 0
    firstrun = True
    # record the keys
    while True:
        try:
            oldkey = key
            key = waiting.getkey()
            if not re.match("(^[A-Za-z0-9])", str(key)):
                waiting.addstr("\n Only letters or numbers will be counted. Key press was ignored.")
                key=oldkey
            # calculate the times
            # time of button press
            presstime = time.time()
            # calculate the difference between button presses
            oldtime = millis
            # calculate the total time
            totaltime = presstime - starttime
            # time diff
            # calculate seconds for pretty display
            millis = int(round(totaltime * 1000))
            seconds, milliseconds = str(millis)[:-3],str(millis)[-3:]
            # workaround because empty seconds looks ugly
            if seconds == "":
                seconds = "0"
            # end recording on Return
            stroke_summary[oldkey].append(millis - oldtime)
            if key == "P":
                strokes[millis] = "End of recording - manual exit"
                break
            # ending condition
            if run_forever == False:
                if int(seconds) >= int(observation_time):
                    # substract again the time counted too much
                    stroke_summary[oldkey].append((millis - int(observation_time)*1000)*-1)
                    strokes[millis] = "End of recording - time out after {} seconds".format(str(seconds))
                    break
            # save keystrokes in a dict
            strokes[millis] = key
            # print to screen
            waiting.addstr("\n Time: " + str(seconds) + "s," + milliseconds + "ms: Detected key:")
            waiting.addstr(str(key))
        except:
            pass

def flashing(self):
    self.addstr("TIME OUT")
    curses.beep()
    curses.flash()
    curses.napms(100)


# execute main function
curses.wrapper(main)

# notify the user that the program is done
curses.wrapper(flashing)

# sum up the summary lists (yes this has to be done that way - somehow curses does
# not like to modify a dictionary value internally)
for i in stroke_summary:
    stroke_summary[i] = sum(stroke_summary[i])
drop = stroke_summary.pop('', None)

# write the output
with open(sys.argv[1] + "_" + str(observation).zfill(padding) + "_ethoc.csv" , "w") as writefile:
    # write a header
    writefile.write("Time in ms,key pressed\n")
    # write all elements in the dictionary
    for i,j in sorted(strokes.items(), key=lambda x: x[0]):
        # lambda function to have the output of the dict ordered
        writefile.write(str(i) + "," + str(j) + "\n")

with open(sys.argv[1] + "_" + str(observation).zfill(padding) + "_summary.csv" , "w") as writefile:
    # write a header
    writefile.write("key pressed,summed up time\n")
    # write all elements in the dictionary
    for i,j in sorted(stroke_summary.items(), key=lambda x: x[0]):
        # skipping first line as it is empty
        # lambda function to have the output of the dict ordered
        writefile.write(str(i) + "," + str(j) + "\n")
