# HA-Audio-Sync
Sync home assistant lights to a chosen or default audio input.

It is a work in progress.

Made for home assistant instance on another server.

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
usage: color_script.py [-h] [-c] [-e ENTITY] [-d DEVICE]

options:
  -h, --help            show this help message and exit
  -c, --clear           clear the display on exit
  -e ENTITY, --entity ENTITY
                        Entity
  -d DEVICE, --device DEVICE
                        Device index to use for input, will use default input device if not provided
```