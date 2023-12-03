#!/usr/bin/python3

"""
Author: Daniel Elsner
Date: 2023-12-03

Description:
    This script records a timestamp for each key press, displaying it on screen (in human-readable
    format) and logging it in a CSV file (in milliseconds). It is useful for counting events in
    behavioral observations, though the user must remember which key represents which event.

Usage:
    The script takes two parameters: a base name for the output files and, optionally, a number
    indicating the observation time in seconds. Upon launching, press any key (excluding Umlauts
    etc.) to start recording. This initial key press sets the starting "condition." Continue
    pressing keys as needed to denote, for example, the start of a behavior. When the runtime
    ends (if specified), recording stops. The script generates two files: one detailing all key
    press events and another summarizing the duration of each "condition" in milliseconds.

Warning:
    The script includes a terminal flash at the end of the execution. If you are epileptic, avoid
    using this script or disable the flashing by removing the line "curses.flash()." Note that not
    all terminals support this feature, but Xterm should.

License:
    MIT License
    Copyright (c) 2023 Daniel Elsner
    Permission is granted, free of charge, to any person obtaining a copy of this software and
    associated documentation files (the "Software"), to deal in the Software without restriction,
    including without limitation the rights to use, copy, modify, merge, publish, distribute,
    sublicense, and/or sell copies of the Software, and to permit persons to whom the Software
    is furnished to do so, subject to the following conditions:
    The above copyright notice and this permission notice shall be included in all copies or
    substantial portions of the Software.
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
    INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
    PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE
    FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

Disclaimer:
    This script is provided as-is and used at one's own risk. The accuracy of millisecond detection
    may vary depending on the system. The last key press detected might appear after the
    observation time; this is expected behavior and not counted. The script requires detecting
    the key press to close, which is intentional. This project was created as a hobby and will
    not be supported or maintained.

Settings:
    Specify the number of fixed digits in the filename. Default is 4.
"""


import argparse
import pathlib
import time
import curses
from collections import defaultdict
from typing import Dict
import re


def parse_time(time_str: str) -> int:
    """Parse time from HH:MM:SS format to seconds."""
    if re.match(r"\d{2}:\d{2}:\d{2}", time_str):
        h, m, s = map(int, time_str.split(":"))
        return h * 3600 + m * 60 + s
    if time_str.isdigit():
        return int(time_str)
    raise ValueError("Time format is invalid. Please use HH:MM:SS or seconds format.")


# Set up argument parsing
parser = argparse.ArgumentParser(
    description="Record keystrokes for behavioral observation."
)
parser.add_argument(
    "-b", "--base_name", required=True, help="Base name for output files."
)
parser.add_argument(
    "-t",
    "--observation_time",
    nargs="?",
    default=None,
    help="Duration of observation in seconds or in HH:MM:SS format (optional).",
)
parser.add_argument(
    "-o",
    "--output_dir",
    type=pathlib.Path,
    default=".",
    help="Where should the output be stored?",
)
parser.add_argument(
    "-p",
    "--padding",
    type=int,
    default=4,
    help="How many zeros should be used to pad the counter.",
)

# Parse arguments
args = parser.parse_args()

# Convert observation_time to seconds if in HH:MM:SS format
if args.observation_time:
    try:
        args.observation_time = parse_time(args.observation_time)
    except ValueError as e:
        parser.error(str(e))

# Check for existing observation files
observation = 0
base_path = args.output_dir
for filename in base_path.glob("*_ethoc.csv"):
    if filename.stem.startswith(args.base_name):
        observation += 1

# Determine observation time
if args.observation_time is not None:
    observation_time = int(args.observation_time)
    run_forever = False
else:
    run_forever = True

# Initialize dictionaries for recording keystrokes and summaries
strokes = dict()
stroke_summary = defaultdict(list)


# using curses to record keyboard events
def main(waiting) -> None:
    waiting.nodelay(True)
    waiting.scrollok(True)
    key = ""
    waiting.addstr(
        "Press any key (no special character) you wish to record. It will be printed in the terminal and stored in a *.csv file with time points in milliseconds. Actual milliseconds accuracy depends on your system and may vary. No warranty, use at own risk. Pressing multiple keys at once may freeze the script. Any stats you need to do yourself ;)\n\n"
    )
    waiting.addstr(
        "Press any alphanumeric key to start the counter (it will record this as initial key), and Shift+P to exit manually and save the output. If you set an observation time, the script will exit automatically."
    )
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
    # record the keys
    while True:
        try:
            oldkey = key
            key = waiting.getkey()
            if not re.match("(^[A-Za-z0-9])", str(key)):
                waiting.addstr(
                    "\n Only letters or numbers will be counted. Key press was ignored."
                )
                key = oldkey
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
            seconds, milliseconds = str(millis)[:-3], str(millis)[-3:]
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
                    stroke_summary[oldkey].append(
                        (millis - int(observation_time) * 1000) * -1
                    )
                    strokes[
                        millis
                    ] = "End of recording - time out after {} seconds".format(
                        str(seconds)
                    )
                    break
            # save keystrokes in a dict
            strokes[millis] = key
            # print to screen
            waiting.addstr(
                "\n Time: " + str(seconds) + "s," + milliseconds + "ms: Detected key:"
            )
            waiting.addstr(str(key))
        except:
            pass


def flashing(self) -> None:
    self.addstr("TIME OUT")
    curses.beep()
    curses.flash()
    curses.napms(100)


# execute main function
curses.wrapper(main)

# notify the user that the program is done
curses.wrapper(flashing)


# Sum up the summary lists
stroke_summary_sums: Dict[str, int] = {}

for key in list(stroke_summary.keys()):  # Create a list of keys to iterate over
    stroke_summary_sums[key] = sum(stroke_summary[key])

# Remove the entry with an empty string key, if it exists
drop = stroke_summary_sums.pop("", None)

# Define the base file name
base_file_name = args.base_name + "_" + str(observation).zfill(args.padding)

# Write to the ethoc CSV file
ethoc_file_path = args.output_dir / (base_file_name + "_ethoc.csv")
with ethoc_file_path.open("w") as writefile:
    writefile.write("Time in ms,key pressed\n")
    for i, j in sorted(strokes.items(), key=lambda x: x[0]):
        writefile.write(f"{i},{j}\n")

# Write to the summary CSV file
summary_file_path = args.output_dir / (base_file_name + "_summary.csv")
with summary_file_path.open("w") as writefile:
    writefile.write("key pressed,summed up time\n")
    for i, j in sorted(stroke_summary_sums.items(), key=lambda x: x[0]):
        writefile.write(f"{i},{j}\n")
