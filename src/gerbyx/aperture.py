import re
from dataclasses import dataclass


@dataclass
class Aperture:
    id: str
    type: str
    params: list[float]


def _parse_aperture_def(self, value):
    # value es: "ADD10R,1.100000X1.000000*"
    body = value[2:-1]  # togli "AD" e "*"
    regex = r"(\d+)"
    matches = re.finditer(regex, body, re.MULTILINE)
    aperture_id = next(matches).group()
    rest = body[len(aperture_id):]
    if rest[0].isdigit():
        rest = rest[1:]

    if rest.startswith("C"):
        # Circle
        diameter = float(rest.split(",")[1])
        self.apertures[aperture_id] = Aperture(aperture_id, "C", [diameter])
    elif rest.startswith("R"):
        # Rectangle
        dims = rest.split(",")[1].split("X")
        self.apertures[aperture_id] = Aperture(aperture_id, "R", [float(dims[0]), float(dims[1])])
    elif rest.startswith("O"):
        # Obround
        dims = rest.split(",")[1].split("X")
        self.apertures[aperture_id] = Aperture(aperture_id, "O", [float(dims[0]), float(dims[1])])
    elif rest.startswith("P"):
        # Polygon
        parts = rest.split(",")[1].split("X")
        diameter = float(parts[0])
        vertices = int(parts[1])
        rotation = float(parts[2]) if len(parts) > 2 else 0.0
        self.apertures[aperture_id] = Aperture(aperture_id, "P", [diameter, vertices, rotation])
    else:
        # Macro reference: if type is not C/R/O/P, assume is macro
        macro_name = rest.split(",", 1)[0].strip()  # fino alla virgola o fine stringa
        print("Macro Name:", macro_name)
        self.apertures[aperture_id] = Aperture(aperture_id, rest[0], [])
