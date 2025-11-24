from functools import wraps

from flask import request, jsonify, g, current_app

from google.oauth2 import id_token

from google.auth.transport import requests

import jwt

import logging


logger = logging.getLogger(__name__)


def login_required(f):

    @wraps(f)

    def decorated_function(*args, **kwargs):

        # Skip auth if disabled (useful for dev/testing)
        enable_auth = current_app.config.get('ENABLE_AUTH')
        if enable_auth and str(enable_auth).lower() == 'false':

            return f(*args, **kwargs)


        # 1. Get the token from the header

        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith('Bearer '):

            return jsonify({'error': 'No token provided'}), 401
        

        token = auth_header.split(' ')[1]


        logger.info(f"Token: {token}")

        logger.info(f"enable auth: {enable_auth}")
        

        try:

            # 2. Verify the token (Backend JWT)

            secret_key = current_app.config.get('JWT_SECRET_KEY')

            if not secret_key:

                logger.error("JWT_SECRET_KEY not set")

                return jsonify({'error': 'Server configuration error'}), 500


            try:

                payload = jwt.decode(token, secret_key, algorithms=['HS256'])

            except jwt.ExpiredSignatureError:

                return jsonify({'error': 'Token has expired'}), 401

            except jwt.InvalidTokenError:

                return jsonify({'error': 'Invalid token'}), 401
            

            # 3. Store user info for the route to use

            g.user_id = payload.get('sub')

            g.user_email = payload.get('email')

            g.user_name = payload.get('name', '')

            g.user_picture = payload.get('picture', '')
            

            # 4. Check whitelist (Double check, though login already checked)

            allowed_emails_str = current_app.config.get('ALLOWED_EMAILS', '')

            if allowed_emails_str:

                allowed_emails = [e.strip().lower() for e in allowed_emails_str.split(',') if e.strip()]

                if allowed_emails and g.user_email.lower() not in allowed_emails:

                    logger.warning(f"Access denied for email: {g.user_email}")

                    return jsonify({'error': 'Access denied: Email not whitelisted'}), 403
            

        except Exception as e:

            logger.error(f"Auth error: {str(e)}")

            return jsonify({'error': 'Authentication failed'}), 401
            

        return f(*args, **kwargs)
    return decorated_function

