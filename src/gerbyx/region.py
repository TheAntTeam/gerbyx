from shapely.geometry import LineString, Polygon


from shapely.geometry import LineString, Polygon

class RegionBuilder:
    def __init__(self, polarity="D"):
        self.points = []
        self.open = False
        self.polarity = polarity

    def start(self, pt):
        """Inizia una nuova regione con il primo punto."""
        self.points = [pt]
        self.open = True

    def add_point(self, pt):
        """Aggiunge un punto alla regione se è aperta."""
        if not self.open:
            #print("Warning: add_point called on closed region")
            return
        self.points.append(pt)

    def close_polygon(self):
        """Chiude la regione e restituisce un poligono Shapely."""
        if len(self.points) < 3:
            #print("Warning: region closed with insufficient points")
            self.open = False
            self.points = []
            return Polygon()  # poligono vuoto

        ring = LineString(self.points)

        # forza validità
        if not ring.is_valid:
            ring = ring.buffer(0)

        poly = Polygon(ring)
        self.open = False
        self.points = []
        return poly
