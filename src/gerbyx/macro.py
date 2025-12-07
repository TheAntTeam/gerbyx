from dataclasses import dataclass


@dataclass
class Macro:
    name: str
    body: list[str]   # lista di primitive


def _parse_macro_start(self, value: str):
    # es: "AMRECT*"
    name = value[2:-1]  # togli "AM" e "*"
    self.current_macro = name
    self.macros[name] = []


def _parse_macro_body(self, value: str):
    # es: "0 Rectangle,1.0X2.0,0,0*"
    self.macros[self.current_macro].append(value)
    # se arriva un '%', chiudi la macro
    if value.endswith("%"):
        self.current_macro = None
