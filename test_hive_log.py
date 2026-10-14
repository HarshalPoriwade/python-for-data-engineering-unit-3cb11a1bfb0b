import unittest
from hive_log import parse_line, parse_log,biggest_daily_drop,report
class ParseTests(unittest.TestCase):
    def test_parse_line_with_extra_spaces(self):
        r = parse_line("  2025-06-01 , 08:00 ,  HiveA , 30.5 , 18  ")
        self.assertEqual(r["hive"], "HiveA")
        self.assertEqual(r["weight"], 30.5)
        self.assertEqual(r["temp"], 18.0)
    def test_blank_and_broken_lines_are_skipped(self):
        self.assertIsNone(parse_line(""))
        self.assertIsNone(parse_line("   \r\n"))
        self.assertIsNone(parse_line("2025-06-01,08:00,HiveA,30.5"))
        self.assertIsNone(parse_line("2025-06-01,08:00,HiveA,heavy,18"))
    def test_windows_line_endings(self):
        text = "2025-06-01,08:00,HiveA,30.5,18\r\n\r\n2025-06-02,08:00,HiveA,27.0,20\r\n"
        hives = parse_log(text)
        self.assertEqual(len(hives["HiveA"]), 2)
    def test_readings_sorted_by_date_and_time(self):
        text = "2025-06-02,08:00,HiveA,27.0,20\n2025-06-01,08:00,HiveA,30.5,18\n"
        readings = parse_log(text)["HiveA"]
        self.assertEqual(readings[0]["weight"], 30.5)
        self.assertEqual(readings[-1]["weight"], 27.0)
class ReportTests(unittest.TestCase):
    def test_example_from_task(self):
        text = "2025-06-01,08:00,HiveA,30.5,18\n2025-06-02,08:00,HiveA,27.0,20\n"
        self.assertEqual(report(text), [
            "HiveA: 2 readings, first 30.5 kg, last 27.0 kg, change -3.5 kg",
            "Possible swarm: HiveA",
        ])

    def test_exactly_two_kg_drop_is_a_swarm(self):
        text = "2025-06-01,08:00,HiveA,16.4,18\n2025-06-02,08:00,HiveA,14.4,20\n"
        self.assertIn("Possible swarm: HiveA", report(text))

    def test_small_drop_is_not_a_swarm(self):
        text = "2025-06-01,08:00,HiveA,30.0,18\n2025-06-02,08:00,HiveA,28.5,20\n"
        self.assertNotIn("Possible swarm: HiveA", report(text))

    def test_slow_loss_over_several_days_is_not_a_swarm(self):
        text = ("2025-06-01,08:00,HiveA,30.0,18\n"
                "2025-06-02,08:00,HiveA,29.0,18\n"
                "2025-06-03,08:00,HiveA,28.0,18\n")
        lines = report(text)
        self.assertEqual(lines[0], "HiveA: 3 readings, first 30.0 kg, last 28.0 kg, change -2.0 kg")
        self.assertNotIn("Possible swarm: HiveA", lines)

    def test_drop_within_one_day_is_a_swarm(self):
        text = "2025-06-01,08:00,HiveA,30.0,18\n2025-06-01,14:00,HiveA,27.5,25\n"
        self.assertEqual(biggest_daily_drop(parse_log(text)["HiveA"]), -2.5)
        self.assertIn("Possible swarm: HiveA", report(text))

    def test_sensor_error_limits(self):
        ok = "2025-06-01,08:00,HiveA,30.0,-10\n2025-06-01,09:00,HiveA,30.0,45\n"
        self.assertNotIn("Sensor error: HiveA", report(ok))
        cold = "2025-06-01,08:00,HiveA,30.0,-10.5\n"
        self.assertIn("Sensor error: HiveA", report(cold))
        hot = "2025-06-01,08:00,HiveA,30.0,45.1\n"
        self.assertIn("Sensor error: HiveA", report(hot))

    def test_two_hives_kept_apart_in_order(self):
        text = ("2025-06-01,08:00,HiveB,25.0,18\n"
                "2025-06-01,08:00,HiveA,30.0,18\n"
                "2025-06-02,08:00,HiveB,25.5,60\n")
        lines = report(text)
        self.assertEqual(lines, [
            "HiveB: 2 readings, first 25.0 kg, last 25.5 kg, change +0.5 kg",
            "Sensor error: HiveB",
            "HiveA: 1 readings, first 30.0 kg, last 30.0 kg, change +0.0 kg",
        ])

    def test_empty_input(self):
        self.assertEqual(report("\n   \n"), ["No readings found."])


if __name__ == "__main__":
    unittest.main()
        