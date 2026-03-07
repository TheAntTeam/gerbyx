from typing import Generator, Tuple, Optional
import re

from .processor import GerberProcessor
from .aperture import parse_aperture_def
from .format import parse_format_spec
from .units import parse_units
from .layer_polarity import parse_layer_polarity
from .macro import Macro, parse_macro_start, parse_macro_body
from .blocks import ApertureBlock, parse_ab_start, is_ab_end

class GerberParser:
    def __init__(self, processor: GerberProcessor):
        self.processor = processor
        self.current_macro_name: Optional[str] = None
        self.current_macro_body: list[str] = []
        self.current_ab_id: Optional[str] = None
        self.current_ab_tokens: list[Tuple[str, str]] = []

    def parse(self, tokens: Generator[Tuple[str, str], None, None]):
        for kind, value in tokens:
            # Gestione Aperture Block (AB)
            if self.current_ab_id:
                if kind == 'param' and is_ab_end(value):
                    self._finalize_ab()
                else:
                    self.current_ab_tokens.append((kind, value))
                continue

            # Gestione Macro in corso
            if self.current_macro_name and kind == 'param':
                is_primitive = re.match(r'^\d', value) or value.startswith('$')

                if is_primitive:
                    self.current_macro_body.append(parse_macro_body(value))
                    continue
                else:
                    self._finalize_macro()

            elif self.current_macro_name and kind != 'param':
                self._finalize_macro()

            # Parsing normale
            if kind == 'param':
                self._parse_param(value)
            elif kind == 'stmt':
                self._parse_stmt(value)
            elif kind == 'comment':
                pass

        self._finalize_macro()
        self._finalize_ab()

    def _parse_param(self, value: str):
        if value.startswith("AB"):
            if is_ab_end(value):
                pass
            else:
                self.current_ab_id = parse_ab_start(value)
                self.current_ab_tokens = []
            return

        if value.startswith("AM"):
            if self.current_macro_name:
                self._finalize_macro()

            if len(value) > 3:
                self.current_macro_name = parse_macro_start(value)
                self.current_macro_body = []
            return

        if value.startswith("FS"): self.processor.set_format_spec(parse_format_spec(value))
        elif value.startswith("MO"): self.processor.set_units(parse_units(value).code)
        elif value.startswith("AD"): self.processor.define_aperture(parse_aperture_def(value))
        elif value.startswith("LP"):
            polarity = parse_layer_polarity(value)
            self.processor.set_layer_polarity(polarity.mode)

    def _finalize_macro(self):
        if self.current_macro_name:
            macro = Macro(self.current_macro_name, self.current_macro_body)
            self.processor.define_macro(macro)
            self.current_macro_name = None
            self.current_macro_body = []

    def _finalize_ab(self):
        if self.current_ab_id:
            ab = ApertureBlock(self.current_ab_id, self.current_ab_tokens)
            self.processor.define_aperture_block(ab)
            self.current_ab_id = None
            self.current_ab_tokens = []

    def _parse_stmt(self, value: str):
        if value.endswith('*'): value = value[:-1]
        self._handle_g_code(value)
        self._handle_coordinates_and_dcode(value)

    def _handle_g_code(self, value: str):
        g_codes = re.findall(r'G(\d{2})', value)
        for code in g_codes:
            if code == '01': self.processor.set_interpolation_mode('Linear')
            elif code == '02': self.processor.set_interpolation_mode('ClockwiseCircular')
            elif code == '03': self.processor.set_interpolation_mode('CounterClockwiseCircular')
            elif code == '36': self.processor.start_region()
            elif code == '37': self.processor.end_region()
            elif code == '74': self.processor.set_quadrant_mode('Single')
            elif code == '75': self.processor.set_quadrant_mode('Multi')

    def _handle_coordinates_and_dcode(self, value: str):
        def get_val(char, text):
            match = re.search(rf"{char}([+-]?[\d\.]+)", text)
            if match: return self.processor.parse_value(match.group(1), is_x=(char in ['X', 'I']))
            return None

        x, y, i, j = get_val('X', value), get_val('Y', value), get_val('I', value), get_val('J', value)
        d_match = re.search(r'D(\d+)', value)
        d_code = int(d_match.group(1)) if d_match else None

        if d_code is not None:
            if d_code == 1:
                center = (i, j) if (i is not None or j is not None) else None
                self.processor.draw_to(x, y, center)
            elif d_code == 2: self.processor.update_point(x, y)
            elif d_code == 3: self.processor.flash_at(x, y)
            elif d_code >= 10:
                self.processor.select_aperture(f"D{d_code}")
                if x is not None or y is not None: self.processor.update_point(x, y)
        elif x is not None or y is not None:
            self.processor.update_point(x, y)
