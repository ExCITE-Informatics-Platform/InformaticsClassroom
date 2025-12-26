from flask_session import Session
import requests
from flask import render_template, session, redirect,url_for, request
from informatics_classroom.auth import auth_bp
from informatics_classroom.classroom import classroom_bp
import msal
from informatics_classroom.config import Config

def auth_configure_app(app):
    app.config.from_object(Config)
    Session(app)
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    app.jinja_env.globals.update(_build_auth_code_flow=_build_auth_code_flow)  # Used in template
    return app

@auth_bp.route("/login")
def login():
    # SECURITY FIX: Do NOT auto-login as a specific user in DEBUG mode
    # Even in development, users should authenticate via SSO for proper testing
    # DEBUG mode only bypasses some strict security checks, not identity

    # Check for repeated auth failures to prevent infinite loops
    retry_count = session.get("auth_retry_count", 0)
    if retry_count >= 3:
        # Too many failures - show error page instead of looping
        session["auth_retry_count"] = 0  # Reset for next attempt
        return render_template("login.html",
                             auth_url="#",
                             version=msal.__version__,
                             error="Authentication failed after multiple attempts. Please try again.")

    # Production: Auto-redirect to Microsoft (no intermediate login page)
    session["flow"] = _build_auth_code_flow(scopes=Config.SCOPE)
    return redirect(session["flow"]["auth_uri"])

@auth_bp.route(Config.REDIRECT_PATH)  # Its absolute URL must match your app's redirect_uri set in AAD
def authorized():
    try:
        cache = _load_cache()
        result = _build_msal_app(cache=cache).acquire_token_by_auth_code_flow(
            session.get("flow", {}), request.args)
        if "error" in result:
            # Increment retry count and redirect back to login (which auto-redirects to Microsoft)
            session["auth_retry_count"] = session.get("auth_retry_count", 0) + 1
            return redirect("/login")
        # Success - reset retry count and save session
        session["auth_retry_count"] = 0
        session["user"] = result.get("id_token_claims")
        _save_cache(cache)
    except ValueError:  # Usually caused by CSRF
        # Increment retry count and redirect back to login
        session["auth_retry_count"] = session.get("auth_retry_count", 0) + 1
        return redirect("/login")
    # Redirect to React SPA root after successful authentication
    return redirect("/")

