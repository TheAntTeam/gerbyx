
from matplotlib.offsetbox import DraggableAnnotation
import copy
from gerbyx.aperture import _parse_aperture_def
from gerbyx.attributes import _parse_attribute, _terminate_attribute
from gerbyx.macro import _parse_macro_start, _parse_macro_body
from gerbyx.geometry import _parse_stmt
from gerbyx.format import _parse_format_spec
from gerbyx.units import _parse_units
from gerbyx.layer_polarity import _parse_layer_polarity
from gerbyx.blocks import _parse_ab_end, _parse_ab_start, _collect_ab_body
from gerbyx.step_repeat import _parse_step_repeat


class GerberParser:
    def __init__(self):
        self.format_spec = None
        self.units = None
        self.layer_polarity = None
        _parse_layer_polarity(self, value="LPD*")
        self.apertures = {}
        self.macros = {}
        self.attributes = {}
        self.geometries = []
        self.aperture_blocks = {}
        self.current_aperture = None
        self.current_macro = None
        self.current_attribute = None
        self.current_ap_block = None

    def __str__(self):
        print("Format spec:", self.format_spec)
        print("Units:", self.units)
        print("Layer polarity:", self.layer_polarity)
        print("Apertures:", self.apertures)
        print("Macros:", self.macros)
        print("Attributes:", self.attributes)
        print("Blocks:")
        for block_id, block_body in self.aperture_blocks.items():
            print(f"  {block_id}:")
            print(block_body)
        print("Geometries:", self.geometries)
        return ""

    def parse(self, tokens):
        for kind, value in tokens:
            # Gestione AB aperto: cattura tutto (tranne la chiusura) nel corpo
            if self.current_ap_block is not None:
                if (kind == "param"
                        and (value.startswith("ABEND")
                             or (value.startswith("AB*") and self.current_ap_block is not None))):
                    self.resolve_current_block()
                    _parse_ab_end(self, value)
                    continue
                # Accumula qualsiasi cosa dentro il blocco
                _collect_ab_body(self, kind, value)
                continue
            print("*", kind, value)
            if kind == "param":
                # Format and Mode
                if value.startswith("FS"):
                    print("FS", value)
                    _parse_format_spec(self, value)
                elif value.startswith("MO"):
                    _parse_units(self, value)

                # Aperture AD AB.
                # le macro vengono gestite separatamente
                elif value.startswith("AD"):
                    _parse_aperture_def(self, value)

                elif value.startswith("AB"):
                    # start di un aperture block
                    _parse_ab_start(self, value)

                elif value.startswith("TF"):
                    _parse_attribute(self, value, "file")
                elif value.startswith("TA"):
                    _parse_attribute(self, value, "aperture")
                elif value.startswith("TO"):
                    _parse_attribute(self, value, "object")
                elif value.startswith("TCMP"):
                    _parse_attribute(self, value, "component")
                elif value.startswith("TD"):
                    _terminate_attribute(self)
                elif value.startswith("LP"):
                    _parse_layer_polarity(self, value)
                elif value.startswith("SR"):
                    _parse_step_repeat(self, value)
                # altri parametri FS, MO, LP...

            elif kind == "stmt":
                _parse_stmt(self, value)
            elif kind == "macro_start":
                _parse_macro_start(self, value)
            elif kind == "macro_body":
                _parse_macro_body(self, value)

    def resolve_current_block(self):
        local_gerber_parser = GerberParser()
        local_gerber_parser.format_spec = copy.deepcopy(self.format_spec)
        local_gerber_parser.units = copy.deepcopy(self.units)
        local_gerber_parser.layer_polarity = copy.deepcopy(self.layer_polarity)
        block_tokens = copy.deepcopy(self.aperture_blocks[self.current_ap_block])
        print("RESOLVE BLOCK")
        print(self.current_ap_block, "block tokens:", block_tokens)
        local_gerber_parser.parse(block_tokens)
        print(local_gerber_parser)
        print("------------------------------------")
        self.aperture_blocks[self.current_ap_block] = local_gerber_parser
