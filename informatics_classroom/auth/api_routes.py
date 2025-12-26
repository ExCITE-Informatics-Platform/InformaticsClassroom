"""
API Authentication Routes for React SPA

These routes provide JWT-based authentication for the React SPA,
integrating with the existing MSAL authentication flow.
"""

from flask import jsonify, request, session, url_for
from informatics_classroom.auth import auth_bp
from informatics_classroom.auth.jwt_utils import (
    generate_access_token,
    generate_refresh_token,
    refresh_access_token,
    require_jwt_token
)
import jwt as pyjwt


@auth_bp.route("/api/auth/login", methods=["POST"])
def api_login():
    """
    Initiate MSAL login flow for React SPA.

    Returns:
        JSON with auth_url to redirect user to Microsoft login
    """
    from informatics_classroom.auth.routes import _build_auth_code_flow
    from informatics_classroom.config import Config

    # Build MSAL auth code flow
    flow = _build_auth_code_flow(scopes=Config.SCOPE)
    session["flow"] = flow

    return jsonify({
        "auth_url": flow["auth_uri"],
        "message": "Redirect user to auth_url for Microsoft login"
    }), 200


@auth_bp.route("/api/auth/callback", methods=["GET"])
def api_callback():
    """
    MSAL callback endpoint that issues JWT tokens for React SPA.

    This endpoint:
    1. Completes the MSAL authentication flow
    2. Extracts user information
    3. Issues JWT access and refresh tokens
    4. Returns tokens to React for storage

    Query Parameters:
        code: Authorization code from Microsoft
        state: State parameter for CSRF protection

    Returns:
        JSON with JWT tokens and user information
    """
    from informatics_classroom.auth.routes import _build_msal_app, _load_cache, _save_cache

    try:
        cache = _load_cache()
        result = _build_msal_app(cache=cache).acquire_token_by_auth_code_flow(
            session.get("flow", {}),
            request.args
        )

        if "error" in result:
            return jsonify({
                "error": result.get("error"),
                "error_description": result.get("error_description")
            }), 400

        # Extract user information from ID token
        user_data = result.get("id_token_claims")
        session["user"] = user_data
        _save_cache(cache)

        # AUTO-CREATE USER ON FIRST SSO LOGIN
        from informatics_classroom.database.factory import get_database_adapter
        import datetime as dt

        user_id = user_data.get("oid") or user_data.get("sub") or user_data.get("email", "").split('@')[0]
        db = get_database_adapter()
        db_user = db.get('users', user_id)

        if not db_user:
            # Create user on first SSO login
            import sys
            print(f"DEBUG - Creating user {user_id} on first SSO login", file=sys.stderr)
            sys.stderr.flush()

            db_user = {
                'id': user_id,
                'email': user_data.get("email") or user_data.get("preferred_username"),
                'name': user_data.get("name"),
                'roles': user_data.get("roles", ['student']),  # Get roles from Azure AD or default to student
                'class_memberships': [],
                'classRoles': {},
                'accessible_classes': [],
                'created_at': dt.datetime.utcnow().isoformat(),
                'team': user_id,
                'isActive': True,
                'permissions': []
            }
            db.upsert('users', db_user)
            print(f"DEBUG - Created user {user_id} in database", file=sys.stderr)
            sys.stderr.flush()

        # Merge Azure AD data with database roles
        # Database roles take precedence (admin set in DB, not Azure AD)
        user_roles = db_user.get('roles', []) if db_user else user_data.get("roles", ['student'])

        # Create merged user data for token generation
        merged_user_data = dict(user_data)
        merged_user_data['roles'] = user_roles

        # Generate JWT tokens with database roles
        access_token = generate_access_token(merged_user_data)
        refresh_token = generate_refresh_token(user_data.get("oid") or user_data.get("sub"))

        # Return tokens and user info to React
        return jsonify({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": 3600,  # 1 hour
            "user": {
                "id": user_data.get("oid") or user_data.get("sub"),
                "email": user_data.get("email") or user_data.get("preferred_username"),
                "displayName": user_data.get("name"),
                "roles": user_roles  # Use database roles, not Azure AD roles
            }
        }), 200

    except ValueError as e:
        # Usually caused by CSRF or invalid flow
        return jsonify({
            "error": "Authentication failed",
            "message": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


@auth_bp.route("/api/auth/refresh", methods=["POST"])
def api_refresh():
    """
    Refresh access token using refresh token.

    Request Body:
        {
            "refresh_token": "..."
        }

    Returns:
        JSON with new access token
    """
    data = request.get_json()
    refresh_token = data.get("refresh_token")

    if not refresh_token:
        return jsonify({
            "error": "Refresh token required",
            "message": "Missing refresh_token in request body"
        }), 400

    try:
        new_access_token = refresh_access_token(refresh_token)

        return jsonify({
            "access_token": new_access_token,
            "token_type": "Bearer",
            "expires_in": 3600
        }), 200

    except pyjwt.InvalidTokenError as e:
        return jsonify({
            "error": "Invalid refresh token",
            "message": str(e)
        }), 401


@auth_bp.route("/api/auth/session", methods=["GET"])
def api_get_session():
    """
    Get current user session information.

    Supports both JWT tokens (production) and session cookies (development).
    In development mode (DEBUG=True), auto-creates session if none exists.

    Returns:
        JSON with current user information
    """
    import sys
    print("=" * 80, file=sys.stderr)
    print("API AUTH SESSION CALLED - FUNCTION ENTRY POINT", file=sys.stderr)
    print("=" * 80, file=sys.stderr)
    sys.stderr.flush()

    from informatics_classroom.config import Config
    from informatics_classroom.database.factory import get_database_adapter

    print(f"Config.DEBUG = {Config.DEBUG}", file=sys.stderr)
    sys.stderr.flush()

    # Development mode logging (NO auto-login - security risk!)
    if Config.DEBUG:
        import sys
        print(f"DEBUG - /api/auth/session - session.get('user'): {session.get('user')}", file=sys.stderr)

        # SECURITY FIX: Do NOT auto-create sessions or escalate privileges
        # Users must authenticate via SSO even in debug mode
        # If session exists but has empty roles, look up from database (don't auto-grant admin)
        if session.get("user"):
            roles = session["user"].get("roles")
            print(f"DEBUG - /api/auth/session - existing session, roles: {roles}, type: {type(roles)}", file=sys.stderr)

            if not roles or (isinstance(roles, list) and len(roles) == 0):
                # Look up actual roles from database instead of auto-granting admin
                user_id = session["user"].get("id") or session["user"].get("preferred_username", "").split('@')[0]
                db = get_database_adapter()
                db_user = db.get('users', user_id)
                if db_user:
                    session["user"]["roles"] = db_user.get('roles', ['student'])
                    session.modified = True
                    print(f"DEBUG - /api/auth/session - loaded roles from DB: {session['user']['roles']}", file=sys.stderr)
                else:
                    # User not in database - default to student, NOT admin
                    session["user"]["roles"] = ['student']
                    session.modified = True
                    print(f"DEBUG - /api/auth/session - user not in DB, defaulting to student role", file=sys.stderr)

    # Try JWT token first, then fall back to session cookie
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_data = None

    if token:
        # Try JWT authentication
        try:
            from informatics_classroom.auth.jwt_utils import decode_token
            payload = decode_token(token)
            if payload.get('type') == 'access':
                user_data = {
                    "user_id": payload.get("user_id"),
                    "email": payload.get("email"),
                    "displayName": payload.get("display_name"),
                    "roles": payload.get("roles", [])
                }
        except:
            pass  # Token invalid, try session fallback

    # Fallback to session authentication (development mode)
    if not user_data and session.get("user"):
        session_user = session["user"]
        # Use 'id' field if present (for impersonation), otherwise extract from preferred_username
        user_id = session_user.get("id") or session_user.get("preferred_username", "").split('@')[0]

        # Get full user data from database
        db = get_database_adapter()
        db_user = db.get('users', user_id)

        # Build class memberships and user data from database
        class_roles = {}
        class_memberships = []
        accessible_classes = []
        user_email = ""
        user_display_name = ""
        user_roles = []
        username = ""

        if db_user:
            import sys
            print(f"DEBUG /api/auth/session - db_user found for user_id={user_id}", file=sys.stderr)
            print(f"DEBUG - db_user email field: {repr(db_user.get('email'))}", file=sys.stderr)
            print(f"DEBUG - db_user name field: {repr(db_user.get('name'))}", file=sys.stderr)
            sys.stderr.flush()

            class_roles = db_user.get('classRoles', {})
            class_memberships = db_user.get('class_memberships', [])
            accessible_classes = db_user.get('accessible_classes', [])

            # Build defaults for missing data
            db_email = db_user.get('email', '')
            user_email = db_email if db_email else f"{user_id}@jhu.edu"

            db_name = db_user.get('name', '')
            user_display_name = db_name if db_name else user_id

            user_roles = db_user.get('roles', [])
            username = db_user.get('id', '')

            print(f"DEBUG - After processing: user_email={repr(user_email)}, user_display_name={repr(user_display_name)}", file=sys.stderr)
            sys.stderr.flush()

            # Build classRoles from class_memberships if classRoles is empty
            if not class_roles and class_memberships:
                class_roles = {}
                for membership in class_memberships:
                    if isinstance(membership, dict):
                        class_id = membership.get('class_id')
                        role = membership.get('role')
                        if class_id and role:
                            class_roles[class_id] = role

        # In development mode, generate JWT tokens
        access_token = None
        refresh_token = None
        if Config.DEBUG:
            jwt_user_data = {
                'id': user_id,
                'email': user_email,
                'displayName': user_display_name,
                'roles': user_roles,
                'preferred_username': user_email
            }
            access_token = generate_access_token(jwt_user_data)
            refresh_token = generate_refresh_token(user_id)

        response_data = {
            "user": {
                "id": user_id,
                "email": user_email,
                "displayName": user_display_name,
                "username": username,
                "roles": user_roles,
                "classRoles": class_roles,
                "class_memberships": class_memberships,
                "accessible_classes": accessible_classes,
                "createdAt": db_user.get('createdAt', '') if db_user else '',
                "isActive": db_user.get('isActive', True) if db_user else True,
                "permissions": db_user.get('permissions', []) if db_user else []
            },
            "isAuthenticated": True
        }

        # Include impersonation status if active
        impersonation = session.get('impersonation')
        if impersonation:
            response_data["impersonating"] = True
            response_data["original_user"] = {
                "id": impersonation.get("original_user_id"),
                "email": impersonation.get("original_user_email"),
                "displayName": impersonation.get("original_user_name")
            }
        else:
            response_data["impersonating"] = False

        # Include JWT tokens in development mode
        if Config.DEBUG and access_token:
            response_data["accessToken"] = access_token
            response_data["refreshToken"] = refresh_token

        return jsonify(response_data), 200

    # JWT token authentication successful
    if user_data:
        return jsonify({
            "user": {
                "id": user_data.get("user_id"),
                "email": user_data.get("email"),
                "displayName": user_data.get("displayName"),
                "roles": user_data.get("roles", [])
            },
            "isAuthenticated": True
        }), 200

    # No authentication found
    return jsonify({
        "success": False,
        "error": "Not authenticated"
    }), 401


@auth_bp.route("/api/auth/logout", methods=["POST"])
@require_jwt_token
def api_logout():
    """
    Logout user (client-side token cleanup).

    For React SPA, logout is primarily client-side (delete tokens from localStorage).
    This endpoint clears server-side session if present.

    Returns:
        JSON confirmation
    """
    session.clear()

    from informatics_classroom.config import Config

    return jsonify({
        "message": "Logged out successfully",
        "logout_url": Config.AUTHORITY + "/oauth2/v2.0/logout"
    }), 200


@auth_bp.route("/api/auth/validate", methods=["POST"])
def api_validate_token():
    """
    Validate a JWT token without requiring authentication decorator.

    Useful for client-side token validation.

    Request Body:
        {
            "token": "..."
        }

    Returns:
        JSON with validation result
    """
    from informatics_classroom.auth.jwt_utils import decode_token

    data = request.get_json()
    token = data.get("token")

    if not token:
        return jsonify({
            "valid": False,
            "error": "Token required"
        }), 400

    try:
        payload = decode_token(token)
        return jsonify({
            "valid": True,
            "payload": {
                "user_id": payload.get("user_id"),
                "email": payload.get("email"),
                "expires": payload.get("exp")
            }
        }), 200

    except pyjwt.ExpiredSignatureError:
        return jsonify({
            "valid": False,
            "error": "Token expired"
        }), 200  # Return 200 with error info, not 401

    except pyjwt.InvalidTokenError as e:
        return jsonify({
            "valid": False,
            "error": str(e)
        }), 200  # Return 200 with error info, not 401
