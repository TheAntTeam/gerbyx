from dataclasses import dataclass


@dataclass
class Units:
    code: str   # "IN" o "MM"


def _parse_units(self, value: str):
    # value es: "MOIN*" oppure "MOMM*"
    body = value[2:-1]  # togli "MO" e "*"
    if body == "IN":
        self.units = Units("IN")
    elif body == "MM":
        self.units = Units("MM")
    else:
        raise ValueError(f"Units not supported: {body}")
