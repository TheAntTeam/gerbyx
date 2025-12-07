from shapely.geometry import Point, LineString, Polygon, GeometryCollection


class GerberGeometryBuilder:
    def __init__(self, parser):
        """
        parser: istanza di GerberParser già eseguita su un file Gerber
        """
        self.parser = parser
        self.shapely_geometries = []

    def build(self):
        """
        Costruisce la lista di geometrie Shapely a partire dalle entità del parser.
        """
        for geom in self.parser.geometries:
            shapely_obj = self._to_shapely(geom)
            if shapely_obj:
                self.shapely_geometries.append(shapely_obj)
        return self.shapely_geometries

    def _to_shapely(self, geom):
        """
        Converte una singola entità del parser in un oggetto Shapely.
        geom: dict o dataclass con tipo e parametri
        """
        gtype = geom["type"]

        if gtype == "flash":
            return self._flash_to_geometry(geom)
        elif gtype == "draw":
            return self._draw_to_geometry(geom)
        elif gtype == "region":
            return self._region_to_geometry(geom)
        elif gtype == "block":
            return self._block_to_geometry(geom)
        else:
            return None

    def _flash_to_geometry(self, geom):
        x, y = geom["x"], geom["y"]
        aperture = geom["aperture"]
        if aperture.shape == "C":
            r = aperture.diameter / 2
            return Point(x, y).buffer(r)
        elif aperture.shape == "R":
            w, h = aperture.width, aperture.height
            return Polygon([
                (x - w/2, y - h/2),
                (x + w/2, y - h/2),
                (x + w/2, y + h/2),
                (x - w/2, y + h/2)
            ])
        return Point(x, y)

    def _draw_to_geometry(self, geom):
        x1, y1 = geom["x1"], geom["y1"]
        x2, y2 = geom["x2"], geom["y2"]
        aperture = geom["aperture"]
        line = LineString([(x1, y1), (x2, y2)])
        if aperture.shape == "C":
            r = aperture.diameter / 2
            return line.buffer(r, cap_style=2)
        return line

    def _region_to_geometry(self, geom):
        points = geom["points"]
        return Polygon(points)

    def _block_to_geometry(self, geom):
        block_id = geom["block_id"]
        block_parser = self.parser.resolved_blocks[block_id]
        return GeometryCollection(block_parser.geometries)
