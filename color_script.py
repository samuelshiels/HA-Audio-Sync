#!/usr/bin/env python3
""" Audio pitch/volume to light color/brightness.

    Author: Rob Landry (rob.a.landry@gmail.com)"""
import os
import sys
import contextlib
import time
import requests
import json
import argparse
from dotenv import load_dotenv

# For Music
# import alsaaudio as aa
import pyaudio
import aubio
import numpy as np
import colorsys
import webcolors

SLEEP = 0.05

# AUDIO CONFIGURATION
#
# FORMAT = pyaudio.paInt16
# CHANNELS =
# RATE =
# CHUNK =
# DEVICE_INDEX =
FORMAT = pyaudio.paFloat32
CHANNELS = 1
RATE = 16000
CHUNK = 1024
DEVICE_INDEX = 0

# HASS CONFIGURATION
HASS_URL = "http://localhost:8123"
HASS_PASS = "APIKEYHERE"
COLOR_LIGHTS = "light.living_room, light.garden_lights"
WHITE_LIGHTS = ""

# prevents same colors repeating by changing hs +/- 30
PREVENT_STATIC = False


@contextlib.contextmanager
def silence():
    devnull = os.open(os.devnull, os.O_WRONLY)
    old_stderr = os.dup(2)
    sys.stderr.flush()
    os.dup2(devnull, 2)
    os.close(devnull)
    try:
        yield
    finally:
        os.dup2(old_stderr, 2)
        os.close(old_stderr)


def get_colour_name(rgb_triplet):
    min_colours = {}
    for key, name in webcolors.CSS21_HEX_TO_NAMES.items():
        r_c, g_c, b_c = webcolors.hex_to_rgb(key)
        rd = (r_c - rgb_triplet[0]) ** 2
        gd = (g_c - rgb_triplet[1]) ** 2
        bd = (b_c - rgb_triplet[2]) ** 2
        min_colours[(rd + gd + bd)] = name
    return min_colours[min(min_colours.keys())]


