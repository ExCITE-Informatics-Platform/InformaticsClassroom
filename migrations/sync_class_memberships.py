#!/usr/bin/env python3
"""
Migration script to check and sync class membership formats.

This script ensures all three class membership formats are in sync:
- class_memberships: List format [{class_id, role, ...}] - NEW standard
- classRoles: Dict format {class_id: role} - Legacy intermediate
- accessible_classes: List of class IDs [class_id, ...] - Legacy old

Usage:
    python migrations/sync_class_memberships.py [--dry-run] [--fix] [--user USER_ID]

Options:
    --dry-run    Preview changes without modifying database
    --fix        Fix inconsistencies found
    --user       Check/fix specific user only
"""

import os
import sys
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


def check_user_consistency(user):
    """
    Check if a user's class membership formats are consistent.

    Returns:
        tuple: (is_consistent, list of issues)
    """
    issues = []

    class_memberships = user.get('class_memberships', [])
    class_roles = user.get('classRoles', {})
    accessible_classes = user.get('accessible_classes', [])

    # Normalize to sets for comparison
    memberships_classes = set()
    memberships_roles = {}

    if isinstance(class_memberships, list):
        for m in class_memberships:
            if isinstance(m, dict) and 'class_id' in m:
                memberships_classes.add(m['class_id'])
                memberships_roles[m['class_id']] = m.get('role', 'student')
    elif isinstance(class_memberships, dict):
        # Old dict format still present
        issues.append("class_memberships is dict format (should be list)")
        for class_id, value in class_memberships.items():
            memberships_classes.add(class_id)
            if isinstance(value, dict):
                memberships_roles[class_id] = value.get('role', 'student')
            else:
                memberships_roles[class_id] = value if value else 'student'

    roles_classes = set()
    roles_map = {}
    if isinstance(class_roles, dict):
        for class_id, role in class_roles.items():
            roles_classes.add(class_id)
            if isinstance(role, dict):
                roles_map[class_id] = role.get('role', 'student')
            else:
                roles_map[class_id] = role if role else 'student'

    accessible_set = set()
    if isinstance(accessible_classes, list):
        accessible_set = set(c for c in accessible_classes if c)

    # Find all classes across all formats
    all_classes = memberships_classes | roles_classes | accessible_set

    # Check for missing classes in each format
    missing_in_memberships = all_classes - memberships_classes
    missing_in_roles = all_classes - roles_classes
    missing_in_accessible = all_classes - accessible_set

    if missing_in_memberships:
        issues.append(f"class_memberships missing: {missing_in_memberships}")

    if missing_in_roles:
        issues.append(f"classRoles missing: {missing_in_roles}")

    if missing_in_accessible:
        issues.append(f"accessible_classes missing: {missing_in_accessible}")

    # Check for role mismatches
    for class_id in memberships_classes & roles_classes:
        if memberships_roles.get(class_id) != roles_map.get(class_id):
            issues.append(
                f"Role mismatch for {class_id}: "
                f"class_memberships='{memberships_roles.get(class_id)}', "
                f"classRoles='{roles_map.get(class_id)}'"
            )

    return len(issues) == 0, issues