@auth_bp.route("/api/auth/session", methods=["GET"])
def api_session():
    """API endpoint for React frontend to check authentication status"""
    from flask import jsonify
    from informatics_classroom.auth.jwt_utils import generate_access_token, generate_refresh_token

    # SECURITY FIX: Do NOT auto-login or auto-escalate privileges
    import sys
    print(f"DEBUG - Config.DEBUG = {Config.DEBUG}", file=sys.stderr)
    print(f"DEBUG - session.get('user') = {session.get('user')}", file=sys.stderr)
    sys.stderr.flush()

    # If session exists with empty roles, look up from database (don't auto-grant admin)
    if Config.DEBUG and session.get("user"):
        roles = session["user"].get("roles")
        if not roles or (isinstance(roles, list) and len(roles) == 0):
            from informatics_classroom.database.factory import get_database_adapter
            user_id = session["user"].get("id") or session["user"].get("preferred_username", "").split('@')[0]
            db = get_database_adapter()
            db_user = db.get('users', user_id)
            if db_user:
                session["user"]["roles"] = db_user.get('roles', ['student'])
            else:
                session["user"]["roles"] = ['student']
            session.modified = True
            print(f"DEBUG - Loaded roles from DB: {session['user']['roles']}", file=sys.stderr)
            sys.stderr.flush()

    if not session.get("user"):
        return jsonify({
            "success": False,
            "error": "Not authenticated"
        }), 401

    user_data = session["user"]
    # Use 'id' field if present (for impersonation), otherwise extract from preferred_username
    user_id = user_data.get('id') or user_data.get("preferred_username", "").split('@')[0]

    # Get full user data from database to include classRoles
    from informatics_classroom.database.factory import get_database_adapter
    import datetime as dt
    db = get_database_adapter()
    db_user = db.get('users', user_id)

    # Auto-create user if they don't exist (first login)
    if not db_user:
        print(f"DEBUG - User {user_id} not found in database, creating new user record", file=sys.stderr)
        sys.stderr.flush()

        db_user = {
            'id': user_id,
            'email': user_data.get('email', f"{user_id}@jhu.edu"),
            'name': user_data.get('name', user_id),
            'roles': user_data.get('roles', ['student']),  # Default to student role
            'class_memberships': [],  # Empty initially, will be populated on answer submission
            'classRoles': {},  # Legacy format
            'accessible_classes': [],  # Legacy format
            'created_at': dt.datetime.utcnow().isoformat(),
            'team': user_id  # Used for answer submissions
        }

        db.upsert('users', db_user)
        print(f"DEBUG - Created new user record for {user_id}", file=sys.stderr)
        sys.stderr.flush()

    # Build classRoles from database or default to empty
    class_roles = {}
    class_memberships = []
    accessible_classes = []
    created_at = ''
    permissions = []
    user_email = ''
    user_display_name = ''
    user_roles = []

    if db_user:
        class_roles = db_user.get('classRoles', {})
        class_memberships = db_user.get('class_memberships', [])
        accessible_classes = db_user.get('accessible_classes', [])
        created_at = db_user.get('created_at', db_user.get('createdAt', ''))
        permissions = db_user.get('permissions', [])

        # Get user data from database with defaults
        db_email = db_user.get('email', '')
        user_email = db_email if db_email else f"{user_id}@jhu.edu"

        db_name = db_user.get('name', '')
        user_display_name = db_name if db_name else user_id

        user_roles = db_user.get('roles', [])

        # Build classRoles from class_memberships if classRoles is empty
        if not class_roles and class_memberships:
            class_roles = {}
            for membership in class_memberships:
                if isinstance(membership, dict):
                    class_id = membership.get('class_id')
                    role = membership.get('role')
                    if class_id and role:
                        class_roles[class_id] = role

        # Backward compatibility: if no classRoles but has accessible_classes, build from that
        if not class_roles and accessible_classes:
            # Get role from database or default to instructor for rbarre16
            db_role = db_user.get('role', '').lower()
            if db_role in ['admin', 'instructor']:
                class_roles = {class_id: 'instructor' for class_id in accessible_classes}
            else:
                class_roles = {class_id: 'student' for class_id in accessible_classes}

    # In development mode, generate JWT tokens for the React app
    access_token = None
    refresh_token = None
    if Config.DEBUG:
        # Prepare user data for JWT token generation using database values
        jwt_user_data = {
            'id': user_id,
            'email': user_email,
            'displayName': user_display_name,
            'roles': user_roles,
            'preferred_username': user_email,
            'classRoles': class_roles,  # Include for backward compatibility
            'class_memberships': class_memberships  # Include new format
        }
        access_token = generate_access_token(jwt_user_data)
        refresh_token = generate_refresh_token(user_id)

    # Convert session user to React expected format using database values
    response_data = {
        "success": True,
        "data": {
            "user": {
                "id": user_id,
                "username": user_id,  # Use user_id as username
                "email": user_email,
                "displayName": user_display_name,
                "roles": user_roles,
                "isActive": True,
                "classRoles": class_roles,
                "class_memberships": class_memberships,  # Include new format
                "accessibleClasses": accessible_classes,  # Include for debugging
                "createdAt": created_at,
                "permissions": permissions  # Include actual permissions from database
            },
            "isAuthenticated": True
        }
    }

    # Include impersonation status if currently impersonating
    if session.get('impersonation'):
        response_data["data"]["impersonating"] = True
        response_data["data"]["original_user"] = {
            "id": session['impersonation']['original_user_id'],
            "email": session['impersonation']['original_user_email'],
            "displayName": session['impersonation']['original_user_name']
        }

    # Include JWT tokens in development mode
    if Config.DEBUG and access_token:
        response_data["data"]["accessToken"] = access_token
        response_data["data"]["refreshToken"] = refresh_token

    return jsonify(response_data), 200

