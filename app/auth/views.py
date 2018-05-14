from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

import datetime
from . import auth
from flask_jwt_extended import get_raw_jwt, jwt_required, get_jwt_identity
from flask_bcrypt import Bcrypt
from app.models import User, TokenBlacklist
from app.view_helpers import validate_email, token_generator
from app.utils import validate_auth_data_null, check_blank_key, require_json

@auth.route('/register', methods=['POST'])
@require_json
def register():
    try:
        required_fields = ['email', 'password', 'username', 'first_name']
        data = check_blank_key(request.get_json(), required_fields)
    except AssertionError as err:
        msg = err.args[0]
        return jsonify({"message": msg})

    email = validate_auth_data_null(data.get('email'))
    username = validate_auth_data_null(data.get('username'))
    first_name = validate_auth_data_null(data.get('first_name'))
    password = validate_auth_data_null(data.get('password'))

    if not username or not email or not password:
        return jsonify(
                {'message':'You need email, username and password to register'}), 400

    if not validate_email(email):
        return jsonify(
                {'message':'Invalid Email. Enter valid email to register'}), 400
    existant_user = User.query.filter_by(email=email).first()
    if existant_user:
        return jsonify(
                {'message': 'This email is registered, login instead'}), 404
    new_user = User(email=email, username=username,first_name=first_name,
                    password=password)
    new_user.save()
    return jsonify(
        {'message': 'New user Succesfully created'}), 201





@auth.route('/login', methods=['POST'])
@require_json
def login():
    try:
        required_fields = ['email', 'password']
        data = check_blank_key(request.get_json(), required_fields)
    except AssertionError as err:
        msg = err.args[0]
        return jsonify({"message": msg})
    email = validate_auth_data_null(data.get('email'))
    password = validate_auth_data_null(data.get('password'))

    if not email or not password:
        return jsonify(
                {'message':'Enter Valid Data: Email and password'}), 400

    user = User.query.filter_by(email=email).first()
    # print('Hellow owrld', password, user.password)
    if not user:
        return jsonify(
                {'message':'Invalid Email: Enter right credentions to login'}), 401
    elif not user.verify_password(password):
        return jsonify(
                {'message':'Invalid password: Enter right password to login'}), 401
    current_user = user.id
    return token_generator(current_user)


@auth.route('/logout', methods=['DELETE'])
@jwt_required
def logout():
    """ logout a user """
    jti = get_raw_jwt()['jti']
    user_identity = get_jwt_identity()
    tokenlist = TokenBlacklist(token=jti, user_identity=user_identity)
    tokenlist.save()
    return jsonify(
        {'message':'User Successfully logged out'}), 200


@auth.route('/changepassword', methods=['PUT'])
@require_json
@jwt_required
def change_password():
    try:
        required_fields = ['old_password', 'new_password']
        data = check_blank_key(request.get_json(), required_fields)
    except AssertionError as err:
        msg = err.args[0]
        return jsonify({"message": msg})
    old_password = validate_auth_data_null(data.get('old_password'))
    new_password = validate_auth_data_null(data.get('new_password'))
    jti = get_raw_jwt()['jti']

    if not old_password or not new_password :
        return jsonify(
                {'message':'Enter Valid Data: Email and password'}), 400
    current_user = get_jwt_identity()
    user = User.query.filter_by(id=current_user).first()
    if not user.verify_password(old_password):
        return jsonify(
                {'message':'Enter Valid Password: Old password is wrong'}), 400
    User.update(User, current_user, password=new_password)
    tokenlist = TokenBlacklist(token=jti, user_identity=current_user)
    tokenlist.save()
    return jsonify(
            {'message':'Password Successfully Changed'}), 200
