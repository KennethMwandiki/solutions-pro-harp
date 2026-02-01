"""
Example: Using Azure AD Authentication in Streamlit Dashboard

This shows how to protect dashboard pages with Azure AD authentication
and role-based access control.
"""

import streamlit as st
from auth import require_auth, get_current_user, is_authenticated

# Protect the entire dashboard with authentication
# Minimum role required is "Viewer"
@require_auth(role="Viewer")
def main():
    st.title("🛡️ Pro-Harp Emergency Response Dashboard")
    
    # Get current user info
    user = get_current_user()
    
    # Display user info in sidebar
    with st.sidebar:
        st.write(f"**Logged in as:** {user.get('displayName', 'Unknown')}")
        st.write(f"**Email:** {user.get('userPrincipalName', 'N/A')}")
        
        # Show user's roles/groups
        groups = user.get('groups', [])
        if groups:
            st.write("**Roles:**")
            for group in groups[:5]:  # Show first 5 groups
                st.write(f"- {group.get('displayName', 'Unknown')}")
        
        if st.button("Logout"):
            from auth import AzureAuthenticator
            auth = AzureAuthenticator()
            auth.logout()
            st.rerun()
    
    # Main content
    st.write("Welcome to the Pro-Harp Emergency Response System!")
    st.write("You have been successfully authenticated via Azure AD.")
    
    # Example: Show different content based on role
    st.subheader("Role-Based Access")
    
    # Check if user has Admin role
    from auth import AzureAuthenticator
    auth = AzureAuthenticator()
    
    if auth.check_role(user, "Admin"):
        st.success("✅ You have Admin access")
        st.write("You can access all dashboard features including:")
        st.write("- Entity Management (full CRUD)")
        st.write("- Incident Response Configuration")
        st.write("- System Settings")
    elif auth.check_role(user, "Operator"):
        st.info("ℹ️ You have Operator access")
        st.write("You can:")
        st.write("- View and edit entities")
        st.write("- Manage incidents")
        st.write("- View reports")
    else:
        st.warning("⚠️ You have Viewer access")
        st.write("You can view dashboards and reports in read-only mode")


if __name__ == "__main__":
    main()
