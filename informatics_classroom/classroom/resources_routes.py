"""
Resources management routes for ExCITE portal.

Handles flexible resource management including applications, videos, documents,
wikis, links, datasets, and extensible content types.
"""

from flask import request, jsonify
from informatics_classroom.auth.jwt_utils import require_jwt_token, require_role
from informatics_classroom.auth.class_auth import require_class_role, user_has_class_permission
from informatics_classroom.database.factory import get_database_adapter
from informatics_classroom.classroom.routes import get_classes_for_user
from informatics_classroom.classroom import classroom_bp
import uuid
from datetime import datetime


# ========== HELPER FUNCTIONS ==========

def validate_resource_data(data, require_all=True):
    """
    Validate resource data.

    Args:
        data: Resource data dictionary
        require_all: If True, require all fields. If False, allow partial updates.

    Returns:
        tuple: (is_valid, error_message)
    """
    if require_all:
        required_fields = ['name', 'description', 'resource_type', 'url', 'category']
        for field in required_fields:
            if field not in data or not data[field]:
                return False, f'Missing required field: {field}'

    # Validate resource type
    valid_types = ['application', 'video', 'document', 'link', 'wiki', 'dataset', 'other']
    if 'resource_type' in data and data['resource_type'] not in valid_types:
        return False, f'Invalid resource_type. Must be one of: {", ".join(valid_types)}'

    # Validate category (flexible - any string allowed for extensibility)
    if 'category' in data and not isinstance(data['category'], str):
        return False, 'Category must be a string'

    # Validate URL format (basic check)
    if 'url' in data and data['url']:
        url = data['url'].strip()
        if not (url.startswith('http://') or url.startswith('https://')):
            return False, 'URL must start with http:// or https://'

    # Validate order if present
    if 'order' in data:
        try:
            int(data['order'])
        except (ValueError, TypeError):
            return False, 'Order must be an integer'

    # Validate metadata if present
    if 'metadata' in data and not isinstance(data['metadata'], dict):
        return False, 'Metadata must be a dictionary'

    return True, None


def get_user_accessible_resources(user_id):
    """
    Get all resources accessible to a user (general + course-specific for their courses).

    Args:
        user_id: User ID

    Returns:
        dict: {'general': [...], 'course_specific': {course_id: [...]}}
    """
    db = get_database_adapter()

    # Get user's courses
    user_courses = get_classes_for_user(user_id)

    # Get all active resources
    all_resources = db.query('resources', filters={'is_active': True})

    general_resources = []
    course_resources = {course: [] for course in user_courses}

    for resource in all_resources:
        course_specific = resource.get('course_specific')

        if course_specific is None:
            # General resource
            general_resources.append(resource)
        elif course_specific in user_courses:
            # Course-specific resource for user's course
            course_resources[course_specific].append(resource)

    # Sort by order
    general_resources.sort(key=lambda r: r.get('order', 999))
    for course in course_resources:
        course_resources[course].sort(key=lambda r: r.get('order', 999))

    return {
        'general': general_resources,
        'course_specific': course_resources
    }


# ========== PUBLIC/STUDENT ENDPOINTS ==========

