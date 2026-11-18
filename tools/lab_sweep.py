#!/usr/bin/env python3

import argparse
import csv
import re
import sys
import time

import serial


ATTEMPT_RE = re.compile(
    r"LAB_ATTEMPT id=(\d+) delay_us=(\d+) width_us=(\d+) "
    r"power_off_ms=(\d+) swd_wait_ms=(\d+)"
)
RESULT_RE = re.compile(
    r"LAB_RESULT id=(\d+) swd=(0x[0-9a-fA-F]+) "
    r"variant=(0x[0-9a-fA-F]+) unlocked=(\d+) success=(\d+)"
)


def send(port, command):
    port.write((command + "\n").encode("ascii"))
    port.flush()


def values(start, end, step):
    value = start
    while value <= end:
        yield value
        value += step


def run_point(port, delay_us, width_us, power_off_ms, swd_wait_ms, timeout_s):
    send(
        port,
        f"SET delay={delay_us} delay_end={delay_us} width={width_us} "
        f"power_off={power_off_ms} swd_wait={swd_wait_ms}",
    )
    time.sleep(0.15)
    send(port, "START")

    deadline = time.monotonic() + timeout_s
    rows = []

    while time.monotonic() < deadline:
        line = port.readline().decode("ascii", "replace").strip()
        if not line:
            continue

        attempt_match = ATTEMPT_RE.search(line)
        if attempt_match:
            attempt_id = attempt_match.group(1)
            print(line, flush=True)

        result_match = RESULT_RE.search(line)
        if result_match:
            attempt_id, swd_id, variant, unlocked, success = result_match.groups()
            print(line, flush=True)
            rows.append(
                {
                    "attempt_id": attempt_id,
                    "swd_id": swd_id,
                    "variant": variant,
                    "unlocked": unlocked,
                    "success": success,
                }
            )
            if success == "1":
                send(port, "STOP")
                return rows, True

    send(port, "STOP")
    return rows, False


def main():
    parser = argparse.ArgumentParser(
        description="Run a bounded coarse timing sweep without memory access."
    )
    parser.add_argument("--port", default="/dev/ttyUSB0")
    parser.add_argument("--delay-start-us", type=int, default=1000)
    parser.add_argument("--delay-end-us", type=int, default=30000)
    parser.add_argument("--delay-step-us", type=int, default=1000)
    parser.add_argument("--width-start-us", type=int, default=1)
    parser.add_argument("--width-end-us", type=int, default=30)
    parser.add_argument("--width-step-us", type=int, default=1)
    parser.add_argument("--delays-us")
    parser.add_argument("--widths-us")
    parser.add_argument("--power-off-ms", type=int, default=50)
    parser.add_argument("--swd-wait-ms", type=int, default=100)
    parser.add_argument("--point-timeout-s", type=float, default=0.5)
    parser.add_argument("--output", default="lab_sweep.csv")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()

    if args.delays_us:
        delays = [int(value) for value in args.delays_us.split(",") if value]
    else:
        delays = list(values(args.delay_start_us, args.delay_end_us, args.delay_step_us))

    if args.widths_us:
        widths = [int(value) for value in args.widths_us.split(",") if value]
    else:
        widths = list(values(args.width_start_us, args.width_end_us, args.width_step_us))

    if not args.run:
        print("Refusing to start: add --run.", file=sys.stderr)
        return 2
    if len(delays) * len(widths) > 200:
        print("Refusing sweep: more than 200 points.", file=sys.stderr)
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
        timeout=0.05,
        rtscts=False,
        dsrdtr=False,
    ) as port:
        port.setDTR(False)
        port.setRTS(False)
        port.reset_input_buffer()
        time.sleep(1)

        with open(args.output, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()

            for width in widths:
                for delay in delays:
                    print(
                        f"LAB_POINT delay_us={delay} width_us={width}",
                        flush=True,
                    )
                    rows, success = run_point(
                        port,
                        delay,
                        width,
                        args.power_off_ms,
                        args.swd_wait_ms,
                        args.point_timeout_s,
                    )
                    timestamp = time.strftime("%Y-%m-%dT%H:%M:%S%z")
                    if rows:
                        for row in rows:
                            writer.writerow(
                                {
                                    "timestamp": timestamp,
                                    "delay_us": delay,
                                    "width_us": width,
                                    "power_off_ms": args.power_off_ms,
                                    "swd_wait_ms": args.swd_wait_ms,
                                    **row,
                                }
                            )
                    else:
                        writer.writerow(
                            {
                                "timestamp": timestamp,
                                "delay_us": delay,
                                "width_us": width,
                                "power_off_ms": args.power_off_ms,
                                "swd_wait_ms": args.swd_wait_ms,
                                "attempt_id": "",
                                "swd_id": "",
                                "variant": "",
                                "unlocked": "",
                                "success": "",
                            }
                        )
                    csv_file.flush()

                    if success:
                        print(
                            f"LAB_SWEEP_SUCCESS delay_us={delay} width_us={width}",
                            flush=True,
                        )
                        return 0

    print("LAB_SWEEP_DONE no success", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
