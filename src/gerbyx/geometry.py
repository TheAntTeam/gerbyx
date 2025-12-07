import re
from dataclasses import dataclass


@dataclass
class Geometry:
    kind: str
    x: float | None
    y: float | None
    aperture: str | None


def _parse_stmt(self, value):
    if value.startswith("D"):
        self.current_aperture = value
        return

    m = re.match(r"X(\d+)Y(\d+)(D\d+)", value)
    if m:
        x = int(m.group(1)) / 1000.0
        y = int(m.group(2)) / 1000.0
        dcode = m.group(3)
        print("dcode ->", dcode)
        kind = {"D01": "draw", "D02": "move", "D03": "flash"}.get(dcode, "unknown")
        print(kind)
        self.geometries.append(Geometry(kind, x, y, self.current_aperture))
        print(self.geometries)
        return

    if value.startswith("G36"):
        self.geometries.append(Geometry("region_start", None, None, None))
    elif value.startswith("G37"):
        self.geometries.append(Geometry("region_end", None, None, None))
    elif value.startswith("M02"):
        self.geometries.append(Geometry("end_of_file", None, None, None))
