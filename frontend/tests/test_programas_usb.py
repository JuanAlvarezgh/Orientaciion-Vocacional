"""Pruebas del módulo compartido de programas USB (lógica pura, sin servidor)."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.programas_usb import (
    PROGRAMAS, afinidad, programas_con_afinidad, programas_por_afinidad,
    definicion_perfil, sesiones_distintas, recomendaciones_accionables,
)


def _puntajes(**valores):
    nombres = {'R': 'Realista', 'I': 'Investigador', 'A': 'Artístico',
               'S': 'Social', 'E': 'Emprendedor', 'C': 'Convencional'}
    return {nombres[k]: {'normalizado': v} for k, v in valores.items()}


def test_hay_18_programas_con_perfil_completo():
    assert len(PROGRAMAS) == 18
    for p in PROGRAMAS:
        assert set(p['s']) == {'R', 'I', 'A', 'S', 'E', 'C'}


def test_afinidad_es_100_con_la_misma_forma_y_0_con_la_opuesta():
    programa = {'R': 9, 'I': 1, 'A': 1, 'S': 1, 'E': 1, 'C': 1}
    assert afinidad([90, 10, 10, 10, 10, 10], programa) == 100
    assert afinidad([10, 90, 90, 90, 90, 90], programa) == 0


def test_afinidad_de_perfil_plano_es_50():
    assert afinidad([50] * 6, {'R': 9, 'I': 1, 'A': 1, 'S': 1, 'E': 1, 'C': 1}) == 50


def test_afinidad_redondea_como_javascript():
    # Math.round(68.5) = 69 en JS; round(68.5) = 68 en Python. Se usa el de JS.
    from app.programas_usb import _redondear
    assert _redondear(68.5) == 69


def test_programas_por_afinidad_ordena_de_mayor_a_menor_y_trae_url():
    lista = programas_por_afinidad(_puntajes(R=10, I=20, A=95, S=30, E=40, C=10))
    assert [p['af'] for p in lista] == sorted((p['af'] for p in lista), reverse=True)
    assert lista[0]['url'].startswith('https://usbmed.edu.co/programas/pregrados/')
    assert lista[0]['n'] in ('Diseño de Modas', 'Arquitectura', 'Ingeniería Multimedia',
                             'Creación de Contenidos Digitales')


def test_programas_con_afinidad_conserva_el_orden_original():
    lista = programas_con_afinidad(_puntajes(R=50, I=50, A=50, S=50, E=50, C=60))
    assert [p['n'] for p in lista] == [p['n'] for p in PROGRAMAS]


def test_perfil_marcado_con_un_campo_lejos_del_resto():
    d = definicion_perfil(_puntajes(E=100, C=87.5, S=37.5, I=37.5, A=29.2, R=12.5))
    assert d == {'tipo': 'marcado', 'areas': ['Emprendedor']}


def test_perfil_marcado_en_dos_campos():
    d = definicion_perfil(_puntajes(R=80, I=75, A=40, S=30, E=20, C=10))
    assert d == {'tipo': 'marcado', 'areas': ['Realista', 'Investigador']}


def test_perfil_equilibrado_con_tres_o_mas_campos_cerca():
    d = definicion_perfil(_puntajes(R=63.2, I=51.9, A=63.4, S=60.0, E=43.3, C=63.2))
    assert d['tipo'] == 'equilibrado'
    assert d['areas'][0] == 'Artístico'
    assert set(d['areas']) == {'Artístico', 'Realista', 'Convencional', 'Social'}


def test_definicion_sin_puntajes_es_none():
    assert definicion_perfil({}) is None


def test_sesiones_distintas_cuenta_fechas_no_aplicaciones():
    historial = [{'fecha': '2026-09-23'}, {'fecha': '2026-09-23'}, {'fecha': None}]
    assert sesiones_distintas(historial) == 1
    historial.append({'fecha': '2027-03-01'})
    assert sesiones_distintas(historial) == 2


def test_recomendaciones_quita_las_repetidas_y_deja_las_accionables():
    descripcion = 'Tienes una fuerte inclinación hacia actividades prácticas.'
    texto = '\n'.join([
        'Tu perfil vocacional Holland es: Realista (Código RIASEC: RCI).',
        descripcion,
        'Programas de pregrado de la USB afines a tu perfil: Ingeniería Industrial.',
        'Tu perfil secundario es Convencional. En la USB también podrías explorar: Contaduría.',
        'Ambientes de trabajo ideales: Talleres.',
        'Se recomienda hablar con el orientador escolar o consejero de tu institución.',
        'Aún no has completado la prueba de Intereses; tu perfil integrado se actualizará cuando la realices.',
    ])
    assert recomendaciones_accionables(texto, descripcion) == [
        'Aún no has completado la prueba de Intereses; tu perfil integrado se actualizará cuando la realices.',
    ]
