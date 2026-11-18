# ESP32 SWD Flasher for nRF52
This software makes it possible to Read and Write the internal Flash of the Nordic nRF52 series with an ESP32 using the SWD interface.
A tool to exploit the APPROTECT vulnerability is included as well.

To flash an nRF52 connect the following:
- nRF52 **SWDCLK** to ESP32 **GPIO 21**
- nRF52 **SWDIO** to ESP32 **GPIO 19**
- nRF52 **GND** to ESP32 **GND** to N-Channel MOSFET **GND** (Optional: O-scope **GND Clips**)
- Then power the nRF52 as needed

To bypass the Readout protection (APPROTECT) of an nRF52 connect all of the above and the following:
- nRF52 3.3V Power **VDD** to ESP32 **GPIO 22** (Optional: O-scope **Channel 2 Probe**)
- N-Channel MOSFET **PWM+** to ESP32 **GPIO 5** (as shown)
- N-Channel MOSFET **VOUT-** to nRF52 **DEC1** (as shown) (Optional: O-scope **Channel 1 Probe**)
- Then power the nRF52 as needed


This repo is explained and demonstrated in these videos (click to watch):


[![YoutubeVideo](https://img.youtube.com/vi/tMPD0kBG_So/0.jpg)](https://www.youtube.com/watch?v=tMPD0kBG_So)


[![YoutubeVideo](https://img.youtube.com/vi/Iu6RoXRZxOk/0.jpg)](https://www.youtube.com/watch?v=Iu6RoXRZxOk)

### Required Hardware

- ESP32 Development Board
- N-Channel MOSFET Board
- nRF52 Series Board
- Optional: Oscilloscope

### HowTo:

Use Visual Studio Code with PlatformIO to compile and upload the project.

Note: The Arduino IDE is not supported any more!

Change the WiFi credentials in Web.cpp and the Pinout to your needs in the platformio.ini file

Upload the data/index.htm to the ESP32 via the ip-address/edit web editor 


### Python machine control

The host-side CLI uses only the Python standard library and keeps the ESP32 browser interface unchanged. Point `--host` at the ESP32's IP address or `swd.local`:

```bash
python tools/nrf52_swd.py --host swd.local status
```

For APPROTECT unlocking, the known-good timing is `2368` microseconds:

```bash
python tools/nrf52_swd.py --host swd.local glitch --delay 2368
```

Dump the original flash and UICR:

```bash
python tools/nrf52_swd.py --host swd.local dump --kind flash --output dumps/full_flash.bin
python tools/nrf52_swd.py --host swd.local dump --kind uicr --output dumps/full_uicr.bin
```

Restore the original factory archive only with explicit confirmation. The CLI verifies the 512 KiB flash and 4 KiB UICR sizes and their original SHA-256 values before transmitting bytes:

```bash
python tools/nrf52_swd.py --host swd.local restore --flash dumps/full_flash.bin --uicr dumps/full_uicr.bin --confirm
```

Original archive paths and hashes:

- `dumps/full_flash.bin`: 512 KiB, SHA-256 `ec3060bb5d8160296f1891a2d4d2db7882535f80779dd6fe611bf300a475d826`
- `dumps/full_uicr.bin`: 4 KiB, SHA-256 `8cf25c59ad391780435765317039d2256cc618ff036a3c0847033c8d593e13dd`

The CLI prints a SHA-256 digest for every downloaded dump. A restore must include `--confirm`; omitting it or using a wrong-size or wrong-checksum file fails before restore starts.


### ESP32 Glitcher schematic:

<img width="800" alt="" src="https://github.com/atc1441/ESP32_nRF52_SWD/blob/main/ESP32_nRF_glitcher_schematic.jpg">

#### nRF52832 Glitch Tip, way better results with these 2 caps removed
<img width="800" alt="" src="https://github.com/atc1441/ESP32_nRF52_SWD/blob/main/nRF52832_glitchtip.jpg">


Credits go to LimitedResults for finding the Power glitching Exploit: https://limitedresults.com/2020/06/nrf52-debug-resurrection-approtect-bypass-part-2/
