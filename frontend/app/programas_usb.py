"""Pregrados de la USB Medellín y su afinidad con el perfil RIASEC del estudiante.

Única fuente para la página de resultados y el mapa vocacional: los dos usan la
misma lista y la misma fórmula, así nunca recomiendan programas distintos.
El perfil RIASEC de cada programa (0-10) es una estimación del equipo.
"""

import math

URL_BASE = 'https://usbmed.edu.co/programas/pregrados/'
CLAVES = ('R', 'I', 'A', 'S', 'E', 'C')
AREA_DE_CLAVE = {
    'R': 'Realista', 'I': 'Investigador', 'A': 'Artístico',
    'S': 'Social', 'E': 'Emprendedor', 'C': 'Convencional',
}

# n: nombre, f: facultad, s: perfil RIASEC estimado, u: ruta en usbmed.edu.co, d: descripción
PROGRAMAS = [
    {'n': 'Licenciatura en Educación Física y Deporte', 'f': 'Educación', 's': {'R': 8, 'I': 3, 'A': 3, 'S': 8, 'E': 5, 'C': 3}, 'u': 'licenciatura-en-educacion-fisica-y-deporte', 'd': 'Formación de docentes y gestores del deporte, la educación física y la promoción de la salud.'},
    {'n': 'Tecnología en Entrenamiento Deportivo', 'f': 'Educación', 's': {'R': 9, 'I': 4, 'A': 2, 'S': 6, 'E': 5, 'C': 4}, 'u': 'tecnologia-en-entrenamiento-deportivo', 'd': 'Diseño, aplicación y evaluación de planes de entrenamiento deportivo.'},
    {'n': 'Licenciatura en Educación Infantil', 'f': 'Educación', 's': {'R': 2, 'I': 4, 'A': 7, 'S': 9, 'E': 3, 'C': 4}, 'u': 'licenciatura-en-educacion-infantil', 'd': 'Acompañamiento del desarrollo integral de niñas y niños en la primera infancia.'},
    {'n': 'Administración de Negocios', 'f': 'Ciencias Empresariales', 's': {'R': 2, 'I': 4, 'A': 3, 'S': 5, 'E': 9, 'C': 7}, 'u': 'administracion-de-negocios', 'd': 'Dirección y transformación de organizaciones, con enfoque en emprendimiento e innovación.'},
    {'n': 'Contaduría Pública', 'f': 'Ciencias Empresariales', 's': {'R': 1, 'I': 5, 'A': 1, 'S': 3, 'E': 5, 'C': 10}, 'u': 'contaduria-publica', 'd': 'Gestión de la información financiera y contable de las organizaciones.'},
    {'n': 'Negocios Internacionales', 'f': 'Ciencias Empresariales', 's': {'R': 2, 'I': 4, 'A': 3, 'S': 6, 'E': 9, 'C': 6}, 'u': 'negocios-internacionales', 'd': 'Internacionalización de empresas y búsqueda de oportunidades en mercados globales.'},
    {'n': 'Arquitectura', 'f': 'Artes Integradas', 's': {'R': 6, 'I': 6, 'A': 9, 'S': 3, 'E': 4, 'C': 5}, 'u': 'arquitectura', 'd': 'Diseño y gestión de proyectos arquitectónicos y del espacio habitable.'},
    {'n': 'Diseño de Modas', 'f': 'Artes Integradas', 's': {'R': 5, 'I': 3, 'A': 10, 'S': 4, 'E': 6, 'C': 3}, 'u': 'diseno-de-modas', 'd': 'Ideación, diseño y producción de colecciones y líneas de ropa.'},
    {'n': 'Diseño Industrial', 'f': 'Artes Integradas', 's': {'R': 8, 'I': 6, 'A': 8, 'S': 3, 'E': 4, 'C': 4}, 'u': 'diseno-industrial', 'd': 'Creación de productos que mejoran el entorno y el bienestar de las personas.'},
    {'n': 'Creación de Contenidos Digitales', 'f': 'Ingenierías', 's': {'R': 3, 'I': 4, 'A': 9, 'S': 6, 'E': 7, 'C': 3}, 'u': 'creacion-de-contenidos-digitales', 'd': 'Producción de contenido digital para redes, marcas y medios.'},
    {'n': 'Ingeniería Ambiental', 'f': 'Ingenierías', 's': {'R': 8, 'I': 8, 'A': 2, 'S': 5, 'E': 3, 'C': 5}, 'u': 'ingenieria-ambiental', 'd': 'Soluciones técnicas para el desarrollo sostenible y el cuidado del ambiente.'},
    {'n': 'Ingeniería de Datos y Software', 'f': 'Ingenierías', 's': {'R': 4, 'I': 9, 'A': 3, 'S': 2, 'E': 4, 'C': 8}, 'u': 'ingenieria-de-datos-y-software', 'd': 'Desarrollo de software y gestión de datos para la industria.'},
    {'n': 'Ingeniería de Sistemas Cibernéticos', 'f': 'Ingenierías', 's': {'R': 7, 'I': 9, 'A': 4, 'S': 2, 'E': 4, 'C': 6}, 'u': 'ingenieria-de-sistemas-ciberneticos', 'd': 'Inteligencia artificial, robótica e internet de las cosas.'},
    {'n': 'Ingeniería de Sonido', 'f': 'Ingenierías', 's': {'R': 7, 'I': 7, 'A': 8, 'S': 3, 'E': 3, 'C': 4}, 'u': 'ingenieria-de-sonido', 'd': 'Acústica, producción musical y sonido para medios audiovisuales.'},
    {'n': 'Ingeniería Industrial', 'f': 'Ingenierías', 's': {'R': 6, 'I': 6, 'A': 2, 'S': 4, 'E': 7, 'C': 8}, 'u': 'ingenieria-industrial', 'd': 'Mejora de procesos, producción, logística y gestión del talento.'},
    {'n': 'Ingeniería Multimedia', 'f': 'Ingenierías', 's': {'R': 5, 'I': 6, 'A': 9, 'S': 3, 'E': 5, 'C': 4}, 'u': 'ingenieria-multimedia', 'd': 'Animación, videojuegos, realidad virtual y aumentada, y medios audiovisuales.'},
    {'n': 'Derecho', 'f': 'Derecho', 's': {'R': 1, 'I': 5, 'A': 3, 'S': 7, 'E': 9, 'C': 6}, 'u': 'derecho', 'd': 'Formación de abogados con énfasis en la justicia social.'},
    {'n': 'Psicología', 'f': 'Psicología', 's': {'R': 1, 'I': 8, 'A': 5, 'S': 10, 'E': 4, 'C': 4}, 'u': 'psicologia', 'd': 'Comprensión del comportamiento humano y acompañamiento a personas y grupos.'},
]

