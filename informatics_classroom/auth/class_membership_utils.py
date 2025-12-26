"""
Class Membership Utilities

Provides utilities for normalizing, validating, and syncing class membership data
across the three supported formats:
- class_memberships: List format [{class_id, role, ...}] - NEW standard
- classRoles: Dict format {class_id: role} - Legacy intermediate
- accessible_classes: List of class IDs [class_id, ...] - Legacy old

These utilities ensure data consistency across all three formats.
"""

from typing import Dict, List, Optional, Any, Tuple
import datetime


def normalize_class_memberships(user: Dict) -> Dict:
    """
    Normalize class membership data to ensure all three formats are in sync.

    Priority order (source of truth):
    1. class_memberships list (if populated)
    2. classRoles dict (if class_memberships empty)
    3. accessible_classes list (if both above empty)

    Args:
        user: User document/dict

    Returns:
        Updated user dict with normalized class membership fields
    """
    if not user:
        return user

    # Get current values
    class_memberships = user.get('class_memberships', [])
    class_roles = user.get('classRoles', {})
    accessible_classes = user.get('accessible_classes', [])

    # Determine source of truth and build canonical list
    canonical_memberships = []

    # Priority 1: Use class_memberships list if populated
    if isinstance(class_memberships, list) and class_memberships:
        for membership in class_memberships:
            if isinstance(membership, dict) and 'class_id' in membership:
                canonical_memberships.append({
                    'class_id': membership['class_id'],
                    'role': membership.get('role', 'student'),
                    'assigned_at': membership.get('assigned_at'),
                    'assigned_by': membership.get('assigned_by')
                })

    # Priority 2: Convert class_memberships dict format (legacy)
    elif isinstance(class_memberships, dict) and class_memberships:
        for class_id, value in class_memberships.items():
            if isinstance(value, dict):
                role = value.get('role', 'student')
            else:
                role = value if value else 'student'
            canonical_memberships.append({
                'class_id': class_id,
                'role': role
            })

    # Priority 3: Use classRoles dict
    elif isinstance(class_roles, dict) and class_roles:
        for class_id, role in class_roles.items():
            if isinstance(role, dict):
                role = role.get('role', 'student')
            canonical_memberships.append({
                'class_id': class_id,
                'role': role if role else 'student'
            })

    # Priority 4: Use accessible_classes with inferred role
    elif isinstance(accessible_classes, list) and accessible_classes:
        # Infer role from global role
        global_role = user.get('role', '').lower()
        if global_role in ['admin', 'instructor']:
            inferred_role = 'instructor'
        elif global_role in ['ta', 'grader']:  # grader upgraded to ta
            inferred_role = 'ta'
        else:
            inferred_role = 'student'

        for class_id in accessible_classes:
            if class_id:
                canonical_memberships.append({
                    'class_id': class_id,
                    'role': inferred_role
                })

    # Build all three formats from canonical list
    new_class_memberships = canonical_memberships
    new_class_roles = {}
    new_accessible_classes = []

    for membership in canonical_memberships:
        class_id = membership['class_id']
        role = membership['role']
        new_class_roles[class_id] = role
        new_accessible_classes.append(class_id)

    # Update user with normalized values
    user['class_memberships'] = new_class_memberships
    user['classRoles'] = new_class_roles
    user['accessible_classes'] = new_accessible_classes

    return user


