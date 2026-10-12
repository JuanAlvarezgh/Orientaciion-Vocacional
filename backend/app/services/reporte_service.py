"""Servicio de generación de reportes PDF."""

import os
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether,
)

from ..extensions import db
from ..models.resultado import PerfilVocacional, Reporte
from .psicometrico_service import PsicometricoService
from .reporte_graficos import COLOR_AREA, Cuadros, Luz
from .reporte_respuestas import filas_de_aplicacion

AREAS = ['Realista', 'Investigador', 'Artístico', 'Social', 'Emprendedor', 'Convencional']
MASCOTA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'recursos', 'mascota')
MASCOTA_POR_PERFIL = {
    'Realista': 'realista', 'Investigador': 'investigador', 'Artístico': 'artistico',
    'Social': 'social', 'Emprendedor': 'emprendedor', 'Convencional': 'convencional',
}
TINTA = colors.HexColor('#1c1b22')
GRIS = colors.HexColor('#6f6b80')
LINEA = colors.HexColor('#ece8e1')
ACENTO = colors.HexColor('#a35200')
# Márgenes de 0.8 in y el relleno de 6 pt a cada lado que deja el marco de reportlab.
ANCHO_UTIL = letter[0] - 1.6 * inch - 12


def ruta_mascota(perfil_principal):
    """Zorro del perfil principal; el de por defecto si el perfil no tiene uno."""
    ruta = os.path.join(MASCOTA_DIR, MASCOTA_POR_PERFIL.get(perfil_principal, 'default') + '.png')
    return ruta if os.path.exists(ruta) else os.path.join(MASCOTA_DIR, 'default.png')


