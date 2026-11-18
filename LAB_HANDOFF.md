# nRF52832 / ESP32 Lab Handoff

## Cel i zakres

Badanie timingów power-glitchingu układu nRF52832 podłączonego do ESP32 NodeMCU.

Cel:

- znaleźć moment i szerokość impulsu skutecznego do odblokowania interfejsu debugowego,
- badać zachowanie układu bez odczytu, kasowania lub zapisu pamięci flash,
- zebrać dane do pracy dyplomowej na temat projektowania układów.

Badania odbywają się w laboratorium elektroniki Politechniki Warszawskiej.

Zasada obowiązkowa: nie pobierać, nie zapisywać, nie kasować i nie eksportować pamięci flash ani firmware nRF52832.

## Aktualny stan fizyczny

- ESP32 NodeMCU DevKit podłączony przez USB do komputera.
- Port szeregowy ESP32: `/dev/ttyUSB0`.
- nRF52832 pozostaje zablokowany.
- SWD odpowiada na ID `0x2ba01477`.
- STATUS APPROTECT/odblokowanie nie dało potwierdzonego sukcesu.
- Potwierdzony wariant z pomiarów: zazwyczaj `0x23000000`.
- Niepotwierdzony wariant `0x00000000` pojawiał się sporadycznie i nie oznacza odblokowania.

## Podłączenie

- ESP32 GPIO21 -> nRF52 pin25, SWDCLK.
- ESP32 GPIO19 -> nRF52 pin26, SWDIO.
- ESP32 GPIO22 -> nRF52 VDD/3.3 V.
- ESP32 GND -> nRF52 GND.
- ESP32 GPIO5 -> bramka IRLZ44N.
- Drain IRLZ44N -> nRF52 DEC1.
- Source IRLZ44N -> wspólna masa.

GPIO34 jest skonfigurowane jako ADC dla analizy przebiegu. Aktualnie jest to wejście `OSCI_PIN=34`.

## Aktualne sterowanie firmware

Źródła główne:

- `src/glitcher.cpp` - sekwencja odcięcia zasilania i impulsu.
- `src/glitcher.h` - interfejs glitchera i pomiaru ADC.
- `src/lab_controller.cpp` - komendy szeregu.
- `src/main.cpp` - uruchomienie SWD i kontrolera laboratoryjnego.
- `src/nrf_swd.cpp` - inicjalizacja SWD i odczyt stanu zabezpieczenia.
- `platformio.ini` - piny i konfiguracja środowiska.

Nie dodawać funkcji odczytu ani eksportu pamięci flash.

## Komendy kontrolera szeregowego

Połączyć się z `/dev/ttyUSB0`, 115200 bps:

```text
STATUS
SET delay=2000 delay_end=2000 width=30 power_off=50 swd_wait=100
START
STOP
ADC delay=2000 width=30 power_off=50 sample_us=10 samples=500
```

Oczekiwane komunikaty wyników:

```text
LAB_READY
LAB_STATUS enabled=0 delay_us=... delay_end_us=... width_us=... power_off_ms=... swd_wait_ms=...
LAB_ATTEMPT id=... delay_us=... width_us=... power_off_ms=... swd_wait_ms=...
LAB_RESULT id=... swd=0x... variant=0x... unlocked=0|1 success=0|1
LAB_ADC_HEADER ...
LAB_ADC time_us=... value=...
LAB_ADC_END
```

## Aktualne skrypty

Wszystkie skrypty korzystają z `uv`.

### Jednorazowy zestaw parametrów

```bash
uv run python tools/lab_run.py \
  --delay-us 2000 \
  --width-us 30 \
  --timeout-s 10 \
  --output lab_results.csv \
  --run
```

Bez `--run` skrypt nie uruchamia glitchera.

### Raster timingów

```bash
uv run python tools/lab_sweep.py \
  --delays-us 1000,1500,2000,2500,3000,3500,4000,4500,5000,5500,6000 \
  --widths-us 35,40,50,60,75,100 \
  --point-timeout-s 0.6 \
  --output lab_sweep_fine.csv \
  --run
```

`lab_sweep.py` ma limit 200 punktów i zapisuje pełny CSV.

### Pomiar ADC

```bash
uv run python tools/lab_adc.py \
  --delay-us 2000 \
  --width-us 30 \
  --power-off-ms 50 \
  --sample-us 10 \
  --samples 500 \
  --output lab_adc_width30.csv \
  --run
```

## Wyniki dotychczas

### Próba bazowa

- Opóźnienie: `2000 µs`.
- Szerokość: `0 µs`.
- Odcięcie zasilania: `50 ms`.
- Oczekiwanie SWD: `100 ms`.
- Wynik: `47` próbek bez odblokowania.
- Wszystkie próby dały `unlocked=0`, `success=0`.

### Raster szerokości i opóźnienia

- Pokryto szerokości `1–100 µs`.
- Pokryto opóźnienia od `0 µs` do `30000 µs`.
- Pokryto szczególnie wczesne okno `0–1000 µs`.
- Pokryto odcięcie zasilania `20, 50, 100 i 200 ms`.
- Łącznie wykonano ponad 1000 prób punktowych.
- Nie ma potwierdzonego sukcesu ani potwierdzonego przejścia APPROTECT.
- Najczęstsza odpowiedź po impulsie:
  - SWD: `0x2ba01477`,
  - wariant: `0x23000000`,
  - unlocked: `0`,
  - success: `0`.