# Margen (en puntos de porcentaje) para decir que dos campos están "cerca".
MARGEN_DEFINICION = 10

# Recomendaciones del backend que solo repiten lo que la página ya muestra en
# otros capítulos (perfil, programas, ambiente). La del orientador pasa a "Qué sigue".
_PREFIJOS_REPETIDOS = (
    'Tu perfil vocacional Holland es',
    'Programas de pregrado de la USB',
    'Tu perfil secundario es',
    'Ambientes de trabajo ideales',
    'Se recomienda hablar con el orientador',
)


def _redondear(x):
    """Redondeo como Math.round de JavaScript (.5 hacia arriba), para que la
    página y el mapa muestren exactamente el mismo porcentaje."""
    return int(math.floor(x + 0.5))


def _vector(puntajes):
    return [float((puntajes.get(AREA_DE_CLAVE[k]) or {}).get('normalizado') or 0) for k in CLAVES]


def afinidad(vector_estudiante, perfil_programa):
    """Correlación entre la forma del perfil del estudiante y la del programa,
    llevada a 0-100: compara qué campos destacan más que otros (la lógica de
    Holland), no el nivel absoluto. Un perfil plano no tiene forma: vale 50."""
    a = list(vector_estudiante)
    b = [perfil_programa[k] for k in CLAVES]
    ma, mb = sum(a) / 6, sum(b) / 6
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = sum((x - ma) ** 2 for x in a)
    db = sum((y - mb) ** 2 for y in b)
    if not da or not db:
        return 50
    return _redondear((num / math.sqrt(da * db) + 1) / 2 * 100)


def programas_con_afinidad(puntajes):
    """Los 18 programas en su orden original, cada uno con 'af' y 'url'."""
    v = _vector(puntajes)
    return [dict(p, af=afinidad(v, p['s']), url=URL_BASE + p['u']) for p in PROGRAMAS]


def programas_por_afinidad(puntajes):
    """Los 18 programas de mayor a menor afinidad (empates: orden original)."""
    return sorted(programas_con_afinidad(puntajes), key=lambda p: -p['af'])


def definicion_perfil(puntajes, margen=MARGEN_DEFINICION):
    """'marcado' si uno o dos campos se separan del resto; 'equilibrado' si tres
    o más quedan a menos de `margen` puntos del primero. None sin puntajes."""
    valores = sorted(
        ((float((d or {}).get('normalizado') or 0), area) for area, d in puntajes.items()),
        key=lambda x: -x[0],
    )
    if len(valores) < 3:
        return None
    tope = valores[0][0]
    cercanas = [area for v, area in valores if tope - v < margen]
    tipo = 'equilibrado' if len(cercanas) >= 3 else 'marcado'
    return {'tipo': tipo, 'areas': cercanas}


def sesiones_distintas(historial):
    """Número de días distintos con pruebas completadas. Las pruebas de Intereses
    y Competencias de un mismo día son una sola sesión, no dos momentos."""
    return len({h.get('fecha') for h in historial or [] if h.get('fecha')})


def recomendaciones_accionables(texto, descripcion=''):
    """Líneas de recomendación que no repiten lo que ya muestran otros capítulos."""
    lineas = [l.strip() for l in (texto or '').splitlines() if l.strip()]
    return [
        l for l in lineas
        if l != (descripcion or '').strip() and not l.startswith(_PREFIJOS_REPETIDOS)
    ]
