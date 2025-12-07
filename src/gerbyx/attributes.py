from dataclasses import dataclass


@dataclass
class Attribute:
    scope: str   # "file", "aperture", "object", "component"
    name: str
    values: list[str]


def _parse_attribute(self, value, scope):
    body = value[:-1] if value.endswith("*") else value
    parts = body.split(",")
    name = parts[0]  # es: TF.FileFunction
    values = parts[1:]
    attr = Attribute(scope, name, values)
    self.attributes.setdefault(scope, []).append(attr)


def _terminate_attribute(self):
    self.current_attribute = None
