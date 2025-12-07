from dataclasses import dataclass, field
from .format import FormatSpec


@dataclass
class PlotState:
    fmt: FormatSpec = field(default_factory=FormatSpec)
    x: float | None = None
    y: float | None = None
    interp: str = 'G01'
    quadrant_single: bool = False
    region_mode: bool = False
    current_ap: int | None = None
    polarity: str = 'D'
