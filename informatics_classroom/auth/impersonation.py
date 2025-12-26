"""
Admin User Impersonation API

Allows administrators to view the application as another user for testing
and support purposes. Maintains audit trail of impersonation sessions.
"""

from flask import jsonify, request, session
from informatics_classroom.auth import auth_bp
from informatics_classroom.auth.jwt_utils import require_jwt_token, decode_token, generate_access_token
from informatics_classroom.database.factory import get_database_adapter
from functools import wraps
from typing import Optional, Dict, Any
import sys


def require_admin(f):
    """Decorator to require admin role for impersonation endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from informatics_classroom.config import Config

        # SECURITY FIX: Do NOT auto-create sessions or escalate privileges
        # Even in debug mode, admin endpoints require proper authentication
        if Config.DEBUG:
            if not session.get("user"):
                # No session - require authentication
                print(f"DEBUG - require_admin: No session, authentication required", file=sys.stderr)
                return jsonify({"error": "Authentication required. Please log in via SSO."}), 401
            elif not session["user"].get("roles"):
                # Incomplete session - look up roles from database
                user_id = session["user"].get("id") or session["user"].get("preferred_username", "").split('@')[0]
                print(f"DEBUG - require_admin: Looking up roles for user {user_id}", file=sys.stderr)
                db = get_database_adapter()
                db_user = db.get('users', user_id)
                if db_user:
                    session["user"]["roles"] = db_user.get('roles', ['student'])
                else:
                    session["user"]["roles"] = ['student']

        # Helper to check database roles (source of truth for admin status)
        def check_db_admin(user_id: str) -> bool:
            """Check if user has admin role in database"""
            db = get_database_adapter()
            db_user = db.get('users', user_id)
            if db_user:
                db_roles = db_user.get('roles', [])
                return 'admin' in db_roles
            return False

        # Check JWT token
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if token:
            try:
                payload = decode_token(token)
                user_id = payload.get('user_id') or payload.get('sub', '').split('@')[0]
                roles = payload.get('roles', [])

                # Check JWT roles first, then fallback to database (handles token refresh issues)
                if 'admin' not in roles:
                    # JWT might be stale, check database as source of truth
                    if not check_db_admin(user_id):
                        return jsonify({"error": "Admin access required"}), 403
            except Exception as e:
                return jsonify({"error": "Invalid token"}), 401
        # Check session (development mode)
        elif session.get('user'):
            user_data = session['user']
            user_id = user_data.get('id') or user_data.get('preferred_username', '').split('@')[0]
            roles = user_data.get('roles', [])

            # Check if impersonating - use original user's roles
            if session.get('impersonation'):
                roles = session['impersonation'].get('original_user_roles', [])

            # Check session roles first, then fallback to database
            if 'admin' not in roles:
                if not check_db_admin(user_id):
                    return jsonify({"error": "Admin access required"}), 403
        else:
            return jsonify({"error": "Not authenticated"}), 401

        return f(*args, **kwargs)
    return decorated_function


@auth_bp.route("/api/admin/users", methods=["GET"])
@require_admin
def get_users_for_impersonation():
    """
    Get list of all users for admin impersonation selection.

    Returns:
        JSON with list of users containing id, email, name, and roles
    """
    db = get_database_adapter()

    # Query all users
    users = db.query('users', limit=1000, order_by='id')

    # Format user data for frontend
    user_list = []
    for user in users:
        user_list.append({
            'id': user.get('id'),
            'email': user.get('email', user.get('id') + '@jh.edu'),
            'displayName': user.get('name', user.get('id')),
            'roles': user.get('roles', ['student']),
            'classRoles': user.get('classRoles', {}),
            'class_memberships': user.get('class_memberships', [])
        })

    return jsonify({
        'success': True,
        'users': user_list
    }), 200


@auth_bp.route("/api/admin/impersonate", methods=["POST"])
@require_admin
def start_impersonation():
    """
    Start impersonating another user.

    Stores original user info and switches session to target user.

    Request Body:
        {
            "user_id": "target_user_id"
        }

    Returns:
        JSON with impersonated user information and new access token
    """
    data = request.get_json()
    target_user_id = data.get('user_id')

    if not target_user_id:
        return jsonify({
            'success': False,
            'error': 'user_id required'
        }), 400

    db = get_database_adapter()
    target_user = db.get('users', target_user_id)

    if not target_user:
        return jsonify({
            'success': False,
            'error': 'User not found'
        }), 404

    # Store original user information
    original_user = session.get('user')
    if not original_user:
        # Get from JWT token
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if token:
            try:
                payload = decode_token(token)
                original_user = {
                    'id': payload.get('user_id'),
                    'email': payload.get('email'),
                    'displayName': payload.get('display_name'),
                    'roles': payload.get('roles', [])
                }
            except:
                return jsonify({'error': 'Invalid authentication'}), 401

    # Check if already impersonating
    if session.get('impersonation'):
        return jsonify({
            'success': False,
            'error': 'Already impersonating a user. Stop current impersonation first.'
        }), 400

    # Set up impersonation
    session['impersonation'] = {
        'original_user_id': original_user.get('id') if isinstance(original_user, dict) else original_user.get('preferred_username', '').split('@')[0],
        'original_user_email': original_user.get('email') if isinstance(original_user, dict) else original_user.get('preferred_username'),
        'original_user_name': original_user.get('displayName') if isinstance(original_user, dict) else original_user.get('name'),
        'original_user_roles': original_user.get('roles', ['admin']),
        'target_user_id': target_user_id,
        'started_at': str(__import__('datetime').datetime.utcnow())
    }

    # Switch session to target user
    session['user'] = {
        'preferred_username': target_user.get('email', target_user_id + '@jh.edu'),
        'name': target_user.get('name', target_user_id),
        'email': target_user.get('email', target_user_id + '@jh.edu'),
        'roles': target_user.get('roles', ['student']),
        'id': target_user_id
    }

    # Generate new JWT token for impersonated user
    jwt_user_data = {
        'id': target_user_id,
        'email': target_user.get('email', target_user_id + '@jh.edu'),
        'displayName': target_user.get('name', target_user_id),
        'roles': target_user.get('roles', ['student']),
        'preferred_username': target_user.get('email', target_user_id + '@jh.edu'),
        '_impersonating': True,  # Flag to indicate this is an impersonation token
        '_original_user_id': session['impersonation']['original_user_id']
    }

    access_token = generate_access_token(jwt_user_data)

    return jsonify({
        'success': True,
        'impersonating': True,
        'original_user': {
            'id': session['impersonation']['original_user_id'],
            'email': session['impersonation']['original_user_email'],
            'displayName': session['impersonation']['original_user_name']
        },
        'current_user': {
            'id': target_user_id,
            'email': target_user.get('email', target_user_id + '@jh.edu'),
            'displayName': target_user.get('name', target_user_id),
            'roles': target_user.get('roles', ['student']),
            'classRoles': target_user.get('classRoles', {}),
            'class_memberships': target_user.get('class_memberships', []),
            'accessible_classes': target_user.get('accessible_classes', [])
        },
        'accessToken': access_token
    }), 200


@auth_bp.route("/api/admin/stop-impersonate", methods=["POST"])
def stop_impersonation():
    """
    Stop impersonating and restore original user session.

    Returns:
        JSON with restored original user information
    """
    impersonation = session.get('impersonation')

    if not impersonation:
        return jsonify({
            'success': False,
            'error': 'Not currently impersonating'
        }), 400

    db = get_database_adapter()

    # Restore original user
    original_user_id = impersonation['original_user_id']
    original_user = db.get('users', original_user_id)

    # SECURITY FIX: Always fetch current roles from database, not stored impersonation data
    # This ensures that if the admin's role was revoked during impersonation,
    # they don't retain their old permissions
    if original_user:
        # Use CURRENT database roles, not stored impersonation roles
        current_roles = original_user.get('roles', ['student'])
        session['user'] = {
            'preferred_username': original_user.get('email', original_user_id + '@jh.edu'),
            'name': original_user.get('name', impersonation['original_user_name']),
            'email': original_user.get('email', impersonation['original_user_email']),
            'roles': current_roles,  # Use current DB roles, not stale stored roles
            'id': original_user_id
        }
    else:
        # User no longer exists in database - deny access
        import logging
        logging.warning(f"Impersonation stop failed: original user {original_user_id} not found in database")
        del session['impersonation']
        session.clear()
        return jsonify({
            'success': False,
            'error': 'Original user no longer exists'
        }), 401

    # Clear impersonation
    del session['impersonation']

    # Generate new JWT token for original user with CURRENT database roles
    user_data = session['user']
    jwt_user_data = {
        'id': user_data.get('id', original_user_id),
        'email': user_data.get('email'),
        'displayName': user_data.get('name'),
        'roles': current_roles,  # Use DB roles directly, not from session with unsafe default
        'preferred_username': user_data.get('preferred_username')
    }

    access_token = generate_access_token(jwt_user_data)

    # Get full user data
    class_roles = {}
    class_memberships = []
    accessible_classes = []

    if original_user:
        class_roles = original_user.get('classRoles', {})
        class_memberships = original_user.get('class_memberships', [])
        accessible_classes = original_user.get('accessible_classes', [])

    return jsonify({
        'success': True,
        'impersonating': False,
        'user': {
            'id': original_user_id,
            'email': user_data.get('email'),
            'displayName': user_data.get('name'),
            'roles': user_data.get('roles', ['admin']),
            'classRoles': class_roles,
            'class_memberships': class_memberships,
            'accessible_classes': accessible_classes
        },
        'accessToken': access_token
    }), 200


@auth_bp.route("/api/admin/impersonation-status", methods=["GET"])
def get_impersonation_status():
    """
    Get current impersonation status.

    Returns:
        JSON with impersonation status and user information
    """
    impersonation = session.get('impersonation')

    if not impersonation:
        return jsonify({
            'success': True,
            'impersonating': False
        }), 200

    current_user = session.get('user', {})

    return jsonify({
        'success': True,
        'impersonating': True,
        'original_user': {
            'id': impersonation['original_user_id'],
            'email': impersonation['original_user_email'],
            'displayName': impersonation['original_user_name']
        },
        'current_user': {
            'id': current_user.get('id', impersonation['target_user_id']),
            'email': current_user.get('email'),
            'displayName': current_user.get('name'),
            'roles': current_user.get('roles', [])
        },
        'started_at': impersonation['started_at']
    }), 200
