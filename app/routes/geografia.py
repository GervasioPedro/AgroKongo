from flask import Blueprint, jsonify, current_app, request
from app.extensions import cache
import os
import json

geografia_bp = Blueprint('geografia', __name__, url_prefix='/api/geografia')


def _load_divisoes():
    data_path = os.path.join(current_app.root_path, 'data', 'ao_divisoes.json')
    with open(data_path, 'r', encoding='utf-8') as f:
        return json.load(f)


@geografia_bp.route('/provincias', methods=['GET'])
@cache.cached(timeout=3600)
def listar_provincias():
    """Lista de províncias (id, nome). Fonte: ficheiro canónico ao_divisoes.json.
    Nota: Preencher com a lista oficial (Lei 14/24) assim que disponível.
    """
    data = _load_divisoes()
    items = [{"id": p.get("id"), "nome": p.get("nome")} for p in data]
    return jsonify({"ok": True, "items": items})


@geografia_bp.route('/municipios', methods=['GET'])
@cache.cached(timeout=3600, query_string=True)
def listar_municipios():
    provincia_id = request.args.get('provincia_id', type=int)
    if not provincia_id:
        return jsonify({"ok": False, "message": "provincia_id obrigatorio"}), 400
    data = _load_divisoes()
    prov = next((p for p in data if p.get('id') == provincia_id), None)
    if not prov:
        return jsonify({"ok": False, "message": "provincia nao encontrada"}), 404
    items = prov.get('municipios', [])
    # Normalizar saída: apenas id e nome/slug
    items = [{"id": m.get("id"), "nome": m.get("nome"), "slug": m.get("slug")} for m in items]
    return jsonify({"ok": True, "items": items})
