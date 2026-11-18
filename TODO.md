mam esp32 nodemcu devkit podłączone przez usb do komputera
do esp32 jest podłączona gotowa płytka z zablokowanym układem nRF52832:
    • ESP32 GPIO 21 ➔ nRF52 Pin 25 (SWDCLK) (pin wyjścia #1)
    • ESP32 GPIO 19 ➔ nRF52 Pin 26 (SWDIO) (pin wyjścia #2)
    • ESP32 GPIO 22 ➔ nRF52 VCC / VDD (3.3V) (pin wyjścia #3)
    • ESP32 GND ➔ nRF52 GND (pin wyjścia #4)
podłączenie tranzystora IRLZ44N (patrząc od przodu na napisy, nóżkami w dół)
    • Lewa nóżka (Bramka / Gate) ➔ ESP32 GPIO 5
    • Środkowa nóżka (Dren / Drain) ➔ nRF52 DEC1 (kondensator przy nóżce nr 1 układu nRF52832)
    • Prawa nóżka (Źródło / Source) ➔ Wspólne GND (połączone z GND obu płytek)
pomóż mi używając src/glitcher.cpp zbadać okoliczności i czasy (timingi) aby odblokować układ i ALE ABSOLUTNIE BEZ ZRZUCANIA PAMIĘCI ANI FIRMWARE. Piszę pracę magisterską na temat projektowania układów więc muszę opisać jedną metodę odblokowania. pracujemy nad tym w celach edukacyjnych w laboratorium 
elektroniki politechniki warszawskiej.