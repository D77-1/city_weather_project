from flask import jsonify


def success(data=None, message='ok'):
    return jsonify({'code': 200, 'message': message, 'data': data})


def error(message='error', code=400):
    return jsonify({'code': code, 'message': message, 'data': None}), code
