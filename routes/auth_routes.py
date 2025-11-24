from flask import Blueprint, jsonify, request, current_app
import logging
import jwt
import datetime
from google.oauth2 import id_token
from google.auth.transport import requests

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Exchange Google ID Token for a long-lived backend session token (JWT).
    """
    try:
        data = request.get_json()
        google_token = data.get('token')
        
        if not google_token:
            return jsonify({'error': 'No token provided'}), 400

        # 1. Verify Google Token
        client_id = current_app.config.get('GOOGLE_CLIENT_ID')
        if not client_id:
            logger.error("GOOGLE_CLIENT_ID not set")
            return jsonify({'error': 'Server configuration error'}), 500

        try:
            idinfo = id_token.verify_oauth2_token(
                google_token, 
                requests.Request(), 
                client_id
            )
        except ValueError as e:
            logger.warning(f"Invalid Google token: {str(e)}")
            return jsonify({'error': 'Invalid Google token'}), 401

        # 2. Check Whitelist
        user_email = idinfo['email']
        allowed_emails_str = current_app.config.get('ALLOWED_EMAILS', '')
        if allowed_emails_str:
            allowed_emails = [e.strip().lower() for e in allowed_emails_str.split(',') if e.strip()]
            if allowed_emails and user_email.lower() not in allowed_emails:
                logger.warning(f"Access denied for email: {user_email}")
                return jsonify({'error': 'Access denied: Email not whitelisted'}), 403

        # 3. Create Backend Session Token (JWT)
        expiration_seconds = current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 30 * 24 * 60 * 60)
        expiration = datetime.datetime.utcnow() + datetime.timedelta(seconds=expiration_seconds)
        
        payload = {
            'sub': idinfo['sub'],
            'email': user_email,
            'name': idinfo.get('name', ''),
            'picture': idinfo.get('picture', ''),
            'exp': expiration,
            'iat': datetime.datetime.utcnow(),
            'iss': 'mt5-trading-api'
        }
        
        secret_key = current_app.config.get('JWT_SECRET_KEY')
        session_token = jwt.encode(payload, secret_key, algorithm='HS256')

        logger.info(f"Issued session token for {user_email} (expires in {expiration_seconds}s)")

        return jsonify({
            'success': True,
            'token': session_token,
            'user': {
                'email': user_email,
                'name': idinfo.get('name', ''),
                'picture': idinfo.get('picture', '')
            }
        }), 200

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500