def validate_class_membership(membership: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate a single class membership entry.

    Args:
        membership: A membership entry to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(membership, dict):
        return False, "Membership must be a dict"

    if 'class_id' not in membership:
        return False, "Membership missing required 'class_id' field"

    if not membership['class_id']:
        return False, "Membership 'class_id' cannot be empty"

    if not isinstance(membership['class_id'], str):
        return False, "Membership 'class_id' must be a string"

    # Role is optional but must be valid if present
    role = membership.get('role')
    if role is not None:
        if not isinstance(role, str):
            return False, "Membership 'role' must be a string"
        valid_roles = ['admin', 'instructor', 'ta', 'student', 'user']
        if role.lower() not in valid_roles:
            return False, f"Invalid role '{role}'. Must be one of: {valid_roles}"

    return True, None


def validate_class_memberships_list(memberships: Any) -> Tuple[bool, List[str]]:
    """
    Validate a list of class memberships.

    Args:
        memberships: List of membership entries

    Returns:
        Tuple of (all_valid, list of error messages)
    """
    errors = []

    if not isinstance(memberships, list):
        return False, ["class_memberships must be a list"]

    seen_classes = set()
    for idx, membership in enumerate(memberships):
        is_valid, error = validate_class_membership(membership)
        if not is_valid:
            errors.append(f"Entry {idx}: {error}")
        else:
            class_id = membership['class_id']
            if class_id in seen_classes:
                errors.append(f"Entry {idx}: Duplicate class_id '{class_id}'")
            seen_classes.add(class_id)

    return len(errors) == 0, errors


def check_format_consistency(user: Dict) -> Tuple[bool, List[str]]:
    """
    Check if all three class membership formats are consistent.

    Args:
        user: User document/dict

    Returns:
        Tuple of (is_consistent, list of inconsistency descriptions)
    """
    inconsistencies = []

    class_memberships = user.get('class_memberships', [])
    class_roles = user.get('classRoles', {})
    accessible_classes = user.get('accessible_classes', [])

    # Build sets for comparison
    memberships_classes = set()
    memberships_roles = {}
    if isinstance(class_memberships, list):
        for m in class_memberships:
            if isinstance(m, dict) and 'class_id' in m:
                memberships_classes.add(m['class_id'])
                memberships_roles[m['class_id']] = m.get('role', 'student')

    roles_classes = set()
    if isinstance(class_roles, dict):
        roles_classes = set(class_roles.keys())

    accessible_set = set()
    if isinstance(accessible_classes, list):
        accessible_set = set(c for c in accessible_classes if c)

    # Check class ID consistency
    all_classes = memberships_classes | roles_classes | accessible_set

    if memberships_classes != all_classes:
        missing = all_classes - memberships_classes
        extra = memberships_classes - all_classes
        if missing:
            inconsistencies.append(f"class_memberships missing classes: {missing}")
        if extra:
            inconsistencies.append(f"class_memberships has extra classes: {extra}")

    if roles_classes != all_classes:
        missing = all_classes - roles_classes
        extra = roles_classes - all_classes
        if missing:
            inconsistencies.append(f"classRoles missing classes: {missing}")
        if extra:
            inconsistencies.append(f"classRoles has extra classes: {extra}")

    if accessible_set != all_classes:
        missing = all_classes - accessible_set
        extra = accessible_set - all_classes
        if missing:
            inconsistencies.append(f"accessible_classes missing classes: {missing}")
        if extra:
            inconsistencies.append(f"accessible_classes has extra classes: {extra}")

    # Check role consistency between class_memberships and classRoles
    if isinstance(class_roles, dict):
        for class_id, role in class_roles.items():
            if class_id in memberships_roles:
                if memberships_roles[class_id] != role:
                    inconsistencies.append(
                        f"Role mismatch for {class_id}: "
                        f"class_memberships has '{memberships_roles[class_id]}', "
                        f"classRoles has '{role}'"
                    )

    return len(inconsistencies) == 0, inconsistencies


def add_class_membership(
    user: Dict,
    class_id: str,
    role: str = 'student',
    assigned_by: Optional[str] = None
) -> Dict:
    """
    Add a class membership to a user, updating all three formats.

    Args:
        user: User document/dict
        class_id: Class identifier
        role: Role to assign (default: 'student')
        assigned_by: ID of user making the assignment

    Returns:
        Updated user dict
    """
    if not user:
        return user

    # Normalize first
    user = normalize_class_memberships(user)

    class_memberships = user.get('class_memberships', [])
    class_roles = user.get('classRoles', {})
    accessible_classes = user.get('accessible_classes', [])

    # Check if already exists
    existing_idx = None
    for idx, m in enumerate(class_memberships):
        if isinstance(m, dict) and m.get('class_id') == class_id:
            existing_idx = idx
            break

    # Create new membership entry
    new_membership = {
        'class_id': class_id,
        'role': role,
        'assigned_at': datetime.datetime.utcnow().isoformat(),
        'assigned_by': assigned_by
    }

    # Update class_memberships list
    if existing_idx is not None:
        class_memberships[existing_idx] = new_membership
    else:
        class_memberships.append(new_membership)

    # Update classRoles dict
    class_roles[class_id] = role

    # Update accessible_classes list
    if class_id not in accessible_classes:
        accessible_classes.append(class_id)

    user['class_memberships'] = class_memberships
    user['classRoles'] = class_roles
    user['accessible_classes'] = accessible_classes

    return user


def remove_class_membership(user: Dict, class_id: str) -> Dict:
    """
    Remove a class membership from a user, updating all three formats.

    Args:
        user: User document/dict
        class_id: Class identifier to remove

    Returns:
        Updated user dict
    """
    if not user:
        return user

    # Remove from class_memberships list
    class_memberships = user.get('class_memberships', [])
    if isinstance(class_memberships, list):
        class_memberships = [
            m for m in class_memberships
            if not (isinstance(m, dict) and m.get('class_id') == class_id)
        ]
        user['class_memberships'] = class_memberships

    # Remove from classRoles dict
    class_roles = user.get('classRoles', {})
    if isinstance(class_roles, dict) and class_id in class_roles:
        del class_roles[class_id]
        user['classRoles'] = class_roles

    # Remove from accessible_classes list
    accessible_classes = user.get('accessible_classes', [])
    if isinstance(accessible_classes, list) and class_id in accessible_classes:
        accessible_classes.remove(class_id)
        user['accessible_classes'] = accessible_classes

    return user


def get_user_role_for_class(user: Dict, class_id: str) -> Optional[str]:
    """
    Get the user's role for a specific class.

    Args:
        user: User document/dict
        class_id: Class identifier

    Returns:
        Role string or None if not a member
    """
    if not user or not class_id:
        return None

    # Check class_memberships list first (new format)
    class_memberships = user.get('class_memberships', [])
    if isinstance(class_memberships, list):
        for m in class_memberships:
            if isinstance(m, dict) and m.get('class_id') == class_id:
                return m.get('role', 'student')

    # Fallback to classRoles dict (legacy)
    class_roles = user.get('classRoles', {})
    if isinstance(class_roles, dict) and class_id in class_roles:
        role = class_roles[class_id]
        if isinstance(role, dict):
            return role.get('role', 'student')
        return role if role else 'student'

    # Fallback to accessible_classes (very old legacy)
    accessible_classes = user.get('accessible_classes', [])
    if isinstance(accessible_classes, list) and class_id in accessible_classes:
        return 'student'  # Default role for legacy format

    return None