@classroom_bp.route('/api/resources', methods=['GET'])
@require_jwt_token
def api_get_resources():
    """
    Get all accessible resources for the current user.

    Query params:
        course: Optional course filter
        type: Optional resource_type filter
        category: Optional category filter

    Returns:
        JSON with general and course-specific resources
    """
    try:
        user_id = request.jwt_user.get('user_id') or request.jwt_user.get('email', '').split('@')[0]

        # Get all accessible resources
        resources_data = get_user_accessible_resources(user_id)

        # Apply filters
        course_filter = request.args.get('course')
        type_filter = request.args.get('type')
        category_filter = request.args.get('category')

        if type_filter:
            resources_data['general'] = [r for r in resources_data['general'] if r.get('resource_type') == type_filter]
            for course in resources_data['course_specific']:
                resources_data['course_specific'][course] = [
                    r for r in resources_data['course_specific'][course]
                    if r.get('resource_type') == type_filter
                ]

        if category_filter:
            resources_data['general'] = [r for r in resources_data['general'] if r.get('category') == category_filter]
            for course in resources_data['course_specific']:
                resources_data['course_specific'][course] = [
                    r for r in resources_data['course_specific'][course]
                    if r.get('category') == category_filter
                ]

        if course_filter:
            # Filter to only show specific course
            if course_filter in resources_data['course_specific']:
                resources_data['course_specific'] = {course_filter: resources_data['course_specific'][course_filter]}
            else:
                resources_data['course_specific'] = {}

        return jsonify({
            'success': True,
            'general': resources_data['general'],
            'course_specific': resources_data['course_specific']
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@classroom_bp.route('/api/resources/<resource_id>', methods=['GET'])
@require_jwt_token
def api_get_resource(resource_id):
    """
    Get single resource details.

    Returns:
        JSON with resource data
    """
    try:
        db = get_database_adapter()
        resource = db.get('resources', resource_id)

        if not resource:
            return jsonify({
                'success': False,
                'error': 'Resource not found'
            }), 404

        return jsonify({
            'success': True,
            'resource': resource
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ========== ADMIN ENDPOINTS ==========

@classroom_bp.route('/api/resources/admin', methods=['GET'])
@require_jwt_token
@require_role(['admin'])
def api_get_all_resources_admin():
    """
    Get all resources for admin management.

    Query params:
        type: Optional resource_type filter
        category: Optional category filter

    Returns:
        JSON with all resources and statistics
    """
    try:
        db = get_database_adapter()

        # Get all resources (including inactive)
        all_resources = db.query('resources', filters={})

        # Apply filters
        type_filter = request.args.get('type')
        category_filter = request.args.get('category')

        if type_filter:
            all_resources = [r for r in all_resources if r.get('resource_type') == type_filter]

        if category_filter:
            all_resources = [r for r in all_resources if r.get('category') == category_filter]

        # Calculate statistics
        stats = {
            'total': len(all_resources),
            'by_type': {},
            'by_category': {},
            'active': sum(1 for r in all_resources if r.get('is_active', True)),
            'inactive': sum(1 for r in all_resources if not r.get('is_active', True))
        }

        for resource in all_resources:
            rtype = resource.get('resource_type', 'other')
            category = resource.get('category', 'other')

            stats['by_type'][rtype] = stats['by_type'].get(rtype, 0) + 1
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1

        # Sort by order
        all_resources.sort(key=lambda r: (r.get('course_specific') or '', r.get('order', 999)))

        return jsonify({
            'success': True,
            'resources': all_resources,
            'stats': stats
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@classroom_bp.route('/api/resources/admin', methods=['POST'])
@require_jwt_token
@require_role(['admin'])
def api_create_general_resource():
    """
    Create a new general resource (visible to all users).

    Request body:
        name: Resource name
        description: Description
        resource_type: Type (application, video, document, link, wiki, dataset, other)
        url: Resource URL
        icon: Optional icon name
        category: Category
        order: Display order
        is_active: Active status
        metadata: Type-specific metadata

    Returns:
        JSON with created resource
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        # Validate data
        is_valid, error_msg = validate_resource_data(data, require_all=True)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400

        # Create resource
        user_id = request.jwt_user.get('user_id') or request.jwt_user.get('email', '').split('@')[0]

        resource = {
            'id': data.get('id', str(uuid.uuid4())),
            'name': data['name'],
            'description': data['description'],
            'resource_type': data['resource_type'],
            'url': data['url'],
            'icon': data.get('icon', ''),
            'category': data['category'],
            'order': int(data.get('order', 999)),
            'is_active': data.get('is_active', True),
            'course_specific': None,  # General resource
            'metadata': data.get('metadata', {}),
            'created_by': user_id,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }

        db = get_database_adapter()
        db.upsert('resources', resource)

        return jsonify({
            'success': True,
            'resource': resource
        }), 201

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@classroom_bp.route('/api/resources/admin/<resource_id>', methods=['PUT'])
@require_jwt_token
@require_role(['admin'])
def api_update_general_resource(resource_id):
    """
    Update a general resource.

    Request body:
        Partial resource data to update

    Returns:
        JSON with updated resource
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        # Validate data
        is_valid, error_msg = validate_resource_data(data, require_all=False)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400

        db = get_database_adapter()
        existing_resource = db.get('resources', resource_id)

        if not existing_resource:
            return jsonify({
                'success': False,
                'error': 'Resource not found'
            }), 404

        # Only allow updating general resources (not course-specific)
        if existing_resource.get('course_specific') is not None:
            return jsonify({
                'success': False,
                'error': 'Cannot update course-specific resources through admin endpoint'
            }), 403

        # Update fields
        for key in ['name', 'description', 'resource_type', 'url', 'icon', 'category', 'order', 'is_active', 'metadata']:
            if key in data:
                existing_resource[key] = data[key]

        existing_resource['updated_at'] = datetime.utcnow().isoformat()

        db.upsert('resources', existing_resource)

        return jsonify({
            'success': True,
            'resource': existing_resource
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@classroom_bp.route('/api/resources/admin/<resource_id>', methods=['DELETE'])
@require_jwt_token
@require_role(['admin'])
def api_delete_general_resource(resource_id):
    """
    Delete a general resource.

    Returns:
        JSON with success status
    """
    try:
        db = get_database_adapter()
        existing_resource = db.get('resources', resource_id)

        if not existing_resource:
            return jsonify({
                'success': False,
                'error': 'Resource not found'
            }), 404

        # Only allow deleting general resources (not course-specific)
        if existing_resource.get('course_specific') is not None:
            return jsonify({
                'success': False,
                'error': 'Cannot delete course-specific resources through admin endpoint'
            }), 403

        db.delete('resources', resource_id)

        return jsonify({
            'success': True
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@classroom_bp.route('/api/resources/admin/categories', methods=['GET'])
@require_jwt_token
@require_role(['admin'])
def api_get_categories():
    """
    Get all resource categories with counts.

    Returns:
        JSON with categories and resource counts
    """
    try:
        db = get_database_adapter()
        all_resources = db.query('resources', filters={})

        # Count resources by category
        category_counts = {}
        for resource in all_resources:
            category = resource.get('category', 'other')
            category_counts[category] = category_counts.get(category, 0) + 1

        # Build category list
        categories = [
            {'id': cat, 'name': cat.replace('_', ' ').title(), 'count': count}
            for cat, count in category_counts.items()
        ]

        # Sort by count descending
        categories.sort(key=lambda c: c['count'], reverse=True)

        return jsonify({
            'success': True,
            'categories': categories
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ========== COURSE-SPECIFIC ENDPOINTS ==========

@classroom_bp.route('/api/resources/course/<course_id>', methods=['GET'])
@require_jwt_token
def api_get_course_resources(course_id):
    """
    Get resources for a specific course.

    Query params:
        type: Optional resource_type filter
        category: Optional category filter

    Returns:
        JSON with course resources
    """
    try:
        db = get_database_adapter()

        # Get course-specific resources
        course_resources = db.query('resources', filters={
            'course_specific': course_id,
            'is_active': True
        })

        # Apply filters
        type_filter = request.args.get('type')
        category_filter = request.args.get('category')

        if type_filter:
            course_resources = [r for r in course_resources if r.get('resource_type') == type_filter]

        if category_filter:
            course_resources = [r for r in course_resources if r.get('category') == category_filter]

        # Sort by order
        course_resources.sort(key=lambda r: r.get('order', 999))

        return jsonify({
            'success': True,
            'resources': course_resources
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@classroom_bp.route('/api/resources/course/<course_id>', methods=['POST'])
@require_jwt_token
def api_create_course_resource(course_id):
    """
    Create a course-specific resource.
    Requires instructor or TA role in the course.

    Request body:
        name: Resource name
        description: Description
        resource_type: Type
        url: Resource URL
        icon: Optional icon name
        category: Category
        order: Display order
        is_active: Active status
        metadata: Type-specific metadata

    Returns:
        JSON with created resource
    """
    try:
        # Check permission
        current_user = request.jwt_user
        if not user_has_class_permission(current_user, course_id, 'manage_quizzes'):
            return jsonify({
                'success': False,
                'error': 'Insufficient permissions to manage resources for this course'
            }), 403

        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        # Validate data
        is_valid, error_msg = validate_resource_data(data, require_all=True)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400

        # Create resource
        user_id = request.jwt_user.get('user_id') or request.jwt_user.get('email', '').split('@')[0]

        resource = {
            'id': data.get('id', str(uuid.uuid4())),
            'name': data['name'],
            'description': data['description'],
            'resource_type': data['resource_type'],
            'url': data['url'],
            'icon': data.get('icon', ''),
            'category': data['category'],
            'order': int(data.get('order', 999)),
            'is_active': data.get('is_active', True),
            'course_specific': course_id,  # Course-specific
            'metadata': data.get('metadata', {}),
            'created_by': user_id,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }

        db = get_database_adapter()
        db.upsert('resources', resource)

        return jsonify({
            'success': True,
            'resource': resource
        }), 201

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@classroom_bp.route('/api/resources/course/<course_id>/<resource_id>', methods=['PUT'])
@require_jwt_token
def api_update_course_resource(course_id, resource_id):
    """
    Update a course-specific resource.
    Requires instructor or TA role in the course.

    Request body:
        Partial resource data to update

    Returns:
        JSON with updated resource
    """
    try:
        # Check permission
        current_user = request.jwt_user
        if not user_has_class_permission(current_user, course_id, 'manage_quizzes'):
            return jsonify({
                'success': False,
                'error': 'Insufficient permissions to manage resources for this course'
            }), 403

        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        # Validate data
        is_valid, error_msg = validate_resource_data(data, require_all=False)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400

        db = get_database_adapter()
        existing_resource = db.get('resources', resource_id)

        if not existing_resource:
            return jsonify({
                'success': False,
                'error': 'Resource not found'
            }), 404

        # Verify resource belongs to this course
        if existing_resource.get('course_specific') != course_id:
            return jsonify({
                'success': False,
                'error': 'Resource does not belong to this course'
            }), 403

        # Update fields
        for key in ['name', 'description', 'resource_type', 'url', 'icon', 'category', 'order', 'is_active', 'metadata']:
            if key in data:
                existing_resource[key] = data[key]

        existing_resource['updated_at'] = datetime.utcnow().isoformat()

        db.upsert('resources', existing_resource)

        return jsonify({
            'success': True,
            'resource': existing_resource
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@classroom_bp.route('/api/resources/course/<course_id>/<resource_id>', methods=['DELETE'])
@require_jwt_token
def api_delete_course_resource(course_id, resource_id):
    """
    Delete a course-specific resource.
    Requires instructor or TA role in the course.

    Returns:
        JSON with success status
    """
    try:
        # Check permission
        current_user = request.jwt_user
        if not user_has_class_permission(current_user, course_id, 'manage_quizzes'):
            return jsonify({
                'success': False,
                'error': 'Insufficient permissions to manage resources for this course'
            }), 403

        db = get_database_adapter()
        existing_resource = db.get('resources', resource_id)

        if not existing_resource:
            return jsonify({
                'success': False,
                'error': 'Resource not found'
            }), 404

        # Verify resource belongs to this course
        if existing_resource.get('course_specific') != course_id:
            return jsonify({
                'success': False,
                'error': 'Resource does not belong to this course'
            }), 403

        db.delete('resources', resource_id)

        return jsonify({
            'success': True
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@classroom_bp.route('/api/resources/course/<course_id>/stats', methods=['GET'])
@require_jwt_token
def api_get_course_resource_stats(course_id):
    """
    Get resource statistics for a course.
    Requires instructor or TA role in the course.

    Returns:
        JSON with statistics
    """
    try:
        # Check permission
        current_user = request.jwt_user
        if not user_has_class_permission(current_user, course_id, 'manage_quizzes'):
            return jsonify({
                'success': False,
                'error': 'Insufficient permissions to view stats for this course'
            }), 403

        db = get_database_adapter()
        course_resources = db.query('resources', filters={'course_specific': course_id})

        # Calculate statistics
        stats = {
            'total': len(course_resources),
            'by_type': {},
            'by_category': {},
            'active': sum(1 for r in course_resources if r.get('is_active', True)),
            'inactive': sum(1 for r in course_resources if not r.get('is_active', True))
        }

        for resource in course_resources:
            rtype = resource.get('resource_type', 'other')
            category = resource.get('category', 'other')

            stats['by_type'][rtype] = stats['by_type'].get(rtype, 0) + 1
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1

        return jsonify({
            'success': True,
            'stats': stats
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ========== SEED DEFAULT RESOURCES ==========

def seed_default_resources():
    """
    Seeds default ExCITE suite resources and sample educational materials if they don't exist.

    Returns:
        dict: Summary of seeding operation
    """
    db = get_database_adapter()

    # Define default resources for ExCITE suite and sample materials
    default_resources = [
        # ========== CORE EXCITE TOOLS ==========
        {
            'id': 'wintehr-default',
            'name': 'WintEHR',
            'description': 'Electronic Health Record system for healthcare informatics education and research',
            'resource_type': 'application',
            'url': 'https://wintehr.excite.example.edu',
            'icon': 'DocumentTextIcon',
            'category': 'core_tools',
            'order': 1,
            'is_active': True,
            'course_specific': None,
            'metadata': {
                'requires_auth': True,
                'default_credentials_available': True,
                'documentation': '/docs/wintehr',
                'version': '2.0'
            },
            'created_by': 'system',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        },
        {
            'id': 'broadsea-default',
            'name': 'Broadsea',
            'description': 'OHDSI tools suite for observational health data analytics and standardization',
            'resource_type': 'application',
            'url': 'https://broadsea.excite.example.edu',
            'icon': 'ChartBarIcon',
            'category': 'core_tools',
            'order': 2,
            'is_active': True,
            'course_specific': None,
            'metadata': {
                'requires_auth': True,
                'includes_tools': ['ATLAS', 'ACHILLES', 'HADES'],
                'documentation': '/docs/broadsea',
                'version': '3.5'
            },
            'created_by': 'system',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        },
        {
            'id': 'jupyterhub-default',
            'name': 'JupyterHub',
            'description': 'Interactive notebook environment for data analysis, visualization, and collaborative computing',
            'resource_type': 'application',
            'url': 'https://jupyter.excite.example.edu',
            'icon': 'CodeBracketIcon',
            'category': 'core_tools',
            'order': 3,
            'is_active': True,
            'course_specific': None,
            'metadata': {
                'requires_auth': True,
                'supported_kernels': ['Python', 'R', 'Julia'],
                'documentation': '/docs/jupyterhub',
                'version': '4.0'
            },
            'created_by': 'system',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        },

        # ========== TUTORIALS ==========
        {
            'id': 'tutorial-intro-ehr',
            'name': 'Introduction to Electronic Health Records',
            'description': 'Comprehensive video tutorial covering EHR fundamentals, data standards, and clinical workflows',
            'resource_type': 'video',
            'url': 'https://videos.excite.example.edu/intro-to-ehr',
            'icon': 'VideoIcon',
            'category': 'tutorials',
            'order': 1,
            'is_active': True,
            'course_specific': None,
            'metadata': {
                'duration': 2400,
                'author': 'Dr. Sarah Johnson',
                'published_date': '2024-01-15',
                'playlist': 'Healthcare Informatics Fundamentals'
            },
            'created_by': 'system',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        },
        {
            'id': 'tutorial-ohdsi-basics',
            'name': 'OHDSI OMOP CDM Tutorial',
            'description': 'Learn the basics of the OMOP Common Data Model and OHDSI tools for observational research',
            'resource_type': 'video',
            'url': 'https://videos.excite.example.edu/ohdsi-omop-basics',
            'icon': 'VideoIcon',
            'category': 'tutorials',
            'order': 2,
            'is_active': True,
            'course_specific': None,
            'metadata': {
                'duration': 3600,
                'author': 'OHDSI Community',
                'published_date': '2024-02-01',
                'playlist': 'OHDSI Learning Series'
            },
            'created_by': 'system',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        },

        # ========== DOCUMENTATION ==========
        {
            'id': 'doc-fhir-guide',
            'name': 'FHIR Implementation Guide',
            'description': 'Complete guide to implementing HL7 FHIR standards for healthcare data exchange',
            'resource_type': 'document',
            'url': 'https://docs.excite.example.edu/fhir-implementation-guide.pdf',
            'icon': 'DocumentIcon',
            'category': 'documentation',
            'order': 1,
            'is_active': True,
            'course_specific': None,
            'metadata': {
                'file_type': 'PDF',
                'file_size': 2500000,
                'pages': 150,
                'author': 'HL7 International',
                'last_updated': '2024-03-01',
                'language': 'English'
            },
            'created_by': 'system',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        },
        {
            'id': 'doc-python-health-analytics',
            'name': 'Python for Healthcare Analytics',
            'description': 'Practical guide to using Python for healthcare data analysis and visualization',
            'resource_type': 'document',
            'url': 'https://docs.excite.example.edu/python-healthcare-analytics.pdf',
            'icon': 'DocumentIcon',
            'category': 'documentation',
            'order': 2,
            'is_active': True,
            'course_specific': None,
            'metadata': {
                'file_type': 'PDF',
                'file_size': 3200000,
                'pages': 200,
                'author': 'Dr. Michael Chen',
                'last_updated': '2024-02-15',
                'language': 'English'
            },
            'created_by': 'system',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        },

        # ========== DATASETS ==========
        {
            'id': 'dataset-mimic-demo',
            'name': 'MIMIC-III Demo Dataset',
            'description': 'De-identified demo dataset from MIMIC-III for learning clinical database analysis',
            'resource_type': 'dataset',
            'url': 'https://data.excite.example.edu/mimic-iii-demo',
            'icon': 'DatabaseIcon',
            'category': 'datasets',
            'order': 1,
            'is_active': True,
            'course_specific': None,
            'metadata': {
                'dataset_size': '100 patients, ~500MB',
                'format': 'CSV, Parquet',
                'license': 'PhysioNet Credentialed Health Data License'
            },
            'created_by': 'system',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        },
        {
            'id': 'dataset-synthea-sample',
            'name': 'Synthea Synthetic Patients',
            'description': 'Realistic synthetic patient data generated with Synthea for practice and testing',
            'resource_type': 'dataset',
            'url': 'https://data.excite.example.edu/synthea-sample',
            'icon': 'DatabaseIcon',
            'category': 'datasets',
            'order': 2,
            'is_active': True,
            'course_specific': None,
            'metadata': {
                'dataset_size': '1,000 patients, ~250MB',
                'format': 'FHIR JSON, CSV',
                'license': 'Apache 2.0'
            },
            'created_by': 'system',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        },

        # ========== PROJECTS ==========
        {
            'id': 'project-ehr-dashboard',
            'name': 'EHR Analytics Dashboard',
            'description': 'Sample project: Build an interactive dashboard for EHR data visualization using Python and Dash',
            'resource_type': 'link',
            'url': 'https://github.com/excite-edu/ehr-dashboard-example',
            'icon': 'LinkIcon',
            'category': 'projects',
            'order': 1,
            'is_active': True,
            'course_specific': None,
            'metadata': {},
            'created_by': 'system',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        },
        {
            'id': 'project-clinical-nlp',
            'name': 'Clinical Text NLP Pipeline',
            'description': 'Example project demonstrating natural language processing on clinical notes',
            'resource_type': 'link',
            'url': 'https://github.com/excite-edu/clinical-nlp-pipeline',
            'icon': 'LinkIcon',
            'category': 'projects',
            'order': 2,
            'is_active': True,
            'course_specific': None,
            'metadata': {},
            'created_by': 'system',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        },

        # ========== SUPPLEMENTAL ==========
        {
            'id': 'wiki-health-informatics',
            'name': 'Health Informatics Knowledge Base',
            'description': 'Collaborative wiki with definitions, concepts, and best practices in health informatics',
            'resource_type': 'wiki',
            'url': 'https://wiki.excite.example.edu/health-informatics',
            'icon': 'BookIcon',
            'category': 'supplemental',
            'order': 1,
            'is_active': True,
            'course_specific': None,
            'metadata': {},
            'created_by': 'system',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        },
        {
            'id': 'link-ohdsi-community',
            'name': 'OHDSI Community Forums',
            'description': 'Active community forum for OHDSI users and developers to share knowledge and get support',
            'resource_type': 'link',
            'url': 'https://forums.ohdsi.org',
            'icon': 'LinkIcon',
            'category': 'supplemental',
            'order': 2,
            'is_active': True,
            'course_specific': None,
            'metadata': {},
            'created_by': 'system',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
    ]

    results = {
        'seeded': [],
        'existing': [],
        'errors': []
    }

    for resource in default_resources:
        try:
            # Check if resource already exists
            existing = db.get('resources', resource['id'])

            if existing:
                results['existing'].append(resource['name'])
            else:
                # Insert the resource (upsert expects document with 'id' field)
                db.upsert('resources', resource)
                results['seeded'].append(resource['name'])

        except Exception as e:
            results['errors'].append({
                'resource': resource['name'],
                'error': str(e)
            })

    return results


@classroom_bp.route('/api/resources/seed', methods=['POST'])
@require_jwt_token
@require_role(['admin'])
def seed_resources_endpoint():
    """
    Admin endpoint to seed default ExCITE resources.

    POST /api/resources/seed

    Returns:
        JSON response with seeding results
    """
    try:
        results = seed_default_resources()

        return jsonify({
            'success': True,
            'message': 'Seeding operation completed',
            'results': results
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
