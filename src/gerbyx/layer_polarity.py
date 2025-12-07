from dataclasses import dataclass


@dataclass
class LayerPolarity:
    mode: str   # "DARK" o "CLEAR"


def _parse_layer_polarity(self, value: str):
    # value es: "LPD*" oppure "LPC*"
    body = value[2:-1]  # togli "LP" e "*"
    if body == "D":
        self.layer_polarity = LayerPolarity("DARK")
    elif body == "C":
        self.layer_polarity = LayerPolarity("CLEAR")
    else:
        raise ValueError(f"Polarity not supported: {body}")
