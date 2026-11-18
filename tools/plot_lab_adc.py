#!/usr/bin/env python3

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt


def read_csv(path: Path):
    times = []
    values = []

    with path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            if not row.get("time_us") or not row.get("value"):
                continue
            times.append(int(row["time_us"]))
            values.append(int(row["value"]))

    points = sorted(zip(times, values), key=lambda point: point[0])
    if not points:
        raise ValueError(f"No ADC samples found in {path}")

    return zip(*points)


def main():
    parser = argparse.ArgumentParser(
        description="Plot ADC time-series CSV files produced by lab_adc.py."
    )
    parser.add_argument("csv_files", nargs="+", type=Path)
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("lab_adc_plot.png"),
        help="Output image path.",
    )
    parser.add_argument(
        "--title",
        default="nRF52 ADC measurement",
        help="Plot title.",
    )
    parser.add_argument(
        "--xlim",
        nargs=2,
        type=float,
        metavar=("MIN_US", "MAX_US"),
        help="Limit the time axis.",
    )
    args = parser.parse_args()

    fig, ax = plt.subplots(figsize=(12, 6))

    for csv_path in args.csv_files:
        times, values = read_csv(csv_path)
        ax.plot(times, values, linewidth=1.5, label=csv_path.stem)

    ax.set_title(args.title)
    ax.set_xlabel("Czas [µs]")
    ax.set_ylabel("Wartość ADC (12-bit)")
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 4095)
    if args.xlim:
        ax.set_xlim(*args.xlim)
    if len(args.csv_files) > 1:
        ax.legend()

    fig.tight_layout()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=150)
    plt.close(fig)
    print(f"PLOT_DONE output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
