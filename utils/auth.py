from functools import wraps
from flask import request, jsonify, g, current_app
from google.oauth2 import id_token
from google.auth.transport import requests
import logging

logger = logging.getLogger(__name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip auth if disabled (useful for dev/testing)
        disable_auth = current_app.config.get('DISABLE_AUTH')
        if disable_auth and str(disable_auth).lower() == 'true':
            return f(*args, **kwargs)

        # 1. Get the token from the header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'No token provided'}), 401
        
        token = auth_header.split(' ')[1]

        logger.info(f"Token: {token}")
        logger.info(f"disabled auth: {disable_auth}")
        
        try:
            # 2. Verify the token with Google
            # Get Client ID from config
            client_id = current_app.config.get('GOOGLE_CLIENT_ID')
            if not client_id:
                logger.error("GOOGLE_CLIENT_ID not set in configuration")
                return jsonify({'error': 'Server configuration error'}), 500

            idinfo = id_token.verify_oauth2_token(
                token, 
                requests.Request(), 
                client_id
            )
            
            # 3. Store user info for the route to use
            g.user_id = idinfo['sub']
            g.user_email = idinfo['email']
            g.user_name = idinfo.get('name', '')
            g.user_picture = idinfo.get('picture', '')
            
            # 4. Check whitelist
            allowed_emails_str = current_app.config.get('ALLOWED_EMAILS', '')
            logger.info(f"ALLOWED_EMAILS config: '{allowed_emails_str}'")
            logger.info(f"User email: {g.user_email}")
            
            if allowed_emails_str:
                allowed_emails = [e.strip().lower() for e in allowed_emails_str.split(',') if e.strip()]
                logger.info(f"Parsed allowed emails: {allowed_emails}")
                
                if allowed_emails and g.user_email.lower() not in allowed_emails:
                    logger.warning(f"Access denied for email: {g.user_email}")
                    return jsonify({'error': 'Access denied: Email not whitelisted'}), 403
                else:
                    logger.info(f"Email {g.user_email} is in whitelist")
            else:
                logger.info("No ALLOWED_EMAILS configured - allowing all authenticated users")
            
        except ValueError as e:
            logger.warning(f"Invalid token: {str(e)}")
            return jsonify({'error': 'Invalid token'}), 401
        except Exception as e:
            logger.error(f"Auth error: {str(e)}")
            return jsonify({'error': 'Authentication failed'}), 401
            
        return f(*args, **kwargs)
    return decorated_function
