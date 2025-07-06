from flask import Blueprint, request, jsonify

# This is how we need to define the route
route = Blueprint('enrich_leads_v1', __name__)

# The execute endpoint should be defined like this
@route.route('/execute', methods=['POST'])
def execute():
    return jsonify({"test": "works"})