class ReporteService:
    """Servicio para generación de reportes PDF."""

    REPORTES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'reportes')

    @staticmethod
    def _estilos():
        base = getSampleStyleSheet()['Normal']

        def estilo(nombre, **kw):
            opciones = dict(fontName='Helvetica', fontSize=9, leading=12, textColor=TINTA)
            opciones.update(kw)
            return ParagraphStyle(nombre, parent=base, **opciones)

        return {
            'eyebrow': estilo('Eyebrow', fontSize=8, leading=10, textColor=ACENTO),
            'nombre': estilo('Nombre', fontName='Helvetica-Bold', fontSize=17, leading=21, spaceAfter=6),
            'etiqueta': estilo('Etiqueta', textColor=GRIS),
            'dato': estilo('Dato'),
            'h2': estilo('H2', fontName='Helvetica-Bold', fontSize=12, leading=15, spaceBefore=6, spaceAfter=2),
            'ayuda': estilo('Ayuda', fontSize=7.8, leading=10, textColor=GRIS, spaceAfter=5),
            'num': estilo('Num', fontSize=8, textColor=GRIS),
            'fila': estilo('Fila', fontSize=8.5, leading=10.5),
            'letra': estilo('Letra', fontName='Helvetica-Bold', alignment=TA_CENTER),
            'subtotal': estilo('Subtotal', fontSize=7.8, leading=10, alignment=TA_CENTER),
            'perfil': estilo('Perfil', fontName='Helvetica-Bold', fontSize=16, leading=20),
            'texto': estilo('Texto', fontSize=9.5, leading=13.5, spaceBefore=4),
            'pie': estilo('Pie', fontSize=7.5, leading=10, textColor=GRIS),
        }

    @staticmethod
    def _encabezado(usuario, aplicacion, perfil, dj, st):
        """Datos del estudiante a la izquierda y su zorro a la derecha."""
        fecha = aplicacion.fecha_fin or aplicacion.fecha_inicio
        filas = [
            ('Documento', f'{usuario.tipo_documento or ""} {usuario.documento or "N/A"}'.strip()),
            ('Institución', usuario.grado.nombre if usuario.grado else 'No especificada'),
            ('Grado', f'{usuario.semestre}°' if usuario.semestre else 'N/A'),
            ('Fecha', fecha.strftime('%d/%m/%Y') if fecha else 'N/A'),
            ('Código RIASEC', dj.get('codigo_riasec') or '—'),
        ]
        datos = Table(
            [[Paragraph(etq, st['etiqueta']), Paragraph(escape(str(val)), st['dato'])] for etq, val in filas],
            colWidths=[1.15 * inch, 3.2 * inch],
        )
        datos.setStyle(TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 1.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
        ]))
        izquierda = [
            Paragraph('Informe de orientación vocacional', st['eyebrow']),
            Paragraph(escape(f'{usuario.nombres} {usuario.apellidos}'), st['nombre']),
            datos,
        ]
        zorro = Image(ruta_mascota(perfil.perfil_principal), width=1.75 * inch, height=1.75 * inch,
                      kind='proportional')
        cabecera = Table([[izquierda, zorro]], colWidths=[ANCHO_UTIL - 1.9 * inch, 1.9 * inch])
        cabecera.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('LINEBELOW', (0, 0), (-1, 0), 0.8, LINEA),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        return cabecera

    @staticmethod
    def _subtotales(puntajes, es_interes, st):
        """Puntos por campo en la prueba, por ejemplo 'Realista 13 de 25'."""
        clave_p, clave_m = ('interes_puntaje', 'interes_maximo') if es_interes else ('competencia_puntaje', 'competencia_maximo')
        celdas = []
        for area in AREAS:
            d = puntajes.get(area) or {}
            maximo = d.get(clave_m) or 0
            if not maximo:
                continue
            celdas.append(Paragraph(
                f'<font color="{COLOR_AREA[area]}"><b>{area}</b></font><br/>{d.get(clave_p, 0)} de {maximo}',
                st['subtotal']))
        if not celdas:
            return Spacer(1, 0)
        tabla = Table([celdas], colWidths=[ANCHO_UTIL / len(celdas)] * len(celdas))
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f6f2')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        return tabla

    @staticmethod
    def _seccion_respuestas(prueba, es_interes, puntajes, st):
        """Una fila por pregunta: número, enunciado, letra y su valor dibujado."""
        if es_interes:
            titulo = 'Prueba de intereses'
            ayuda = ('Luz encendida: elegiste la opción A y el punto fue para el campo de la pregunta. '
                     'Apagada: elegiste la B y el punto fue para el otro campo.')
        else:
            titulo = 'Prueba de competencias'
            ayuda = 'Cuadros sombreados: los puntos que valió tu respuesta, de 1 a 4.'

        datos = []
        for f in filas_de_aplicacion(prueba):
            dibujo = Luz(f['valor'], f['area']) if f['tipo'] == 'luz' else Cuadros(f['valor'], f['maximo'], f['area'])
            datos.append([
                Paragraph(f"{f['numero']}.", st['num']),
                Paragraph(escape(f['enunciado']), st['fila']),
                Paragraph(f['letra'], st['letra']),
                dibujo,
            ])
        elementos = [Paragraph(titulo, st['h2']), Paragraph(ayuda, st['ayuda'])]
        if datos:
            tabla = Table(datos, colWidths=[0.35 * inch, ANCHO_UTIL - 2.05 * inch, 0.35 * inch, 1.35 * inch])
            tabla.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 2.5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
                ('LEFTPADDING', (0, 0), (-1, -1), 2),
                ('LINEBELOW', (0, 0), (-1, -1), 0.4, LINEA),
            ]))
            elementos.append(tabla)
        elementos += [Spacer(1, 6), ReporteService._subtotales(puntajes, es_interes, st), Spacer(1, 14)]
        return elementos

    @staticmethod
    def _cierre(perfil, dj, st):
        """Perfil vocacional al final del informe."""
        partes = [Paragraph('Perfil vocacional', st['eyebrow']),
                  Paragraph(escape(perfil.perfil_principal or 'Sin determinar'), st['perfil'])]
        detalle = []
        if perfil.perfil_secundario:
            detalle.append(f'Perfil secundario: {escape(perfil.perfil_secundario)}')
        if dj.get('codigo_riasec'):
            detalle.append(f'Código RIASEC {escape(dj["codigo_riasec"])}')
        if detalle:
            partes.append(Paragraph(' · '.join(detalle), st['ayuda']))
        if perfil.descripcion:
            partes.append(Paragraph(escape(perfil.descripcion), st['texto']))
        if dj.get('ambiente_trabajo'):
            partes.append(Paragraph('<b>Ambiente de trabajo ideal:</b> ' + escape(dj['ambiente_trabajo']), st['texto']))
        partes += [Spacer(1, 12), Paragraph(
            'Este informe es una herramienta de orientación y no un diagnóstico definitivo. '
            'Se recomienda revisarlo con el orientador de tu colegio o con Bienestar de la USB.', st['pie'])]
        return KeepTogether(partes)

    @staticmethod
    def generar_reporte_individual(perfil_id: int, generado_por: int = None) -> Reporte:
        """Informe del estudiante: datos y zorro, cada respuesta con lo que valió y el perfil."""
        perfil = PerfilVocacional.query.get_or_404(perfil_id)
        aplicacion = perfil.aplicacion
        usuario = aplicacion.usuario
        dj = perfil.datos_json or {}
        puntajes = dj.get('puntajes_por_area', {})

        os.makedirs(ReporteService.REPORTES_DIR, exist_ok=True)
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f'reporte_{usuario.documento or usuario.id}_{timestamp}.pdf'
        filepath = os.path.join(ReporteService.REPORTES_DIR, filename)

        nombre = f'{usuario.nombres} {usuario.apellidos}'
        doc = SimpleDocTemplate(filepath, pagesize=letter,
                                topMargin=0.7 * inch, bottomMargin=0.8 * inch,
                                leftMargin=0.8 * inch, rightMargin=0.8 * inch,
                                title=f'Informe vocacional - {nombre}')
        st = ReporteService._estilos()

        elements = [ReporteService._encabezado(usuario, aplicacion, perfil, dj, st), Spacer(1, 12)]

        # Las dos pruebas de la sesión: la de esta aplicación y su complementaria.
        # Intereses va primero, como en el cuestionario.
        def nombre_dimension(a):
            d = a.configuracion.instrumento.dimensiones.first()
            return d.nombre if d else ''

        complementaria = PsicometricoService._obtener_aplicacion_complementaria(aplicacion)
        pruebas = [a for a in (aplicacion, complementaria) if a]
        pruebas.sort(key=lambda a: 0 if PsicometricoService._es_interes(nombre_dimension(a)) else 1)
        for prueba in pruebas:
            es_interes = PsicometricoService._es_interes(nombre_dimension(prueba))
            elements += ReporteService._seccion_respuestas(prueba, es_interes, puntajes, st)

        elements.append(ReporteService._cierre(perfil, dj, st))

        def pie_de_pagina(canvas, doc_):
            canvas.saveState()
            canvas.setFont('Helvetica', 7.5)
            canvas.setFillColor(GRIS)
            canvas.drawString(doc_.leftMargin, 0.45 * inch,
                              f'{nombre} · Informe de orientación vocacional · Universidad de San Buenaventura Medellín')
            canvas.drawRightString(letter[0] - doc_.rightMargin, 0.45 * inch, f'Página {doc_.page}')
            canvas.restoreState()

        doc.build(elements, onFirstPage=pie_de_pagina, onLaterPages=pie_de_pagina)

        reporte = Reporte(
            perfil_id=perfil_id,
            tipo='individual',
            ruta_archivo=filepath,
            formato='pdf',
            generado_por=generado_por,
        )
        db.session.add(reporte)
        db.session.commit()

        return reporte