@auth_bp.route("/api/users/me", methods=["GET"])
def api_current_user():
    """API endpoint for React frontend to get current user with full details"""
    from flask import jsonify

    # SECURITY FIX: Do NOT auto-login as a specific user
    # Users must authenticate via SSO even in debug mode

    if not session.get("user"):
        return jsonify({
            "success": False,
            "error": "Not authenticated"
        }), 401

    user_data = session["user"]
    # Use 'id' field if present (for impersonation), otherwise extract from preferred_username
    user_id = user_data.get("id") or user_data.get("preferred_username", "").split('@')[0]

    # Get full user data from database to include classRoles
    from informatics_classroom.database.factory import get_database_adapter
    db = get_database_adapter()
    db_user = db.get('users', user_id)

    # Build classRoles from database or default to empty
    class_roles = {}
    class_memberships = []
    accessible_classes = []
    created_at = ''
    permissions = []
    user_email = ''
    user_display_name = ''
    user_roles = []

    if db_user:
        class_roles = db_user.get('classRoles', {})
        class_memberships = db_user.get('class_memberships', [])
        accessible_classes = db_user.get('accessible_classes', [])
        created_at = db_user.get('created_at', db_user.get('createdAt', ''))
        permissions = db_user.get('permissions', [])

        # Get user data from database with defaults
        db_email = db_user.get('email', '')
        user_email = db_email if db_email else f"{user_id}@jhu.edu"

        db_name = db_user.get('name', '')
        user_display_name = db_name if db_name else user_id

        user_roles = db_user.get('roles', [])

        # Build classRoles from class_memberships if classRoles is empty
        if not class_roles and class_memberships:
            class_roles = {}
            for membership in class_memberships:
                if isinstance(membership, dict):
                    class_id = membership.get('class_id')
                    role = membership.get('role')
                    if class_id and role:
                        class_roles[class_id] = role

        # Backward compatibility: if no classRoles but has accessible_classes, build from that
        if not class_roles and accessible_classes:
            # Get role from database or default to instructor for rbarre16
            db_role = db_user.get('role', '').lower()
            if db_role in ['admin', 'instructor']:
                class_roles = {class_id: 'instructor' for class_id in accessible_classes}
            else:
                class_roles = {class_id: 'student' for class_id in accessible_classes}

    response_data = {
        "success": True,
        "data": {
            "id": user_id,
            "username": user_id,  # Use user_id as username
            "email": user_email,
            "displayName": user_display_name,
            "roles": user_roles,  # Use database roles (admin) not session roles
            "isActive": True,
            "classRoles": class_roles,
            "class_memberships": class_memberships,  # Include new format
            "accessibleClasses": accessible_classes,  # Include for debugging
            "createdAt": created_at,
            "permissions": permissions  # Include actual permissions from database
        }
    }

    # Include impersonation status if currently impersonating
    if session.get('impersonation'):
        response_data["data"]["impersonating"] = True
        response_data["data"]["original_user"] = {
            "id": session['impersonation']['original_user_id'],
            "email": session['impersonation']['original_user_email'],
            "displayName": session['impersonation']['original_user_name']
        }

    return jsonify(response_data), 200

