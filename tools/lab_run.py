#!/usr/bin/env python3

import argparse
import csv
import re
import sys
import time

import serial


RESULT_RE = re.compile(
    r"LAB_RESULT id=(\d+) swd=(0x[0-9a-fA-F]+) "
    r"variant=(0x[0-9a-fA-F]+) unlocked=(\d+) success=(\d+)"
)


def send(port, command):
    port.write((command + "\n").encode("ascii"))
    port.flush()


def read_until(port, timeout_s):
    deadline = time.monotonic() + timeout_s
    rows = []
    success = False

    while time.monotonic() < deadline:
        line = port.readline().decode("ascii", "replace").strip()
        if not line:
            continue

        print(line, flush=True)
        match = RESULT_RE.search(line)
        if match:
            attempt_id, swd_id, variant, unlocked, result_success = match.groups()
            row = {
                "attempt_id": attempt_id,
                "swd_id": swd_id,
                "variant": variant,
                "unlocked": unlocked,
                "success": result_success,
            }
            rows.append(row)
            if result_success == "1":
                success = True

        if success:
            break

    return rows, success


def main():
    parser = argparse.ArgumentParser(
        description="Run safe nRF52 timing measurements; memory read/write is never accessed."
    )
    parser.add_argument("--port", default="/dev/ttyUSB0")
    parser.add_argument("--delay-us", type=int, required=True)
    parser.add_argument("--width-us", type=int, required=True)
    parser.add_argument("--power-off-ms", type=int, default=50)
    parser.add_argument("--swd-wait-ms", type=int, default=100)
    parser.add_argument("--timeout-s", type=float, default=10.0)
    parser.add_argument("--output", default="lab_results.csv")
    parser.add_argument(
        "--run",
        action="store_true",
        help="required confirmation to start glitch attempts",
    )
    args = parser.parse_args()

    if not args.run:
        print("Refusing to start: add --run to confirm a timing run.", file=sys.stderr)
        return 2

    fieldnames = [
        "timestamp",
        "delay_us",
        "width_us",
        "power_off_ms",
        "swd_wait_ms",
        "attempt_id",
        "swd_id",
        "variant",
        "unlocked",
        "success",
    ]

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

        send(
            port,
            f"SET delay={args.delay_us} delay_end={args.delay_us} "
            f"width={args.width_us} power_off={args.power_off_ms} "
            f"swd_wait={args.swd_wait_ms}",
        )
        time.sleep(0.5)
        send(port, "START")
        rows, success = read_until(port, args.timeout_s)
        send(port, "STOP")

    with open(args.output, "a", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        if csv_file.tell() == 0:
            writer.writeheader()

        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        for row in rows:
            writer.writerow(
                {
                    "timestamp": timestamp,
                    "delay_us": args.delay_us,
                    "width_us": args.width_us,
                    "power_off_ms": args.power_off_ms,
                    "swd_wait_ms": args.swd_wait_ms,
                    **row,
                }
            )

    print(
        f"LAB_RUN_DONE samples={len(rows)} success={'yes' if success else 'no'} "
        f"output={args.output}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
