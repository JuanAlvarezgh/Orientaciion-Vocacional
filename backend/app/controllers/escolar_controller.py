"""Controlador escolar: municipios y buscador de colegios (los usa el registro)."""

from flask import Blueprint, jsonify, request

from ..services import escolar_service
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
