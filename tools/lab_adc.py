#!/usr/bin/env python3

import argparse
import csv
import re
import sys
import time

import serial


HEADER_RE = re.compile(
    r"LAB_ADC_HEADER delay_us=(\d+) width_us=(\d+) "
    r"power_off_ms=(\d+) sample_period_us=(\d+) samples=(\d+)"
)
SAMPLE_RE = re.compile(r"LAB_ADC time_us=(\d+) value=(\d+)")


def main():
    parser = argparse.ArgumentParser(
        description="Capture GPIO34 ADC samples around a test pulse."
    )
    parser.add_argument("--port", default="/dev/ttyUSB0")
    parser.add_argument("--delay-us", type=int, default=2000)
    parser.add_argument("--width-us", type=int, default=10)
    parser.add_argument("--power-off-ms", type=int, default=50)
    parser.add_argument("--sample-us", type=int, default=10)
    parser.add_argument("--samples", type=int, default=500)
    parser.add_argument("--output", default="lab_adc.csv")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()

    if not args.run:
        print("Refusing capture: add --run.", file=sys.stderr)
        return 2

    with serial.Serial(
        args.port,
        115200,
        timeout=0.2,
        rtscts=False,
        dsrdtr=False,
    ) as port:
        port.setDTR(False)
        port.setRTS(False)
        port.reset_input_buffer()
        time.sleep(0.5)

        port.write(
            (
                f"ADC delay={args.delay_us} width={args.width_us} "
                f"power_off={args.power_off_ms} sample_us={args.sample_us} "
                f"samples={args.samples}\n"
            ).encode("ascii")
        )
        port.flush()

        deadline = time.monotonic() + 10
        header = None
        with open(args.output, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=[
                    "timestamp",
                    "delay_us",
                    "width_us",
                    "power_off_ms",
                    "sample_period_us",
                    "time_us",
                    "value",
                ],
            )
            writer.writeheader()

            while time.monotonic() < deadline:
                line = port.readline().decode("ascii", "replace").strip()
                if not line:
                    continue

                header_match = HEADER_RE.search(line)
                if header_match:
                    header = header_match.groups()
                    continue

                sample_match = SAMPLE_RE.search(line)
                if sample_match and header:
                    sample_time, value = sample_match.groups()
                    writer.writerow(
                        {
                            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                            "delay_us": args.delay_us,
                            "width_us": args.width_us,
                            "power_off_ms": args.power_off_ms,
                            "sample_period_us": args.sample_us,
                            "time_us": sample_time,
                            "value": value,
                        }
                    )

                if line == "LAB_ADC_END":
                    break

    print(f"LAB_ADC_DONE output={args.output}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
