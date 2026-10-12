"""Dibujos del informe PDF: cuadros de puntaje (Competencias) y luz (Intereses)."""

from reportlab.lib import colors
from reportlab.platypus import Flowable

# La misma paleta por área de la página de resultados.
COLOR_AREA = {
    'Realista': '#eb6834', 'Investigador': '#2a78d6', 'Artístico': '#e87ba4',
    'Social': '#1baf7a', 'Emprendedor': '#eda100', 'Convencional': '#4a3aa7',
}
GRIS_AREA = '#9a9fa9'
GRIS_VACIO = '#d0cdd6'


def color_area(area):
    return colors.HexColor(COLOR_AREA.get(area, GRIS_AREA))


class Cuadros(Flowable):
    """Fila de `maximo` cuadros; se rellenan tantos como puntos valió la respuesta."""

    LADO = 9
    SEP = 3

    def __init__(self, valor, maximo, area):
        super().__init__()
        self.maximo = maximo
        self.valor = max(0, min(int(valor), maximo))
        self.color = color_area(area)
        self.width = maximo * self.LADO + (maximo - 1) * self.SEP
        self.height = self.LADO

    def wrap(self, *args):
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setLineWidth(0.8)
        for i in range(self.maximo):
            x = i * (self.LADO + self.SEP)
            if i < self.valor:
                c.setFillColor(self.color)
                c.setStrokeColor(self.color)
                c.roundRect(x, 0, self.LADO, self.LADO, 1.5, stroke=1, fill=1)
            else:
                c.setStrokeColor(colors.HexColor(GRIS_VACIO))
                c.roundRect(x, 0, self.LADO, self.LADO, 1.5, stroke=1, fill=0)


class Luz(Flowable):
    """Luz minimalista: encendida (con halo suave) o apagada (solo el contorno)."""

    RADIO = 4.5

    def __init__(self, encendida, area):
        super().__init__()
        self.encendida = bool(encendida)
        self.color = color_area(area)
        self.width = self.height = self.RADIO * 2 + 5

    def wrap(self, *args):
        return self.width, self.height

    def draw(self):
        c = self.canv
        cx = cy = self.width / 2
        c.saveState()
        if self.encendida:
            c.setFillColor(self.color)
            c.setFillAlpha(0.22)
            c.circle(cx, cy, self.RADIO + 2.2, stroke=0, fill=1)
            c.setFillAlpha(1)
            c.circle(cx, cy, self.RADIO, stroke=0, fill=1)
        else:
            c.setStrokeColor(colors.HexColor(GRIS_VACIO))
            c.setLineWidth(0.9)
            c.circle(cx, cy, self.RADIO, stroke=1, fill=0)
        c.restoreState()