# pylint: disable=undefined-variable
class ProcessColor:
    """Docstring."""

    def __init__(self, **kwargs):
        """Docstring."""
        self.color = 0
        self.kwargs = kwargs
        with silence():
            self.audioSync()

    def audioSync(self):  # pylint: disable=too-many-locals
        """Docstring."""

        hassSync = self.kwargs.get("hass")

        p = pyaudio.PyAudio()

        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
            input_device_index=DEVICE_INDEX,
        )

        # aubio pitch detection
        pDetection = aubio.pitch("default", 2048, 2048 // 2, 16000)
        pDetection.set_unit("Hz")
        pDetection.set_silence(-40)

        #print("Audio Controlled LEDs.")

        while True:
            # Read data from device
            if stream.is_stopped():
                stream.start_stream()
            data = stream.read(CHUNK)
            stream.stop_stream()

            # determine pitch
            samples = np.fromstring(data, dtype=aubio.float_type)
            pitch = pDetection(samples)[0]
            # #print(pitch)

            # determine volume
            volume = np.sum(samples**2) / len(samples)
            volume = "{:.6f}".format(volume)
            #print(f"Volume {volume}")

            # calculate a brightness based on volume level
            brightness = self.calc_bright(volume)

            # get color based on pitch
            hs_color = self.calc_hs(pitch)
            if PREVENT_STATIC:
                if self.color <= (hs_color + 5) and self.color >= (hs_color - 5):
                    if int(hs_color) <= 30:
                        hs_color = hs_color + 30
                    else:
                        hs_color = hs_color - 30
            self.color = hs_color

            # #print(self.color)
            rgb_color = self.hs_to_rbg(hs_color)
            r, g, b = rgb_color

            # output something to console
            #print(get_colour_name(rgb_color))
            #print("HS Color: %s" % hs_color)
            #print("RGB Color: (%s, %s, %s)" % rgb_color)
            #print("Brightness: %s\n" % brightness)

            # For HASS Lights
            if hassSync:
                self.exec_hass(hs_color, brightness)

            time.sleep(SLEEP)

        stream.stop_stream()
        stream.close()

    def calc_hs(self, pitch):
        """calculate the hs color based off max of 500Hz? thats about the highest ive seen."""
        hs_color = pitch / 500
        hs_color = hs_color * 360
        if hs_color > 360:
            hs_color = 360
        return hs_color

    def hs_to_rbg(self, hs_color):
        """Get RGB color from HS."""
        r, g, b = colorsys.hsv_to_rgb(hs_color / 360.0, 1, 1)
        r = int(r * 255)
        g = int(g * 255)
        b = int(b * 255)
        rgb_color = (r, g, b)
        return rgb_color

    def calc_bright(self, brightness):
        """calculate a brightness based on volume level."""
        brightness = int(float(brightness) * 10000)
        #print(f"Brightness {brightness}")
        if brightness < 10:
            brightness = 10
        if brightness > 100:
            brightness = 100
        return brightness

    def exec_hass(self, hs_color=0, brightness=100):
        saturation = 100
        if hs_color == 0:
            saturation = 0

        url = "/api/services/light/turn_on"

        # color lights
        payload = {
            "entity_id": COLOR_LIGHTS,
            "hs_color": [int(hs_color), saturation],
            "brightness_pct": brightness,
            "transition": 0.5,
        }

        hassConn(url=url, payload=payload)


class hassConn:
    """Format request to HASS."""

    def __init__(self, **kwargs):
        """Initialize the Class."""
        self._url = None
        self._headers = None
        self._payload = None

        if "url" in kwargs:
            self._url = kwargs.get("url")
        if "headers" in kwargs:
            self._headers = kwargs.get("headers")
        if "payload" in kwargs:
            self._payload = kwargs.get("payload")

        self.setUrl(self._url)
        self.setHeaders(self._headers)
        self.setPayload(self._payload)

        if kwargs.get("theType") == "GET":
            self.get()
        else:
            self.post()

    def setUrl(self, url):
        """Assign URL to var.

        Format: '/api/services/light/turn_on'"""
        self._url = HASS_URL + url

    def setHeaders(self, headers):
        """Assign header var."""
        if not headers:
            headers = {
                "Authorization": "Bearer " + HASS_PASS,
                "content-type": "application/json",
            }
        self._headers = headers

    def setPayload(self, payload):
        """Verify payload is valid JSON and assign to var."""
        try:
            json.loads(json.dumps(payload))
        except ValueError:
            
            #print("Invalid JSON!")
            pass
        self._payload = payload

    def post(self):
        """POST the request."""
        response = requests.post(self._url, json=self._payload, headers=self._headers)
        if response.status_code != 200:
            #print(response.text)
            pass

    def get(self):
        """GET the request."""
        try:
            response = requests.get(self._url, headers=self._headers)
            response.raise_for_status()
            # #print(response.text)
        except requests.exceptions.HTTPError as err:
            #print("HTTP Error")
            #print(err)
            exit()
            return "exception"

        except requests.exceptions.Timeout:
            # Maybe set up for a retry, or continue in a retry loop
            #print("Connection Timeout!")
            exit()
            return "exception"

        except requests.exceptions.TooManyRedirects:
            # Tell the user their URL was bad and try a different one
            #print("Too Many Redirects!")
            exit()
            return "exception"

        except requests.exceptions.RequestException as e:
            # catastrophic error. bail.
            #print("Request Exception!")
            #print(e)
            return "exception"
            # exit()

        return response


# Main program logic follows:
if __name__ == "__main__":
    # Process arguments
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument(
        "-c",
        "--clear",
        action="store_true",
        help="clear the display on exit",
        default=True,
    )

    parser.add_argument(
        "-u",
        "--url",
        type=str,
        nargs=1,
        action="store",
        default="http://localhost:8123",
        help="URL/IP/Endpoint for Home Assistant. Include the full endpoint that will resolve correctly from this device, including port if necessary. Will default to http://localhost:8123.",
    )

    parser.add_argument(
        "-p",
        "--apikey",
        type=str,
        nargs=1,
        action="store",
        #required=True,
        help="API Key for access to Home Assistant",
    )

    parser.add_argument(
        "-e",
        "--entity",
        type=str,
        nargs=1,
        action="store",
        required=True,
        help="Comma seperated list of entities to change brightness and colour of",
    )

    parser.add_argument(
        "-d",
        "--device",
        type=int,
        nargs=1,
        default=None,
        help="Device index to use for input, will use default input device if not provided",
    )

    args = parser.parse_args()

    load_dotenv()
    if os.getenv('HA_APIKEY') is not None:
        HASS_PASS = os.getenv('HA_APIKEY')

    if args.entity:
        #print(f"Using entities {args.entity[0]}")
        COLOR_LIGHTS=str(args.entity[0])

    if args.apikey:
        HASS_PASS = str(args.apikey[0])

    if args.url != "http://localhost:8123":
        #print(f"Using endpoint {args.url[0]}")
        HASS_URL = str(args.url[0])

    if args.device != None:
        #print(f"Using device {args.device[0]}")
        DEVICE_INDEX = args.device[0]
    else:
        def_input = pyaudio.PyAudio().get_default_input_device_info()
        DEVICE_INDEX = def_input.get("index", 0)
        #print(f'Using default device {def_input.get("index",0)}')

    try:
        #print("----------------------------------------------")
        #print("----------- Starting Color Server ------------")
        #print("----------------------------------------------")
        while True:
            
            hass = True
            ProcessColor(hass=hass)

            time.sleep(SLEEP)

    except KeyboardInterrupt:
        ProcessColor.exec_hass(0)
        #print("----------------------------------------------")
        #print("--------------- Shutting Down! ---------------")
        #print("----------------------------------------------")
        exit(0)
