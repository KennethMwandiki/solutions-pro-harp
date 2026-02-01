"""
Azure AD Authentication Module for Pro-Harp Dashboard
Provides secure authentication using Microsoft Authentication Library (MSAL)
"""

import streamlit as st
from msal import ConfidentialClientApplication, SerializableTokenCache
from typing import Optional, Dict, List
import os
import jwt
from functools import wraps
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class AzureAuthenticator:
    """Handles Azure AD authentication and authorization"""
    
    def __init__(self):
        """Initialize Azure AD configuration from environment variables"""
        self.client_id = os.getenv("AZURE_CLIENT_ID")
        self.tenant_id = os.getenv("AZURE_TENANT_ID")
        self.client_secret = os.getenv("AZURE_CLIENT_SECRET")
        self.redirect_uri = os.getenv("REDIRECT_URI", "http://localhost:8501")
        self.dev_mode = os.getenv("DEV_MODE") == "true"
        
        # Validate configuration (skip if in dev mode)
        if not self.dev_mode and not all([self.client_id, self.tenant_id, self.client_secret]):
            raise ValueError("Azure AD configuration missing. Set AZURE_CLIENT_ID, AZURE_TENANT_ID, and AZURE_CLIENT_SECRET")
        
        # Authority URL
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        
        # Scopes for user authentication
        self.scopes = ["User.Read"]
        
        # Initialize MSAL app
        self.msal_app = ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret,
        )
    
    def get_auth_url(self) -> str:
        """
        Generate Azure AD authorization URL for user login
        
        Returns:
            str: Authorization URL to redirect user to
        """
        auth_url = self.msal_app.get_authorization_request_url(
            scopes=self.scopes,
            redirect_uri=self.redirect_uri
        )
        return auth_url
    
    def acquire_token_by_auth_code(self, auth_code: str) -> Optional[Dict]:
        """
        Exchange authorization code for access token
        
        Args:
            auth_code: Authorization code from Azure AD callback
            
        Returns:
            Token response dict or None if failed
        """
        result = self.msal_app.acquire_token_by_authorization_code(
            auth_code,
            scopes=self.scopes,
            redirect_uri=self.redirect_uri
        )
        
        if "access_token" in result:
            return result
        else:
            print(f"Token acquisition failed: {result.get('error_description')}")
            return None
    
    def get_user_info(self, access_token: str) -> Optional[Dict]:
        """
        Fetch user information from Microsoft Graph API
        
        Args:
            access_token: Valid Azure AD access token
            
        Returns:
            User info dict with name, email, roles, etc.
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(
            "https://graph.microsoft.com/v1.0/me",
            headers=headers
        )
        
        if response.status_code == 200:
            user_info = response.json()
            
            # Fetch user's group memberships for RBAC
            groups_response = requests.get(
                "https://graph.microsoft.com/v1.0/me/memberOf",
                headers=headers
            )
            
            if groups_response.status_code == 200:
                user_info["groups"] = groups_response.json().get("value", [])
            
            return user_info
        else:
            print(f"Failed to fetch user info: {response.status_code}")
            return None
    
    def check_role(self, user_info: Dict, required_role: str) -> bool:
        """
        Check if user has required role based on Azure AD groups
        
        Args:
            user_info: User information dict from get_user_info()
            required_role: Required role name (Admin, Operator, Viewer)
            
        Returns:
            bool: True if user has required role
        """
        # Role hierarchy
        role_hierarchy = {
            "Admin": 3,
            "Operator": 2,
            "Viewer": 1
        }
        
        required_level = role_hierarchy.get(required_role, 0)
        
        # Extract group names from user's groups
        user_groups = user_info.get("groups", [])
        user_group_names = [group.get("displayName", "") for group in user_groups]
        
        # Check if user has required role or higher
        for role, level in role_hierarchy.items():
            if level >= required_level and role in user_group_names:
                return True
        
        return False
    
    def logout(self):
        """Clear authentication session"""
        if "user_info" in st.session_state:
            del st.session_state["user_info"]
        if "access_token" in st.session_state:
            del st.session_state["access_token"]


def require_auth(role: str = "Viewer"):
    """
    Decorator to protect Streamlit pages with Azure AD authentication
    
    Args:
        role: Minimum required role (Admin, Operator, Viewer)
    
    Usage:
        @require_auth(role="Operator")
        def main():
            st.write("Protected content")
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check for Dev Mode bypass
            if os.getenv("DEV_MODE") == "true":
                if "user_info" not in st.session_state:
                    st.session_state["user_info"] = {
                        "displayName": "Dev Administrator",
                        "mail": "dev-admin@proharp.local",
                        "groups": [{"displayName": "Admin"}]
                    }
                return func(*args, **kwargs)

            # Initialize authenticator
            try:
                auth = AzureAuthenticator()
            except ValueError as e:
                st.error(f"Authentication configuration error: {e}")
                st.stop()
            
            # Check if user is already authenticated
            if "user_info" not in st.session_state:
                # Show login page
                st.title("🔐 Pro-Harp Authentication")
                st.write("Please sign in with your Azure AD account to access the dashboard.")
                
                # Check for authorization code in URL query params
                query_params = st.query_params
                
                if "code" in query_params:
                    # Exchange auth code for token
                    auth_code = query_params["code"]
                    token_response = auth.acquire_token_by_auth_code(auth_code)
                    
                    if token_response:
                        # Fetch user info
                        user_info = auth.get_user_info(token_response["access_token"])
                        
                        if user_info:
                            # Store in session
                            st.session_state["user_info"] = user_info
                            st.session_state["access_token"] = token_response["access_token"]
                            st.rerun()
                        else:
                            st.error("Failed to fetch user information")
                            st.stop()
                    else:
                        st.error("Authentication failed. Please try again.")
                        st.stop()
                else:
                    # Show login button
                    auth_url = auth.get_auth_url()
                    st.markdown(f'<a href="{auth_url}" target="_self"><button>Sign in with Microsoft</button></a>', unsafe_allow_html=True)
                    st.stop()
            
            # Check role authorization
            user_info = st.session_state["user_info"]
            
            if not auth.check_role(user_info, role):
                st.error(f"❌ Access Denied: You need '{role}' role to access this page.")
                st.write(f"Current user: {user_info.get('displayName', 'Unknown')}")
                
                if st.button("Logout"):
                    auth.logout()
                    st.rerun()
                
                st.stop()
            
            # User is authenticated and authorized
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def get_current_user() -> Optional[Dict]:
    """
    Get currently authenticated user info
    
    Returns:
        User info dict or None if not authenticated
    """
    return st.session_state.get("user_info")


def is_authenticated() -> bool:
    """
    Check if user is currently authenticated
    
    Returns:
        bool: True if user is authenticated
    """
    return "user_info" in st.session_state
