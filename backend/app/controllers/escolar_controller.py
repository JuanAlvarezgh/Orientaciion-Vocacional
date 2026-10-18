"""Controlador escolar: buscador de colegios, geocodificador y perfil escolar del estudiante."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..services import escolar_service
from ..services.geo import geocodificador
from ..services.geo.direcciones import MUNICIPIOS
from ..utils.rate_limit import allow_request

escolar_bp = Blueprint('escolar', __name__)


@escolar_bp.route('/municipios', methods=['GET'])
def municipios():
    """Los diez municipios del Valle de Aburrá (público: lo usa el registro)."""
    return jsonify({'municipios': [{'clave': m, 'nombre': m.title().replace('Itagui', 'Itagüí')
                                    .replace('Medellin', 'Medellín')} for m in MUNICIPIOS]}), 200


@escolar_bp.route('/colegios', methods=['GET'])
def colegios():
    """Autocompletar de colegios (público: el catálogo es información abierta)."""
    if not allow_request(f'colegios:{request.remote_addr}', 120, 60):
        return jsonify({'error': 'Demasiadas búsquedas seguidas.'}), 429
    consulta = (request.args.get('q') or '')[:80]
    return jsonify({'colegios': escolar_service.buscar_colegios(consulta, request.args.get('municipio'))}), 200


@escolar_bp.route('/geocodificar', methods=['POST'])
@jwt_required()
def geocodificar():
    usuario_id = int(get_jwt_identity())
    if not allow_request(f'geocodificar:{usuario_id}', 20, 60):
        return jsonify({'error': 'Espera un momento antes de volver a buscar la dirección.'}), 429
    datos = request.get_json(silent=True) or {}
    respuesta = geocodificador.geocodificar((datos.get('direccion') or '')[:200], datos.get('municipio'))
    # El estrato no se le devuelve al estudiante: es un dato para el análisis agregado.
    respuesta.pop('estrato', None)
    return jsonify(respuesta), 200


@escolar_bp.route('/mio', methods=['GET'])
@jwt_required()
def mio():
    perfil = escolar_service.perfil_de(int(get_jwt_identity()))
    datos = perfil.to_dict() if perfil else {'completo': False}
    datos.pop('estrato', None)
    return jsonify(datos), 200


@escolar_bp.route('/mio', methods=['PUT'])
@jwt_required()
def guardar_mio():
    try:
        perfil = escolar_service.guardar_perfil(int(get_jwt_identity()), request.get_json(silent=True) or {})
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    datos = perfil.to_dict()
    datos.pop('estrato', None)
    return jsonify(datos), 200
