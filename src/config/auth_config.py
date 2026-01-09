"""
Authentication configuration and management for the Forex Profit Monitoring System.
"""
import os
import logging
from typing import Dict, Optional, Any
from functools import wraps
from flask import session, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from dotenv import load_dotenv
from pathlib import Path
import jwt
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
env_path = Path(__file__).resolve().parents[2] / '.env'
load_dotenv(env_path)
logger.info(f"Loading environment variables from: {env_path}")

class AuthConfig:
    def __init__(self):
        # Load credentials from environment variables with defaults
        self._load_credentials()
        
        # Session configuration
        self.session_lifetime = int(os.getenv('APP_SESSION_LIFETIME', '3600'))  # 1 hour
        self.remember_me_lifetime = int(os.getenv('APP_REMEMBER_ME_LIFETIME', '2592000'))  # 30 days
        
        # Initialize allowed origins from environment variable
        allowed_origins_str = os.getenv('ALLOWED_ORIGINS', '')
        self.allowed_origins = [origin.strip() for origin in allowed_origins_str.split(',') if origin.strip()]
        if not self.allowed_origins:
            self.allowed_origins = ['*']  # Fallback to allow all if none specified
        
        # Log configuration status
        logger.info("Auth configuration initialized")
        logger.info(f"Using username: {self.username}")
        logger.info(f"Session lifetime: {self.session_lifetime} seconds")
        
    def _load_credentials(self):
        """Load credentials with proper error handling"""
        try:
            # Get username from environment or use default
            self.username = os.getenv('APP_USERNAME')
            if not self.username:
                logger.warning("APP_USERNAME not found in .env, using default: 'admin'")
                self.username = 'admin'
            else:
                logger.info(f"Loaded username from .env: {self.username}")

            # Get or generate secret key
            self.secret_key = os.getenv('APP_SECRET_KEY')
            if not self.secret_key:
                logger.warning("APP_SECRET_KEY not found in .env, generating new one")
                self.secret_key = secrets.token_hex(32)
            else:
                logger.info("Loaded secret key from .env")

            # Handle password
            password = os.getenv('APP_PASSWORD')
            if not password:
                logger.warning("APP_PASSWORD not found in .env, using default: 'changeme'")
                password = 'changeme'
            else:
                logger.info("Loaded password from .env")
            
            # Hash the password
            self.password_hash = generate_password_hash(password)
            
        except Exception as e:
            logger.error(f"Error loading credentials from .env: {str(e)}")
            # Set safe defaults
            self.username = 'admin'
            self.password_hash = generate_password_hash('changeme')
            self.secret_key = secrets.token_hex(32)
    
    def verify_password(self, password: str) -> bool:
        """Verify if the provided password matches the stored hash."""
        try:
            result = check_password_hash(self.password_hash, password)
            logger.debug(f"Password verification for user {self.username}: {'success' if result else 'failed'}")
            return result
        except Exception as e:
            logger.error(f"Error verifying password: {str(e)}")
            return False
    
    def update_credentials(self, username: Optional[str] = None, password: Optional[str] = None) -> bool:
        """Update username and/or password."""
        try:
            env_file = Path(__file__).resolve().parents[2] / '.env'
            current_env = {}
            
            # Read current .env content
            if env_file.exists():
                with open(env_file, 'r') as f:
                    for line in f:
                        if '=' in line and not line.startswith('#'):
                            key, value = line.strip().split('=', 1)
                            current_env[key] = value

            # Update values
            if username:
                current_env['APP_USERNAME'] = username
                self.username = username
                logger.info(f"Username updated to: {username}")
            
            if password:
                current_env['APP_PASSWORD'] = password
                self.password_hash = generate_password_hash(password)
                logger.info("Password updated successfully")

            # Write back to .env file
            with open(env_file, 'w') as f:
                for key, value in current_env.items():
                    f.write(f"{key}={value}\n")
            
            return True
        except Exception as e:
            logger.error(f"Error updating credentials in .env: {str(e)}")
            return False
    
    def get_config(self) -> Dict:
        """Get the current authentication configuration."""
        return {
            'username': self.username,
            'session_lifetime': self.session_lifetime,
            'remember_me_lifetime': self.remember_me_lifetime
        }

    def generate_embed_token(self, domain: str, permissions: Optional[Dict[str, Any]] = None) -> str:
        """Generate a JWT token for embedding with domain and permissions"""
        if not domain:
            raise ValueError("Domain is required for embed token generation")
            
        if not permissions:
            permissions = {
                "views": ["minimal", "chart", "positions"],
                "features": ["read"]
            }
            
        payload = {
            "domain": domain,
            "permissions": permissions,
            "exp": datetime.utcnow() + timedelta(days=30),  # 30 days expiration
            "iat": datetime.utcnow(),
            "type": "embed"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
        
    def validate_embed_token(self, token: str, request_domain: str) -> Dict[str, Any]:
        """Validate embed token and return permissions if valid"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            
            # Check token type
            if payload.get("type") != "embed":
                raise ValueError("Invalid token type")
                
            # Check domain
            token_domain = payload.get("domain")
            if not token_domain:
                raise ValueError("Token missing domain")
                
            # Validate domain - allow subdomains of the token domain
            if not (request_domain == token_domain or 
                   request_domain.endswith('.' + token_domain)):
                raise ValueError(f"Domain mismatch: {request_domain} vs {token_domain}")
                
            # Check expiration
            if datetime.utcnow() > datetime.fromtimestamp(payload["exp"]):
                raise ValueError("Token expired")
                
            return payload["permissions"]
            
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {str(e)}")

def login_required(f):
    """Decorator to require login for routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            logger.warning(f"Unauthorized access attempt to {request.path}")
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        logger.debug(f"Authorized access to {request.path} by {session['user_id']}")
        return f(*args, **kwargs)
    return decorated_function

# Initialize authentication configuration
auth_config = AuthConfig() 