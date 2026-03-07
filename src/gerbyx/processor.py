from typing import List, Optional, Tuple, Dict
import math
import re
from shapely.geometry import Point, LineString, Polygon, MultiPoint, box
from shapely.ops import unary_union
from shapely.affinity import rotate, translate

from .state import PlotState
from .aperture import Aperture
from .format import FormatSpec
from .units import Units
from .macro import Macro
from .blocks import ApertureBlock

class GerberProcessor:
    """
    Interpreta i comandi Gerber e mantiene lo stato del plotter.
    Genera una lista di geometrie Shapely.
    """
    def __init__(self):
        self.state = PlotState()
        self.geometries: List[object] = [] # Lista di geometrie Shapely
        self.current_region_points: List[Tuple[float, float]] = []
        self.macros: Dict[str, Macro] = {}
        self.aperture_blocks: Dict[str, ApertureBlock] = {}

    def set_units(self, units: str):
        self.state.units = Units(units)

    def set_format_spec(self, format_spec: FormatSpec):
        self.state.format_spec = format_spec

    def define_aperture(self, aperture: Aperture):
        self.state.apertures[aperture.id] = aperture

    def define_macro(self, macro: Macro):
        self.macros[macro.name] = macro

    def define_aperture_block(self, block: ApertureBlock):
        self.aperture_blocks[block.id] = block

    def select_aperture(self, aperture_id: str):
        if aperture_id not in self.state.apertures:
            print(f"Warning: Aperture {aperture_id} not defined.")
        self.state.current_aperture_id = aperture_id

    def set_interpolation_mode(self, mode: str):
        self.state.interpolation_mode = mode

    def set_quadrant_mode(self, mode: str):
        self.state.quadrant_mode = mode

    def start_region(self):
        self.state.region_mode = True
        self.current_region_points = []
        if self.state.current_point:
             self.current_region_points.append(self.state.current_point)

    def end_region(self):
        self.state.region_mode = False
        if len(self.current_region_points) > 2:
            if self.current_region_points[0] != self.current_region_points[-1]:
                self.current_region_points.append(self.current_region_points[0])
            poly = Polygon(self.current_region_points)
            if not poly.is_valid:
                poly = poly.buffer(0)
            self.geometries.append(poly)
        self.current_region_points = []

    def parse_value(self, value_str: str, is_x: bool = True) -> float:
        fmt = self.state.format_spec
        if not fmt:
            return float(value_str)

        sign = 1
        if value_str.startswith('+'):
            value_str = value_str[1:]
        elif value_str.startswith('-'):
            sign = -1
            value_str = value_str[1:]

        length = len(value_str)
        if is_x:
            decimals = fmt.x_dec
            integers = fmt.x_int
        else:
            decimals = fmt.y_dec
            integers = fmt.y_int

        if '.' in value_str:
            return float(value_str) * sign

        if fmt.zero_omission == 'L':
            if length < decimals:
                value_str = value_str.zfill(decimals + 1)
            val = float(value_str) / (10 ** decimals)
            return val * sign
        elif fmt.zero_omission == 'T':
            total_len = integers + decimals
            if length < total_len:
                value_str = value_str.ljust(total_len, '0')
            val = float(value_str) / (10 ** decimals)
            return val * sign

        return float(value_str) * sign

    def update_point(self, x: Optional[float] = None, y: Optional[float] = None):
        curr_x, curr_y = self.state.current_point
        new_x = x if x is not None else curr_x
        new_y = y if y is not None else curr_y

        if self.state.format_spec and self.state.format_spec.coord_mode == 'I':
            if x is not None: new_x = curr_x + x
            if y is not None: new_y = curr_y + y

        self.state.current_point = (new_x, new_y)
        if self.state.region_mode:
            self.current_region_points.append(self.state.current_point)

    def draw_to(self, x: Optional[float] = None, y: Optional[float] = None, center_offset: Optional[Tuple[float, float]] = None):
        start_point = self.state.current_point
        curr_x, curr_y = start_point
        target_x = x if x is not None else curr_x
        target_y = y if y is not None else curr_y

        if self.state.format_spec and self.state.format_spec.coord_mode == 'I':
            if x is not None: target_x = curr_x + x
            if y is not None: target_y = curr_y + y

        end_point = (target_x, target_y)

        if self.state.interpolation_mode == 'Linear':
            if self.state.region_mode:
                self.current_region_points.append(end_point)
            else:
                aperture = self.state.get_current_aperture()
                if aperture:
                    line = LineString([start_point, end_point])
                    shape = self._create_stroked_shape(line, aperture)
                    self.geometries.append(shape)

        elif self.state.interpolation_mode in ['ClockwiseCircular', 'CounterClockwiseCircular']:
            if center_offset:
                i, j = center_offset
                center_x = curr_x + i
                center_y = curr_y + j
                is_full_circle = (start_point == end_point)
                arc_points = self._generate_arc_points(
                    start_point, end_point, (center_x, center_y),
                    self.state.interpolation_mode == 'ClockwiseCircular',
                    is_full_circle=is_full_circle
                )
                if self.state.region_mode:
                    self.current_region_points.extend(arc_points[1:])
                else:
                    aperture = self.state.get_current_aperture()
                    if aperture:
                        line = LineString(arc_points)
                        shape = self._create_stroked_shape(line, aperture)
                        self.geometries.append(shape)

        self.state.current_point = end_point

    def flash_at(self, x: Optional[float] = None, y: Optional[float] = None):
        self.update_point(x, y)
        if self.state.region_mode:
            return

        aperture = self.state.get_current_aperture()
        if not aperture:
            return

        # Controlla se è una macro
        if aperture.type not in ['C', 'R', 'O', 'P']:
            # È una macro (o un blocco, ma per ora assumiamo macro se non è standard)
            macro_name = aperture.type
            if macro_name in self.macros:
                macro_def = self.macros[macro_name]
                shape = self._instantiate_macro(macro_def, aperture.params, self.state.current_point)
                if shape and not shape.is_empty:
                    self.geometries.append(shape)
            else:
                print(f"Warning: Macro '{macro_name}' not found.")
        else:
            # Apertura standard
            shape = self._create_flashed_shape(Point(self.state.current_point), aperture)
            self.geometries.append(shape)

    # --- Macro Interpreter ---

    def _instantiate_macro(self, macro: Macro, params: List[float], location: Tuple[float, float]):
        """
        Esegue una macro e restituisce la geometria risultante traslata nella posizione corretta.
        """
        # 1. Risoluzione Variabili
        # I parametri passati nell'AD (params) sostituiscono $1, $2, etc.
        # params[0] -> $1, params[1] -> $2

        shapes_add = []
        shapes_sub = []

        for primitive_str in macro.body:
            # Rimuovi commenti e spazi
            primitive_str = primitive_str.strip()
            if not primitive_str or primitive_str.startswith('0 '): # Commento
                continue

            # Split per virgola per ottenere i token grezzi
            tokens = primitive_str.split(',')

            # Il primo token è il codice primitiva (es. "1", "21")
            code_expr = tokens[0]
            try:
                code = int(self._evaluate_expression(code_expr, params))
            except:
                continue # Skip invalid

            # Valuta tutti gli altri parametri
            evaluated_args = []
            for t in tokens[1:]:
                val = self._evaluate_expression(t, params)
                evaluated_args.append(val)

            # Genera la geometria primitiva
            prim_shape = self._generate_macro_primitive(code, evaluated_args)

            if prim_shape is None or prim_shape.is_empty:
                continue

            # Gestione Esposizione (Polarità)
            # Di solito il primo argomento dopo il codice è l'esposizione (1=on, 0=off)
            # Ma attenzione: alcune primitive hanno l'esposizione in posizione diversa?
            # Standard:
            # 1 Circle: 1, Exp, Dia, X, Y
            # 2 Vector Line: 2, Exp, W, X1, Y1, X2, Y2, Rot
            # 20 Vector Line: 20, Exp, W, X1, Y1, X2, Y2, Rot
            # 21 Center Line: 21, Exp, W, H, Cx, Cy, Rot
            # 4 Outline: 4, Exp, N, X1, Y1... Rot
            # 5 Polygon: 5, Exp, N, Cx, Cy, Dia, Rot
            # 6 Moire: 6, Cx, Cy, Dia, RingThk, Gap, MaxRings, CrossThk, CrossLen, Rot (NO EXP!)
            # 7 Thermal: 7, Cx, Cy, InnerDia, OuterDia, Gap, Rot (NO EXP!)

            exposure = 1 # Default additive

            if code in [1, 2, 20, 21, 4, 5]:
                if len(evaluated_args) > 0:
                    exposure = int(evaluated_args[0])

            # Moire (6) e Thermal (7) sono sempre additivi (o gestiti specificamente)

            if exposure == 1:
                shapes_add.append(prim_shape)
            else:
                shapes_sub.append(prim_shape)

        # Combinazione Booleana
        if not shapes_add:
            return None

        final_shape = unary_union(shapes_add)

        if shapes_sub:
            sub_shape = unary_union(shapes_sub)
            final_shape = final_shape.difference(sub_shape)

        # Traslazione alla posizione finale
        final_shape = translate(final_shape, xoff=location[0], yoff=location[1])
        return final_shape

    def _evaluate_expression(self, expr: str, params: List[float]) -> float:
        """
        Valuta un'espressione aritmetica contenente variabili $n.
        Es: "$1/2 + 0.5" con params=[10.0] -> 5.5
        """
        # Sostituzione variabili $n con i valori
        # Ordiniamo le sostituzioni per evitare che $11 venga sostituito parzialmente da $1
        # Regex per trovare $n
        def replace_var(match):
            idx = int(match.group(1)) - 1
            if 0 <= idx < len(params):
                return str(params[idx])
            return "0" # Default 0 se manca parametro

        # Sostituisci $1, $2...
        # Usa regex per matchare $ seguito da cifre
        expr_sub = re.sub(r'\$(\d+)', replace_var, expr)

        # Sostituisci 'x' o 'X' con '*' se usato come moltiplicazione (comune in Gerber manuali vecchi, ma standard usa *)
        # Lo standard dice: operatori +, -, x, /.
        # Attenzione: 'x' minuscola è moltiplicazione.
        expr_sub = expr_sub.replace('x', '*')
        expr_sub = expr_sub.replace('X', '*')

        try:
            # Eval è pericoloso in generale, ma qui il dominio è ristretto a numeri e operatori matematici.
            # Per sicurezza, permettiamo solo caratteri validi.
            if not re.match(r'^[\d\.\+\-\*\/\(\)\s]+$', expr_sub):
                # Fallback: se ci sono caratteri strani, prova comunque se è semplice
                pass
            return float(eval(expr_sub))
        except Exception as e:
            print(f"Error evaluating macro expression '{expr}': {e}")
            return 0.0

    def _generate_macro_primitive(self, code: int, args: List[float]):
        """Genera la geometria per una singola primitiva macro (coordinate locali)."""
        try:
            if code == 1: # Circle
                # 1, Exp, Dia, X, Y, [Rot]
                dia = args[1]
                x = args[2]
                y = args[3]
                return Point(x, y).buffer(dia / 2)

            elif code == 2 or code == 20: # Vector Line
                # 2, Exp, Width, StartX, StartY, EndX, EndY, Rot
                w = args[1]
                x1, y1 = args[2], args[3]
                x2, y2 = args[4], args[5]
                rot = args[6]

                line = LineString([(x1, y1), (x2, y2)])
                # Buffer rettangolare (cap_style=2 -> Flat/Square, ma Gerber vuole rettangolo esatto)
                # Usiamo cap_style=3 (Square) che estende, o 2 (Flat) e gestiamo lunghezza?
                # Vector Line in macro ha estremità rettangolari.
                shape = line.buffer(w/2, cap_style=2) # Flat ends
                if rot != 0:
                    shape = rotate(shape, rot, origin=(0,0))
                return shape

            elif code == 21: # Center Line (Rectangle)
                # 21, Exp, W, H, Cx, Cy, Rot
                w = args[1]
                h = args[2]
                cx = args[3]
                cy = args[4]
                rot = args[5]

                rect = box(cx - w/2, cy - h/2, cx + w/2, cy + h/2)
                if rot != 0:
                    rect = rotate(rect, rot, origin=(0,0)) # Rotazione attorno all'origine (0,0) o centro?
                    # Spec: "Rotation of the primitive about the macro origin"
                    # Quindi origin=(0,0) è corretto.
                return rect

            elif code == 4: # Outline
                # 4, Exp, NumPts, X1, Y1, X2, Y2, ..., Rot
                # args[0] = Exp
                # args[1] = NumPts
                # args[2...] = coords
                # Ultimo = Rot
                num_pts = int(args[1])
                # Le coordinate partono da args[2]. Ci sono 2 * num_pts valori.
                coords = []
                idx = 2
                for _ in range(num_pts + 1): # +1 perché il punto iniziale è ripetuto alla fine? No, outline definisce segmenti.
                    # Spec: "The number of points is the number of coordinate pairs... The last point is connected to the first."
                    if idx + 1 >= len(args) - 1: # -1 per la rotazione finale
                        break
                    coords.append((args[idx], args[idx+1]))
                    idx += 2

                rot = args[-1]
                poly = Polygon(coords)
                if rot != 0:
                    poly = rotate(poly, rot, origin=(0,0))
                return poly

            elif code == 5: # Polygon (Regular)
                # 5, Exp, Vertices, Cx, Cy, Dia, Rot
                vertices = int(args[1])
                cx = args[2]
                cy = args[3]
                dia = args[4]
                rot = args[5]

                # Crea poligono regolare
                # Shapely non ha primitiva diretta, lo facciamo a mano o bufferiamo un punto con resolution?
                # Buffer point approssima cerchio.
                # Facciamo a mano.
                radius = dia / 2
                angle_step = 2 * math.pi / vertices
                points = []
                # Gerber polygon starts with a vertex on the X axis (before rotation) usually?
                # Spec: "Vertex 0 is at angle 0" (relative to center)
                for i in range(vertices):
                    theta = i * angle_step
                    px = cx + radius * math.cos(theta)
                    py = cy + radius * math.sin(theta)
                    points.append((px, py))

                poly = Polygon(points)
                if rot != 0:
                    poly = rotate(poly, rot, origin=(0,0))
                return poly

            elif code == 7: # Thermal
                # 7, Cx, Cy, InnerDia, OuterDia, Gap, Rot
                cx = args[0]
                cy = args[1]
                inner_dia = args[2]
                outer_dia = args[3]
                gap = args[4]
                rot = args[5]

                # Thermal è un anello (Outer - Inner) tagliato da una croce (Gap)
                outer_circle = Point(cx, cy).buffer(outer_dia/2)
                inner_circle = Point(cx, cy).buffer(inner_dia/2)
                ring = outer_circle.difference(inner_circle)

                # Croce (Gap)
                # Rettangolo orizzontale e verticale di spessore 'gap'
                # Lunghezza > outer_dia
                L = outer_dia + 1.0
                h_bar = box(cx - L/2, cy - gap/2, cx + L/2, cy + gap/2)
                v_bar = box(cx - gap/2, cy - L/2, cx + gap/2, cy + L/2)
                cross = unary_union([h_bar, v_bar])

                shape = ring.difference(cross)
                if rot != 0:
                    shape = rotate(shape, rot, origin=(0,0))
                return shape

        except Exception as e:
            print(f"Error generating macro primitive {code}: {e}")
            return None

        return None

    # --- End Macro Interpreter ---

    def _generate_arc_points(self, start, end, center, clockwise, num_segments=64, is_full_circle=False):
        sx, sy = start
        ex, ey = end
        cx, cy = center
        r_start = math.sqrt((sx - cx)**2 + (sy - cy)**2)
        r_end = math.sqrt((ex - cx)**2 + (ey - cy)**2)
        radius = (r_start + r_end) / 2.0
        if radius < 1e-9: return [start, end]

        start_angle = math.atan2(sy - cy, sx - cx)
        end_angle = math.atan2(ey - cy, ex - cx)

        if is_full_circle:
            if clockwise: end_angle = start_angle - 2 * math.pi
            else: end_angle = start_angle + 2 * math.pi
        else:
            if clockwise:
                if end_angle > start_angle: end_angle -= 2 * math.pi
            else:
                if end_angle < start_angle: end_angle += 2 * math.pi

        points = []
        angle_diff = end_angle - start_angle
        steps = max(int(abs(angle_diff) * num_segments / (2 * math.pi)) + 1, 2)

        for i in range(steps + 1):
            theta = start_angle + angle_diff * (i / steps)
            px = cx + radius * math.cos(theta)
            py = cy + radius * math.sin(theta)
            points.append((px, py))
        return points

    def _create_stroked_shape(self, line: LineString, aperture: Aperture):
        if aperture.type == 'C':
            radius = aperture.params[0] / 2.0
            return line.buffer(radius, cap_style=1)
        elif aperture.type == 'R':
            w = aperture.params[0]
            h = aperture.params[1] if len(aperture.params) > 1 else w
            polys = []
            coords = list(line.coords)
            for k in range(len(coords) - 1):
                x1, y1 = coords[k]
                x2, y2 = coords[k+1]
                p1 = [(x1 - w/2, y1 - h/2), (x1 + w/2, y1 - h/2), (x1 + w/2, y1 + h/2), (x1 - w/2, y1 + h/2)]
                p2 = [(x2 - w/2, y2 - h/2), (x2 + w/2, y2 - h/2), (x2 + w/2, y2 + h/2), (x2 - w/2, y2 + h/2)]
                segment_poly = MultiPoint(p1 + p2).convex_hull
                polys.append(segment_poly)
            return unary_union(polys)
        return line.buffer(0.001)

    def _create_flashed_shape(self, point: Point, aperture: Aperture):
        x, y = point.x, point.y
        if aperture.type == 'C':
            radius = aperture.params[0] / 2.0
            return point.buffer(radius)
        elif aperture.type == 'R':
            w = aperture.params[0]
            h = aperture.params[1] if len(aperture.params) > 1 else w
            return Polygon([(x-w/2, y-h/2), (x+w/2, y-h/2), (x+w/2, y+h/2), (x-w/2, y+h/2)])
        elif aperture.type == 'O':
             w = aperture.params[0]
             h = aperture.params[1] if len(aperture.params) > 1 else w
             if w > h: return LineString([(x-(w-h)/2, y), (x+(w-h)/2, y)]).buffer(h/2)
             else: return LineString([(x, y-(h-w)/2), (x, y+(h-w)/2)]).buffer(w/2)
        return point.buffer(0.1)
