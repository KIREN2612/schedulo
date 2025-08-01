#Create a blueprint for each module so the code is clean and easy to debug
from flask import Blueprint, jsonify

main = Blueprint('main', __name__)

@main.route('/ping', methods=['GET'])
def ping():
    return jsonify({"message": "pong"})
