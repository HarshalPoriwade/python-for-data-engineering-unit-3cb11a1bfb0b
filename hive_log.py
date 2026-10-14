"""Read a hive scale log from standard input and print a summary per hive."""
import sys

SWARM_DROP_KG=2.0
MIN_TEMP=-10.0
MAX_TEMP=45.0
def parse_line(line):
    """Turn one log line into a reading dict, or None if the line is unusable."""
    line=line.strip().lstrip("")
    if not line:
        return None
    parts=[part.strip() for part in line.split(",")]
    if len(parts)!=5:
        return None
    date,time,hive,weight,temp=parts
    try:
        return {
            "date": date,
            "time": time,
            "hive": hive,
            "weight": float(weight),
            "temp": float(temp),
        }
    except ValueError:
        return None
def parse_log(text):
    """Group readings by hive, keeping hives in the order they first appear."""
    hives = {}
    for line in text.splitlines():
        reading = parse_line(line)
        if reading is None:
            continue
        hives.setdefault(reading["hive"], []).append(reading)
    for readings in hives.values():
        readings.sort(key=lambda r: (r["date"], r["time"]))
    return hives
def biggest_daily_drop(readings):
    """Return the largest one-day weight loss (a negative number, or 0.0).

    Each day is measured from the last weight of the day before
    (or the day's own first weight, on the first day) to the last weight of the day.
    """
    last_of_day = {}
    for r in readings:
        last_of_day[r["date"]] = r["weight"]
    worst = 0.0
    previous = readings[0]["weight"]
    for date in sorted(last_of_day):
        change = last_of_day[date] - previous
        worst = min(worst, change)
        previous = last_of_day[date]
    return worst


def has_sensor_error(readings):
    return any(r["temp"] < MIN_TEMP or r["temp"] > MAX_TEMP for r in readings)


def summarize(hive, readings):
    """Build the output lines for one hive."""
    first = readings[0]["weight"]
    last = readings[-1]["weight"]
    change = round(last - first, 2)
    lines = [
        f"{hive}: {len(readings)} readings, first {first:.1f} kg, "
        f"last {last:.1f} kg, change {change:+.1f} kg"
    ]
    if round(biggest_daily_drop(readings), 2) <= -SWARM_DROP_KG:
        lines.append(f"Possible swarm: {hive}")
    if has_sensor_error(readings):
        lines.append(f"Sensor error: {hive}")
    return lines


def report(text):
    hives = parse_log(text)
    if not hives:
        return ["No readings found."]
    lines = []
    for hive, readings in hives.items():
        lines.extend(summarize(hive, readings))
    return lines


def main():
    for line in report(sys.stdin.read()):
        print(line)


if __name__ == "__main__":
    main()