- `0x00000000` pojawiło się sporadycznie przy mocniejszych impulsach; nie interpretować jako odblokowania.

### Pomiar ADC GPIO34

Parametr bazowy:

- opóźnienie `2000 µs`,
- odcięcie `50 ms`,
- próbkowanie `10 µs`,
- 500 próbek, czas całkowity około `26846 µs`.

#### Impuls 10 µs

- Poziom bazowy ADC: około `1465–1470`.
- Pierwsze silne zanurzenie: około `2020 µs`.
- Po zanurzeniu poziom stabilizuje się około `1200`.
- Odczytywane zanurzenie prawie natychmiastowe, dokładność ograniczona przez ADC i czas serializacji.

#### Impuls 30 µs

- Pierwsze silne zanurzenie: około `2009 µs`.
- Poziom `0` od `2009` do `2062 µs`.
- Rzeczywiste zanurzenie odczytane z ADC: około `53 µs`.
- Ostateczny poziom po impulsie: około `1200`.

#### Impuls 100 µs

- Pierwsze silne zanurzenie: około `2044 µs`.
- Poziom `0` od `2044` do `2148 µs`.
- Rzeczywiste zanurzenie odczytane z ADC: około `104 µs`.
- Ostateczny poziom po impulsie: około `1200`.

Wniosek ADC:

- Opóźnienie sprzętowe względem parametru wynosi około `9–44 µs`.
- ADC potwierdza zmianę poziomu i czas impulsu.
- ADC nie potwierdza, że w badanym punkcie doszło do odblokowania nRF52832.
- Pomiar ADC i SWD powinien być następnie korelowany w tym samym czasie za pomocą oscyloskopu lub analizatora logicznego.

## Pliki danych

- `lab_results.csv` - początkowe próby bazowe.
- `lab_sweep.csv` - szerokości `1–30 µs`, opóźnienia `1–30 ms`.
- `lab_sweep_fine.csv` - szerokości `35–100 µs`, opóźnienia `1–6 ms`.
- `lab_sweep_boot.csv` - okno wczesne `0–1000 µs`, szerokości `10–100 µs`.
- `lab_power_sweep.csv` - odcięcie zasilania `20–200 ms`.
- `lab_adc.csv` - pełny przebieg ADC dla impulsu `10 µs`.
- `lab_adc_small.csv` - mały przebieg ADC `20` próbek.
- `lab_adc_width30.csv` - przebieg ADC dla impulsu `30 µs`.
- `lab_adc_width100.csv` - przebieg ADC dla impulsu `100 µs`.
- `lab_results.csv` i pozostałe CSV są metadanymi testów, nie zawierają pobranego firmware ani pamięci.
- Załączony log terminala:
  `/home/darkroom2/.config/Code/agentSessionData/95555b9b-b53b-4996-ad20-42175d2a1c51/attachments/420bed09-0672-45e0-8b94-da92e694efa7/file_terminal-output-z1ksk.txt`

## Jak budować i wgrywać

Budowa:

```bash
uv run pio run -e ESP32_nRF52_SWD
```

Wgrywanie:

```bash
uv run pio run -e ESP32_nRF52_SWD -t upload --upload-port /dev/ttyUSB0
```

Monitor:

```bash
uv run python -m serial.tools.miniterm /dev/ttyUSB0 115200 --rts 0 --dts 0
```

## Od czego zacząć nową sesję

1. Potwierdzić, że firmware jest wgrane.
2. Potwierdzić, że płytka nRF52832 nie została zmieniona przez poprzednie operacje.
3. Potwierdzić fizyczne połączenie:
   - GPIO21 SWDCLK,
   - GPIO19 SWDIO,
   - GPIO22 VDD,
   - wspólną masę,
   - GPIO5 bramkę IRLZ44N,
   - drain IRLZ44N DEC1.
4. Nie uruchamiać żadnych endpointów lub funkcji odczytu flash.
5. Najpierw zebrać `STATUS` i potwierdzić SWD `0x2ba01477`.
6. Użyć oscyloskopu na:
   - GPIO34 jako ADC i wyjście referencyjne,
   - nRF52 VDD,
   - nRF52 DEC1,
   - wspólnej masie,
   - GPIO5 jako trigger/impuls.
7. Powtórzyć pomiar referencyjny:
   - power-off `50 ms`,
   - delay `2000 µs`,
   - width `30–100 µs`.
8. Dopiero po korelacji oscyloskopowej uruchomić nowy raster węższy niż dotychczasowe `1 µs`.

## Najbardziej prawdopodobna kolejna hipoteza

Bieżące wyniki nie wykluczają power-glitchingu, ale nie potwierdzają właściwego momentu boot-time.

Następny etap powinien opierać się na:

- pomiarze fali zasilania oscyloskopem,
- pomiarze równoległym DEC1 i VDD,
- korelacjach triggera GPIO5,
- czasie od ponownego podania VDD,
- większej liczbie powtórzeń dla kilku wąskich okien,
- zmianach width i delay wokół okna bootowym, nie losowym przeszukiwaniu całego zakresu.

Nie zmieniać i nie kasować pamięci flash. Całe sukcesy należy potwierdzić tylko przez stan SWD/APPROTECT, bez pobierania zawartości.
