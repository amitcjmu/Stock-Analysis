"""
Credential Validators
Provides validation logic for different credential types
"""

import base64
import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import requests
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)


class CredentialValidationError(Exception):
    """Exception for credential validation errors"""
    pass


class CredentialValidator:
    """Base class for credential validators"""
    
    async def validate(self, credential_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate credential data
        
        Args:
            credential_data: Credential data to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        raise NotImplementedError


class APIKeyValidator(CredentialValidator):
    """Validator for API key credentials"""
    
    def __init__(self, test_endpoint: Optional[str] = None):
        self.test_endpoint = test_endpoint
    
    async def validate(self, credential_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate API key credential"""
        api_key = credential_data.get("api_key")
        
        if not api_key:
            return False, "API key is required"
        
        # Basic format validation
        if not isinstance(api_key, str) or len(api_key) < 10:
            return False, "Invalid API key format"
        
        # Check for common patterns
        if api_key.lower() in ["test", "demo", "example", "dummy"]:
            return False, "Test/demo API keys are not allowed"
        
        # If test endpoint provided, validate against it
        if self.test_endpoint:
            try:
                headers = credential_data.get("headers", {})
                headers.update({"Authorization": f"Bearer {api_key}"})
                
                response = requests.get(
                    self.test_endpoint,
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 401:
                    return False, "API key authentication failed"
                elif response.status_code >= 400:
                    return False, f"API returned error: {response.status_code}"
                
            except requests.RequestException as e:
                logger.warning(f"Failed to validate API key: {e}")
                # Don't fail validation on network errors
        
        return True, None


class BasicAuthValidator(CredentialValidator):
    """Validator for basic authentication credentials"""
    
    def __init__(self, test_endpoint: Optional[str] = None):
        self.test_endpoint = test_endpoint
    
    async def validate(self, credential_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate basic auth credential"""
        username = credential_data.get("username")
        password = credential_data.get("password")
        
        if not username:
            return False, "Username is required"
        
        if not password:
            return False, "Password is required"
        
        # Basic validation
        if len(username) < 3:
            return False, "Username too short"
        
        if len(password) < 8:
            return False, "Password too short (minimum 8 characters)"
        
        # Check for weak passwords
        weak_passwords = ["password", "12345678", "qwerty", "admin", "letmein"]
        if password.lower() in weak_passwords:
            return False, "Password is too weak"
        
        # If test endpoint provided, validate against it
        if self.test_endpoint:
            try:
                response = requests.get(
                    self.test_endpoint,
                    auth=HTTPBasicAuth(username, password),
                    timeout=10
                )
                
                if response.status_code == 401:
                    return False, "Authentication failed"
                elif response.status_code >= 400:
                    return False, f"API returned error: {response.status_code}"
                
            except requests.RequestException as e:
                logger.warning(f"Failed to validate basic auth: {e}")
        
        return True, None


class OAuth2Validator(CredentialValidator):
    """Validator for OAuth2 credentials"""
    
    def __init__(self, token_endpoint: Optional[str] = None):
        self.token_endpoint = token_endpoint
    
    async def validate(self, credential_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate OAuth2 credential"""
        client_id = credential_data.get("client_id")
        client_secret = credential_data.get("client_secret")
        
        if not client_id:
            return False, "Client ID is required"
        
        if not client_secret:
            return False, "Client secret is required"
        
        # Basic validation
        if len(client_id) < 10:
            return False, "Client ID format appears invalid"
        
        if len(client_secret) < 20:
            return False, "Client secret format appears invalid"
        
        # Validate refresh token if present
        refresh_token = credential_data.get("refresh_token")
        if refresh_token and len(refresh_token) < 10:
            return False, "Refresh token format appears invalid"
        
        # If token endpoint provided, try to get access token
        if self.token_endpoint:
            try:
                data = {
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret
                }
                
                if credential_data.get("scope"):
                    data["scope"] = credential_data["scope"]
                
                response = requests.post(
                    self.token_endpoint,
                    data=data,
                    timeout=10
                )
                
                if response.status_code == 401:
                    return False, "OAuth2 authentication failed"
                elif response.status_code >= 400:
                    return False, f"Token endpoint returned error: {response.status_code}"
                
                # Check if we got a valid token
                token_data = response.json()
                if not token_data.get("access_token"):
                    return False, "No access token received"
                
            except requests.RequestException as e:
                logger.warning(f"Failed to validate OAuth2: {e}")
        
        return True, None


class ServiceAccountValidator(CredentialValidator):
    """Validator for service account credentials"""
    
    async def validate(self, credential_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate service account credential"""
        account_data = credential_data.get("account_data")
        
        if not account_data:
            return False, "Service account data is required"
        
        # Check if it's a JSON string or dict
        if isinstance(account_data, str):
            try:
                account_data = json.loads(account_data)
            except json.JSONDecodeError:
                return False, "Invalid JSON format for service account data"
        
        # Validate common service account fields
        required_fields = []
        
        # Google Cloud service account
        if "type" in account_data and account_data["type"] == "service_account":
            required_fields = ["project_id", "private_key_id", "private_key", "client_email"]
        
        # AWS service account
        elif "aws_access_key_id" in account_data:
            required_fields = ["aws_access_key_id", "aws_secret_access_key"]
        
        # Azure service principal
        elif "appId" in account_data or "clientId" in account_data:
            required_fields = ["appId", "password", "tenant"] if "appId" in account_data else ["clientId", "clientSecret", "tenantId"]
        
        # Check required fields
        missing_fields = [f for f in required_fields if f not in account_data]
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"
        
        # Validate private key if present
        if "private_key" in account_data:
            try:
                # Try to load as PEM
                private_key = account_data["private_key"]
                if isinstance(private_key, str) and "-----BEGIN" in private_key:
                    serialization.load_pem_private_key(
                        private_key.encode(),
                        password=None,
                        backend=default_backend()
                    )
            except Exception as e:
                return False, f"Invalid private key format: {str(e)}"
        
        return True, None


class CertificateValidator(CredentialValidator):
    """Validator for certificate credentials"""
    
    async def validate(self, credential_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate certificate credential"""
        certificate = credential_data.get("certificate")
        private_key = credential_data.get("private_key")
        
        if not certificate:
            return False, "Certificate is required"
        
        if not private_key:
            return False, "Private key is required"
        
        # Validate certificate
        try:
            # Try to load certificate
            if isinstance(certificate, str):
                cert_data = certificate.encode()
            else:
                cert_data = certificate
            
            cert = x509.load_pem_x509_certificate(cert_data, default_backend())
            
            # Check if certificate is expired
            if cert.not_valid_after < datetime.utcnow():
                return False, "Certificate has expired"
            
            # Check if certificate is not yet valid
            if cert.not_valid_before > datetime.utcnow():
                return False, "Certificate is not yet valid"
            
        except Exception as e:
            return False, f"Invalid certificate format: {str(e)}"
        
        # Validate private key
        try:
            if isinstance(private_key, str):
                key_data = private_key.encode()
            else:
                key_data = private_key
            
            # Try to load private key
            key = serialization.load_pem_private_key(
                key_data,
                password=credential_data.get("password", b"").encode() if credential_data.get("password") else None,
                backend=default_backend()
            )
            
            # TODO: Verify that the private key matches the certificate
            
        except Exception as e:
            return False, f"Invalid private key format: {str(e)}"
        
        return True, None


class SSHKeyValidator(CredentialValidator):
    """Validator for SSH key credentials"""
    
    async def validate(self, credential_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate SSH key credential"""
        private_key = credential_data.get("private_key")
        
        if not private_key:
            return False, "Private key is required"
        
        # Check for passphrase if encrypted
        passphrase = credential_data.get("passphrase")
        
        try:
            if isinstance(private_key, str):
                key_data = private_key.encode()
            else:
                key_data = private_key
            
            # Try to load SSH private key
            if key_data.startswith(b"-----BEGIN"):
                # PEM format
                key = serialization.load_pem_private_key(
                    key_data,
                    password=passphrase.encode() if passphrase else None,
                    backend=default_backend()
                )
            else:
                # Try OpenSSH format
                key = serialization.load_ssh_private_key(
                    key_data,
                    password=passphrase.encode() if passphrase else None,
                    backend=default_backend()
                )
            
            # Validate public key if provided
            public_key = credential_data.get("public_key")
            if public_key:
                try:
                    if isinstance(public_key, str):
                        pub_key_data = public_key.encode()
                    else:
                        pub_key_data = public_key
                    
                    # Load public key
                    pub_key = serialization.load_ssh_public_key(
                        pub_key_data,
                        backend=default_backend()
                    )
                except Exception:
                    return False, "Invalid public key format"
            
        except Exception as e:
            return False, f"Invalid SSH key format: {str(e)}"
        
        return True, None


class CustomCredentialValidator(CredentialValidator):
    """Validator for custom credentials"""
    
    async def validate(self, credential_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate custom credential - minimal validation"""
        if not credential_data:
            return False, "Credential data is required"
        
        # Custom credentials must have at least one field
        if not any(credential_data.values()):
            return False, "At least one credential field must have a value"
        
        return True, None


# Factory function to get validator
def get_credential_validator(
    credential_type: str,
    test_endpoint: Optional[str] = None
) -> CredentialValidator:
    """
    Get appropriate validator for credential type
    
    Args:
        credential_type: Type of credential
        test_endpoint: Optional endpoint for validation
        
    Returns:
        Credential validator instance
    """
    validators = {
        "api_key": APIKeyValidator,
        "basic_auth": BasicAuthValidator,
        "oauth2": OAuth2Validator,
        "service_account": ServiceAccountValidator,
        "certificate": CertificateValidator,
        "ssh_key": SSHKeyValidator,
        "custom": CustomCredentialValidator
    }
    
    validator_class = validators.get(credential_type, CustomCredentialValidator)
    
    if credential_type in ["api_key", "basic_auth"]:
        return validator_class(test_endpoint)
    elif credential_type == "oauth2":
        return validator_class(test_endpoint)
    else:
        return validator_class()