@auth_bp.route("/api/dashboard/stats", methods=["GET"])
def api_dashboard_stats():
    """API endpoint for dashboard statistics"""
    from flask import jsonify
    from informatics_classroom.database.factory import get_database_adapter

    # SECURITY FIX: Do NOT auto-login as a specific user

    if not session.get("user"):
        return jsonify({
            "success": False,
            "error": "Not authenticated"
        }), 401

    try:
        db = get_database_adapter()

        # Get counts from database
        users_count = len(db.query('users'))
        quiz_count = len(db.query('quiz'))  # Using 'quiz' not 'quizzes'
        tokens_count = len(db.query('tokens'))
        answers_count = len(db.query('answer'))

        return jsonify({
            "success": True,
            "data": {
                "totalUsers": users_count,
                "activeQuizzes": quiz_count,
                "tokensGenerated": tokens_count,
                "totalAnswers": answers_count
            }
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@auth_bp.route("/api/users", methods=["GET"])
def api_list_users():
    """API endpoint to list all users with pagination"""
    from flask import jsonify, request
    from informatics_classroom.database.factory import get_database_adapter

    # SECURITY FIX: Do NOT auto-login as a specific user

    if not session.get("user"):
        return jsonify({
            "success": False,
            "error": "Not authenticated"
        }), 401

    try:
        db = get_database_adapter()

        # Get pagination parameters
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('pageSize', 10))
        sort_by = request.args.get('sortBy', 'id')
        sort_order = request.args.get('sortOrder', 'asc')

        # Get filter parameters (support both old and new parameter names)
        search = request.args.get('search', '').lower()
        role_filter = request.args.get('role', request.args.get('roleFilter', ''))
        is_active_filter = request.args.get('isActive', request.args.get('isActiveFilter', ''))

        # Get all users from database
        all_users = db.query('users')

        # Apply filters
        filtered_users = all_users

        # Search filter (search in id, displayName, name, email)
        if search:
            filtered_users = [
                user for user in filtered_users
                if (search in user.get('id', '').lower() or
                    search in user.get('displayName', '').lower() or
                    search in user.get('name', '').lower() or
                    search in f"{user.get('id', '')}@jh.edu".lower())
            ]

        # Role filter (supports both global roles and class roles)
        if role_filter:
            def user_has_role(user, role):
                role_lower = role.lower()

                # Check global roles
                user_roles = user.get('roles', [])
                if isinstance(user_roles, str):
                    user_roles = [user_roles]
                if role_lower in [r.lower() for r in user_roles]:
                    return True

                # Check old role field
                if role_lower == user.get('role', '').lower():
                    return True

                # Check class memberships for instructor/ta/student roles
                if role_lower in ['instructor', 'ta', 'student']:
                    class_memberships = user.get('class_memberships', [])
                    for membership in class_memberships:
                        if membership.get('role', '').lower() == role_lower:
                            return True

                    # Also check old classRoles format
                    class_roles = user.get('classRoles', {})
                    if isinstance(class_roles, dict):
                        for class_id, class_role in class_roles.items():
                            if class_role.lower() == role_lower:
                                return True

                return False

            filtered_users = [
                user for user in filtered_users
                if user_has_role(user, role_filter)
            ]

        # Active status filter
        if is_active_filter:
            is_active_bool = is_active_filter.lower() == 'true'
            filtered_users = [
                user for user in filtered_users
                if user.get('isActive', True) == is_active_bool
            ]

        # Sort users
        reverse = (sort_order == 'desc')
        sorted_users = sorted(filtered_users, key=lambda x: x.get(sort_by, ''), reverse=reverse)

        # Calculate pagination
        total = len(sorted_users)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_users = sorted_users[start:end]

        # Format users for React frontend
        formatted_users = []
        for user in paginated_users:
            formatted_users.append({
                "id": user.get('id', ''),
                "username": f"{user.get('id', '')}@jh.edu",
                "email": f"{user.get('id', '')}@jh.edu",
                "displayName": user.get('displayName', user.get('name', user.get('id', ''))),
                "roles": user.get('roles', user.get('role', ['student']) if isinstance(user.get('role'), list) else [user.get('role', 'student')]),
                "isActive": user.get('isActive', True),
                "classRoles": user.get('classRoles', {}),  # Include old format for backward compatibility
                "class_memberships": user.get('class_memberships', []),  # Include new format
                "permissions": user.get('permissions', []),  # Include permissions
                "createdAt": user.get('createdAt', ''),
                "lastLogin": user.get('lastLogin', '')
            })

        return jsonify({
            "success": True,
            "data": {
                "items": formatted_users,
                "page": page,
                "pageSize": page_size,
                "total": total,
                "totalPages": (total + page_size - 1) // page_size
            }
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@auth_bp.route("/api/users/<user_id>", methods=["GET"])
def api_get_user(user_id):
    """API endpoint to get a single user by ID"""
    from flask import jsonify
    from informatics_classroom.database.factory import get_database_adapter

    if not session.get("user"):
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    try:
        db = get_database_adapter()
        user = db.get('users', user_id)

        if not user:
            return jsonify({"success": False, "error": f"User {user_id} not found"}), 404

        # Format user for frontend
        formatted_user = {
            "id": user.get('id', ''),
            "username": user.get('id', ''),
            "email": user.get('email', f"{user.get('id', '')}@jh.edu"),
            "displayName": user.get('displayName', user.get('name', user.get('id', ''))),
            "roles": user.get('roles', ['student']),
            "isActive": user.get('isActive', True),
            "classRoles": user.get('classRoles', {}),
            "class_memberships": user.get('class_memberships', []),
            "permissions": user.get('permissions', []),
            "createdAt": user.get('createdAt', user.get('created_at', '')),
            "lastLogin": user.get('lastLogin', '')
        }

        return jsonify({"success": True, "data": formatted_user}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@auth_bp.route("/api/users/<user_id>", methods=["PUT"])
def api_update_user(user_id):
    """API endpoint to update a user's roles, permissions, and other fields"""
    from flask import jsonify, request
    from informatics_classroom.database.factory import get_database_adapter

    if not session.get("user"):
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    # Check if current user is admin (required to update other users)
    current_user_id = session["user"].get("id") or session["user"].get("preferred_username", "").split("@")[0]
    db = get_database_adapter()
    current_db_user = db.get('users', current_user_id)
    current_roles = current_db_user.get('roles', []) if current_db_user else []

    if 'admin' not in current_roles:
        return jsonify({"success": False, "error": "Admin access required to update users"}), 403

    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        user = db.get('users', user_id)
        if not user:
            return jsonify({"success": False, "error": f"User {user_id} not found"}), 404

        # Update allowed fields
        if 'displayName' in data:
            user['displayName'] = data['displayName']
            user['name'] = data['displayName']  # Keep both in sync
        if 'email' in data:
            user['email'] = data['email']
        if 'role' in data:
            # Single role update - convert to roles array
            user['roles'] = [data['role']]
        if 'roles' in data:
            user['roles'] = data['roles'] if isinstance(data['roles'], list) else [data['roles']]
        if 'isActive' in data:
            user['isActive'] = data['isActive']
        if 'permissions' in data:
            user['permissions'] = data['permissions']

        # Save updated user
        db.upsert('users', user)

        # Format response
        formatted_user = {
            "id": user.get('id', ''),
            "username": user.get('id', ''),
            "email": user.get('email', f"{user.get('id', '')}@jh.edu"),
            "displayName": user.get('displayName', user.get('name', user.get('id', ''))),
            "roles": user.get('roles', ['student']),
            "isActive": user.get('isActive', True),
            "classRoles": user.get('classRoles', {}),
            "class_memberships": user.get('class_memberships', []),
            "permissions": user.get('permissions', []),
            "createdAt": user.get('createdAt', user.get('created_at', '')),
            "lastLogin": user.get('lastLogin', '')
        }

        return jsonify({"success": True, "data": formatted_user}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@auth_bp.route("/api/users/<user_id>", methods=["DELETE"])
def api_delete_user(user_id):
    """API endpoint to delete a user"""
    from flask import jsonify
    from informatics_classroom.database.factory import get_database_adapter

    if not session.get("user"):
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    # Check if current user is admin
    current_user_id = session["user"].get("id") or session["user"].get("preferred_username", "").split("@")[0]
    db = get_database_adapter()
    current_db_user = db.get('users', current_user_id)
    current_roles = current_db_user.get('roles', []) if current_db_user else []

    if 'admin' not in current_roles:
        return jsonify({"success": False, "error": "Admin access required to delete users"}), 403

    # Prevent self-deletion
    if user_id == current_user_id:
        return jsonify({"success": False, "error": "Cannot delete your own account"}), 400

    try:
        user = db.get('users', user_id)
        if not user:
            return jsonify({"success": False, "error": f"User {user_id} not found"}), 404

        db.delete('users', user_id)

        return jsonify({"success": True, "message": f"User {user_id} deleted"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@auth_bp.route("/api/permissions/matrix", methods=["GET"])
def api_permissions_matrix():
    """API endpoint for permissions matrix"""
    from flask import jsonify, request
    from informatics_classroom.database.factory import get_database_adapter

    # SECURITY FIX: Do NOT auto-login as a specific user

    if not session.get("user"):
        return jsonify({
            "success": False,
            "error": "Not authenticated"
        }), 401

    try:
        db = get_database_adapter()

        # Get all users
        all_users = db.query('users', limit=50)  # Limit to 50 for performance

        # Format for permissions matrix
        # Note: In a real system, you'd query actual permissions from a permissions table
        # For now, we'll return a simplified version based on roles
        users_permissions = []
        for user in all_users:
            user_id = user.get('id', '')
            username = f"{user_id}@jh.edu"
            roles = user.get('roles', user.get('role', ['student']))
            if not isinstance(roles, list):
                roles = [roles]

            # Simple permission mapping based on roles
            permissions = {}
            is_admin = 'admin' in [r.lower() for r in roles]
            is_instructor = 'instructor' in [r.lower() for r in roles]

            # Admin gets all permissions
            if is_admin:
                permissions = {
                    'quiz.view': True, 'quiz.create': True, 'quiz.modify': True,
                    'assignment.view': True, 'assignment.create': True,
                    'user.view': True, 'user.manage': True,
                    'system.admin': True, 'system.view_logs': True
                }
            # Instructor gets teaching permissions
            elif is_instructor:
                permissions = {
                    'quiz.view': True, 'quiz.create': True, 'quiz.modify': True,
                    'assignment.view': True, 'assignment.create': True,
                    'user.view': True, 'user.manage': False,
                    'system.admin': False, 'system.view_logs': False
                }
            # Students get basic permissions
            else:
                permissions = {
                    'quiz.view': True, 'quiz.create': False, 'quiz.modify': False,
                    'assignment.view': True, 'assignment.create': False,
                    'user.view': False, 'user.manage': False,
                    'system.admin': False, 'system.view_logs': False
                }

            users_permissions.append({
                "userId": user_id,
                "username": username,
                "permissions": permissions
            })

        return jsonify({
            "success": True,
            "data": {
                "users": users_permissions
            }
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@auth_bp.route("/api/permissions/bulk-grant", methods=["POST"])
def api_bulk_grant_permissions():
    """Bulk grant permissions to multiple users"""
    from flask import jsonify, request
    from informatics_classroom.database.factory import get_database_adapter

    # SECURITY FIX: Do NOT auto-login as a specific user

    if not session.get("user"):
        return jsonify({
            "success": False,
            "error": "Not authenticated"
        }), 401

    # Only admins can bulk grant permissions
    user_roles = session["user"].get("roles", [])
    if "admin" not in user_roles:
        return jsonify({
            "success": False,
            "error": "Only admins can bulk grant permissions"
        }), 403

    data = request.get_json()
    user_ids = data.get("userIds", [])
    permissions = data.get("permissions", [])
    class_id = data.get("classId")

    if not user_ids or not permissions:
        return jsonify({
            "success": False,
            "error": "userIds and permissions are required"
        }), 400

    db = get_database_adapter()
    updated_count = 0

    for user_id in user_ids:
        user = db.get('users', user_id)
        if not user:
            continue

        # If class_id is specified, update classRoles
        if class_id:
            class_roles = user.get('classRoles', {})
            if not isinstance(class_roles, dict):
                class_roles = {}

            # Map permissions to role
            # For now, grant instructor role if any permissions are granted
            if permissions:
                class_roles[class_id] = 'instructor'

            user['classRoles'] = class_roles
        else:
            # Update global roles
            current_roles = user.get('roles', [])
            if not isinstance(current_roles, list):
                current_roles = []

            # Add instructor role if not present
            if 'instructor' not in current_roles:
                current_roles.append('instructor')

            user['roles'] = current_roles

        db.update('users', user_id, user)
        updated_count += 1

    return jsonify({
        "success": True,
        "data": {
            "updated": updated_count
        }
    }), 200

@auth_bp.route("/api/permissions/bulk-revoke", methods=["POST"])
def api_bulk_revoke_permissions():
    """Bulk revoke permissions from multiple users"""
    from flask import jsonify, request
    from informatics_classroom.database.factory import get_database_adapter

    # SECURITY FIX: Do NOT auto-login as a specific user

    if not session.get("user"):
        return jsonify({
            "success": False,
            "error": "Not authenticated"
        }), 401

    # Only admins can bulk revoke permissions
    user_roles = session["user"].get("roles", [])
    if "admin" not in user_roles:
        return jsonify({
            "success": False,
            "error": "Only admins can bulk revoke permissions"
        }), 403

    data = request.get_json()
    user_ids = data.get("userIds", [])
    permissions = data.get("permissions", [])
    class_id = data.get("classId")

    if not user_ids or not permissions:
        return jsonify({
            "success": False,
            "error": "userIds and permissions are required"
        }), 400

    db = get_database_adapter()
    updated_count = 0

    for user_id in user_ids:
        user = db.get('users', user_id)
        if not user:
            continue

        # If class_id is specified, update classRoles
        if class_id:
            class_roles = user.get('classRoles', {})
            if isinstance(class_roles, dict) and class_id in class_roles:
                # Remove the class role
                del class_roles[class_id]
                user['classRoles'] = class_roles
        else:
            # Update global roles - revert to student
            user['roles'] = ['student']

        db.update('users', user_id, user)
        updated_count += 1

    return jsonify({
        "success": True,
        "data": {
            "updated": updated_count
        }
    }), 200

@auth_bp.route("/logout")
def logout():
    session.clear()  # Wipe out user and its token cache from session
    return redirect(  # Also logout from your tenant's web session
        Config.AUTHORITY + "/oauth2/v2.0/logout" +
        "?post_logout_redirect_uri=" + url_for("auth_bp.index", _external=True))

@auth_bp.route("/graphcall")
def graphcall():
    token = _get_token_from_cache(Config.SCOPE)
    if not token:
        return redirect(url_for("auth_bp.login"))
    graph_data = requests.get(  # Use token to call downstream service
        Config.ENDPOINT,
        headers={'Authorization': 'Bearer ' + token['access_token']},
        ).json()
    return render_template('display.html', result=graph_data)


def _load_cache():
    cache = msal.SerializableTokenCache()
    if session.get("token_cache"):
        cache.deserialize(session["token_cache"])
    return cache

def _save_cache(cache):
    if cache.has_state_changed:
        session["token_cache"] = cache.serialize()

def _build_msal_app(cache=None, authority=None):
    return msal.ConfidentialClientApplication(
        Config.CLIENT_ID, authority=authority or Config.AUTHORITY,
        client_credential=Config.CLIENT_SECRET, token_cache=cache)

def _build_auth_code_flow(authority=None, scopes=None):
    return _build_msal_app(authority=authority).initiate_auth_code_flow(
        scopes or [],
        redirect_uri=url_for("auth_bp.authorized", _external=True))

def _get_token_from_cache(scope=None):
    cache = _load_cache()  # This web app maintains one cache per session
    cca = _build_msal_app(cache=cache)
    accounts = cca.get_accounts()
    if accounts:  # So all account(s) belong to the current signed-in user
        result = cca.acquire_token_silent(scope, account=accounts[0])
        _save_cache(cache)
        return result

