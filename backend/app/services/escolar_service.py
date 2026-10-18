"""Catálogo de colegios y perfil escolar (colegio, edad y dirección) del estudiante."""

import json
import os
import re

from ..extensions import db
from ..models.escolar import SedeEducativa, PerfilEscolar
from .geo import geocodificador
from .geo.direcciones import municipio_canonico, sin_tildes

RUTA_CATALOGO = os.path.join(os.path.dirname(__file__), '..', 'recursos', 'geo', 'colegios_valle_aburra.json')
CAJA_VALLE = geocodificador.CAJA_VALLE  # oeste, norte, este, sur
EDAD_MIN, EDAD_MAX = 12, 25
# Si el estudiante mueve el pin más que esto, la ubicación pasa a ser manual.
TOLERANCIA_PIN_M = 25


def cargar_catalogo(ruta=RUTA_CATALOGO):
    """Inserta o actualiza las sedes del archivo. Devuelve cuántas quedaron."""
    with open(ruta, encoding='utf-8') as f:
        colegios = json.load(f)['colegios']
    existentes = {s.codigo: s for s in SedeEducativa.query.all()}
    campos = ('codigo_establecimiento', 'nombre', 'sede', 'sector', 'municipio', 'comuna', 'barrio', 'direccion',
              'lat', 'lon', 'matricula_9', 'matricula_10', 'matricula_11', 'fuente', 'ubicacion')
    for c in colegios:
        sede = existentes.get(c['codigo']) or SedeEducativa(codigo=c['codigo'])
        for campo in campos:
            setattr(sede, campo, c.get(campo))
        db.session.add(sede)
    db.session.commit()
    return SedeEducativa.query.count()


def _plano(texto):
    return re.sub(r'[^A-Z0-9 ]', ' ', sin_tildes(texto or '').upper())


def buscar_colegios(consulta, municipio=None, limite=12):
    """Busca por palabras sueltas en el nombre o la sede ("javiera", "ie san jose bello")."""
    palabras = [p for p in _plano(consulta).split() if len(p) >= 2]
    if not palabras:
        return []
    q = SedeEducativa.query
    mpio = municipio_canonico(municipio)
    if mpio:
        q = q.filter(SedeEducativa.municipio == mpio)
    hallados = [s for s in q.all()
                if all(p in _plano(f'{s.nombre} {s.sede} {s.municipio} {s.barrio or ""}') for p in palabras)]
    # Primero los que empiezan por la primera palabra y, dentro de cada colegio, la sede principal.
    hallados.sort(key=lambda s: (not _plano(s.nombre).startswith(palabras[0]), s.sede != s.nombre,
                                 s.nombre, s.sede or ''))
    return [s.to_dict() for s in hallados[:limite]]


def perfil_de(usuario_id):
    return PerfilEscolar.query.filter_by(usuario_id=usuario_id).first()


def _en_valle(lat, lon):
    oeste, norte, este, sur = CAJA_VALLE
    return sur <= lat <= norte and oeste <= lon <= este


def guardar_perfil(usuario_id, datos):
    """Valida y guarda el perfil escolar. Lanza ValueError con un mensaje para el estudiante."""
    perfil = perfil_de(usuario_id) or PerfilEscolar(usuario_id=usuario_id)

    if 'sede_codigo' in datos or 'colegio_texto' in datos:
        codigo = (datos.get('sede_codigo') or '').strip() or None
        texto = (datos.get('colegio_texto') or '').strip()[:200] or None
        if codigo:
            sede = SedeEducativa.query.filter_by(codigo=codigo).first()
            if not sede:
                raise ValueError('El colegio elegido no está en el catálogo.')
            perfil.sede_codigo, perfil.colegio_texto, perfil.sector = codigo, None, sede.sector
        elif texto:
            sector = datos.get('sector')
            if sector not in ('Oficial', 'Privado'):
                raise ValueError('Indica si tu colegio es oficial o privado.')
            perfil.sede_codigo, perfil.colegio_texto, perfil.sector = None, texto, sector

    if 'edad' in datos and datos.get('edad') not in (None, ''):
        try:
            edad = int(datos['edad'])
        except (TypeError, ValueError):
            raise ValueError('La edad debe ser un número.')
        if not EDAD_MIN <= edad <= EDAD_MAX:
            raise ValueError(f'La edad debe estar entre {EDAD_MIN} y {EDAD_MAX} años.')
        perfil.edad = edad

    if 'lat' in datos:
        mpio = municipio_canonico(datos.get('municipio'))
        if not mpio:
            raise ValueError('Elige tu municipio del Valle de Aburrá.')
        try:
            lat, lon = float(datos['lat']), float(datos['lon'])
        except (TypeError, ValueError, KeyError):
            raise ValueError('Ubica tu casa en el mapa.')
        if not _en_valle(lat, lon):
            raise ValueError('El punto del mapa queda por fuera del Valle de Aburrá.')
        direccion = (datos.get('direccion') or '').strip()[:200]
        if not direccion:
            raise ValueError('Escribe tu dirección.')
        # La precisión se recalcula aquí: no se confía en la que manda el navegador.
        ubicada = geocodificador.geocodificar(direccion, mpio, usar_osm=False)
        if ubicada['encontrada'] and geocodificador.distancia_m(lat, lon, ubicada['lat'], ubicada['lon']) <= TOLERANCIA_PIN_M:
            precision = ubicada['precision']
        elif datos.get('precision') == 'osm' and not datos.get('movido'):
            precision = 'osm'
        else:
            precision = 'manual'
        perfil.municipio = mpio
        perfil.direccion = direccion
        perfil.direccion_normalizada = ubicada.get('normalizada')
        perfil.complemento = (datos.get('complemento') or ubicada.get('complemento') or '').strip()[:80] or None
        perfil.lat, perfil.lon, perfil.precision = round(lat, 6), round(lon, 6), precision
        perfil.estrato = geocodificador.estrato_cercano(lat, lon)

    db.session.add(perfil)
    db.session.commit()
    return perfil