def fix_user_consistency(user):
    """
    Fix a user's class membership formats to be consistent.

    Uses class_memberships as source of truth, falls back to classRoles, then accessible_classes.

    Returns:
        tuple: (updated_user, changes_made)
    """
    changes = []

    class_memberships = user.get('class_memberships', [])
    class_roles = user.get('classRoles', {})
    accessible_classes = user.get('accessible_classes', [])

    # Build canonical membership list
    canonical = []
    seen_classes = set()

    # Priority 1: class_memberships list
    if isinstance(class_memberships, list) and class_memberships:
        for m in class_memberships:
            if isinstance(m, dict) and 'class_id' in m:
                class_id = m['class_id']
                if class_id not in seen_classes:
                    canonical.append({
                        'class_id': class_id,
                        'role': m.get('role', 'student'),
                        'assigned_at': m.get('assigned_at'),
                        'assigned_by': m.get('assigned_by')
                    })
                    seen_classes.add(class_id)

    # Priority 2: class_memberships dict (legacy format - needs conversion)
    elif isinstance(class_memberships, dict) and class_memberships:
        changes.append("Converting class_memberships from dict to list")
        for class_id, value in class_memberships.items():
            if class_id not in seen_classes:
                if isinstance(value, dict):
                    role = value.get('role', 'student')
                else:
                    role = value if value else 'student'
                canonical.append({'class_id': class_id, 'role': role})
                seen_classes.add(class_id)

    # Priority 3: classRoles dict
    if isinstance(class_roles, dict):
        for class_id, role in class_roles.items():
            if class_id not in seen_classes:
                changes.append(f"Adding {class_id} from classRoles")
                if isinstance(role, dict):
                    role = role.get('role', 'student')
                canonical.append({'class_id': class_id, 'role': role if role else 'student'})
                seen_classes.add(class_id)

    # Priority 4: accessible_classes list (infer role)
    if isinstance(accessible_classes, list):
        # Infer role from global role
        global_role = user.get('role', '').lower()
        if global_role in ['admin', 'instructor']:
            inferred_role = 'instructor'
        elif global_role == 'ta':
            inferred_role = 'ta'
        elif global_role == 'grader':
            inferred_role = 'grader'
        else:
            inferred_role = 'student'

        for class_id in accessible_classes:
            if class_id and class_id not in seen_classes:
                changes.append(f"Adding {class_id} from accessible_classes as {inferred_role}")
                canonical.append({'class_id': class_id, 'role': inferred_role})
                seen_classes.add(class_id)

    # Build all three formats from canonical
    new_memberships = canonical
    new_roles = {m['class_id']: m['role'] for m in canonical}
    new_accessible = [m['class_id'] for m in canonical]

    # Check what changed
    if user.get('class_memberships') != new_memberships:
        if not changes:
            changes.append("Syncing class_memberships")
    if user.get('classRoles') != new_roles:
        if not any('classRoles' in c for c in changes):
            changes.append("Syncing classRoles")
    if user.get('accessible_classes') != new_accessible:
        if not any('accessible_classes' in c for c in changes):
            changes.append("Syncing accessible_classes")

    user['class_memberships'] = new_memberships
    user['classRoles'] = new_roles
    user['accessible_classes'] = new_accessible

    return user, changes


def run_sync(dry_run=False, fix=False, user_id=None):
    """Run the sync check and optionally fix inconsistencies."""
    from informatics_classroom.database.factory import get_database_adapter

    db = get_database_adapter()

    print("=" * 60)
    print("Class Membership Format Sync Check")
    print("=" * 60)
    print(f"Mode: {'DRY RUN' if dry_run else 'FIX' if fix else 'CHECK ONLY'}")
    print()

    # Get users
    if user_id:
        user = db.get('users', user_id)
        if not user:
            print(f"User {user_id} not found")
            return
        users = [user]
    else:
        users = db.query('users')

    print(f"Checking {len(users)} users...")
    print()

    consistent_count = 0
    inconsistent_count = 0
    fixed_count = 0
    error_count = 0

    inconsistent_users = []

    for user in users:
        uid = user.get('id', 'unknown')
        email = user.get('email', '')

        try:
            is_consistent, issues = check_user_consistency(user)

            if is_consistent:
                consistent_count += 1
            else:
                inconsistent_count += 1
                inconsistent_users.append((uid, email, issues))

                if fix and not dry_run:
                    updated_user, changes = fix_user_consistency(user)
                    db.update('users', uid, updated_user)
                    fixed_count += 1
                    print(f"  Fixed {uid} ({email})")
                    for change in changes:
                        print(f"    - {change}")

        except Exception as e:
            print(f"  Error checking {uid}: {e}")
            error_count += 1

    # Print summary
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Total users:      {len(users)}")
    print(f"Consistent:       {consistent_count}")
    print(f"Inconsistent:     {inconsistent_count}")
    if fix and not dry_run:
        print(f"Fixed:            {fixed_count}")
    print(f"Errors:           {error_count}")
    print()

    # Print inconsistent users
    if inconsistent_users and not fix:
        print("Inconsistent users:")
        print("-" * 60)
        for uid, email, issues in inconsistent_users[:20]:  # Limit to first 20
            print(f"\n{uid} ({email}):")
            for issue in issues:
                print(f"  - {issue}")

        if len(inconsistent_users) > 20:
            print(f"\n... and {len(inconsistent_users) - 20} more")

        print()
        print("Run with --fix to correct these issues")

    if dry_run:
        print("\nThis was a DRY RUN. No changes were made.")
        print("Run without --dry-run to apply fixes.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Sync class membership formats')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview changes without modifying database')
    parser.add_argument('--fix', action='store_true',
                        help='Fix inconsistencies found')
    parser.add_argument('--user', type=str,
                        help='Check/fix specific user only')
    args = parser.parse_args()

    run_sync(dry_run=args.dry_run, fix=args.fix, user_id=args.user)
