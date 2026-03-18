from flask import Blueprint, jsonify
from app.models import Provincia

utils_api_bp = Blueprint('utils_api', __name__)

@utils_api_bp.route('/geografia', methods=['GET'])
def get_geografia():
    """
    Retorna uma lista de todas as províncias e seus respectivos municípios.
    Essencial para preencher formulários de registo e filtros no frontend.
    """
    try:
        provincias = Provincia.query.all()
        
        # Usar o to_dict() dos modelos para serializar
        resultado = []
        for prov in provincias:
            prov_dict = prov.to_dict()
            prov_dict['municipios'] = [mun.to_dict() for mun in prov.municipios]
            resultado.append(prov_dict)

        return jsonify({
            "success": True,
            "data": resultado
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "errors": [str(e)]
        }), 500
