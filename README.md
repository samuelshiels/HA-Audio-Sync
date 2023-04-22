# HA-Audio-Sync
Sync home assistant lights to a chosen or default audio input.

It is a work in progress.

Made for home assistant instance on another server.

# Usage

```bash
python3 color_script.py -u http://<IP_ADDRESS>:<PORT> -p <API_KEY> -e light.hue_color_lamp_1
```

# API Key

The application uses the REST API endpoints of HA. This requires the use of Long-Lived Access Tokens or API Key to authenticate. Generate one be navigating to Your Profile in HA and scrolling to the bottom for generating an API Key. Otherwise use an existing key.

# Device ID

Finding your device IDs can be done via the provided script:

```bash
python3 get_audio_devices.py
```

Outputting:
```
Input Device id - 0 - Razer Seiren X: USB Audio (hw:0,0)
Input Device id - 7 - HD-Audio Generic: ALC1220 Analog (hw:2,0)
Input Device id - 9 - HD-Audio Generic: ALC1220 Alt Analog (hw:2,2)
Input Device id - 10 - sysdefault
Input Device id - 14 - spdif
Input Device id - 15 - pipewire
Input Device id - 17 - default
```
(Other ALSA errors may be generated, can be safely ignored)

# Command Line
```
usage: color_script.py [-h] [-c] [-u URL] -p APIKEY -e ENTITY [-d DEVICE]

options:
  -h, --help            show this help message and exit
  -c, --clear           clear the display on exit
  -u URL, --url URL     URL/IP/Endpoint for Home Assistant. Include the full endpoint that will resolve correctly from this device, including port if necessary. Will default to
                        http://localhost:8123.
  -p APIKEY, --apikey APIKEY
                        API Key for access to Home Assistant
  -e ENTITY, --entity ENTITY
                        Comma seperated list of entities to change brightness and colour of
  -d DEVICE, --device DEVICE
                        Device index to use for input, will use default input device if not provided
```