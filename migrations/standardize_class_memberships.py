#!/usr/bin/env python3
"""
Migration script to standardize class_memberships format.

This script converts all user records to use the list format for class_memberships:
[{"class_id": "fhir22", "role": "instructor"}, ...]

It handles:
1. Dict format: {"fhir22": "instructor"} -> list format
2. Dict with nested: {"fhir22": {"role": "instructor"}} -> list format
3. classRoles field: Merges into class_memberships
4. accessible_classes field: Converts to student memberships if not already present

Usage:
    python migrations/standardize_class_memberships.py [--dry-run]

Options:
    --dry-run    Preview changes without modifying database
"""

import os
import sys
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


def convert_to_list_format(user):
    """
    Convert all class membership data to standardized list format.

    Returns:
        tuple: (new_class_memberships, changes_made)
    """
    changes = []
    class_memberships = user.get('class_memberships', [])
    class_roles = user.get('classRoles', {})
    accessible_classes = user.get('accessible_classes', [])

    # Start with empty list
    new_memberships = []
    seen_classes = set()

    # Process existing class_memberships
    if isinstance(class_memberships, list):
        # Already list format - validate and keep
        for membership in class_memberships:
            if isinstance(membership, dict) and 'class_id' in membership:
                class_id = membership['class_id']
                role = membership.get('role', 'student')
                if class_id not in seen_classes:
                    new_memberships.append({'class_id': class_id, 'role': role})
                    seen_classes.add(class_id)
    elif isinstance(class_memberships, dict):
        # Dict format - convert to list
        changes.append(f"Converting class_memberships from dict to list format")
        for class_id, value in class_memberships.items():
            if class_id not in seen_classes:
                if isinstance(value, dict):
                    role = value.get('role', 'student')
                else:
                    role = value if value else 'student'
                new_memberships.append({'class_id': class_id, 'role': role})
                seen_classes.add(class_id)

    # Merge classRoles
    if class_roles and isinstance(class_roles, dict):
        for class_id, role in class_roles.items():
            if class_id not in seen_classes:
                changes.append(f"Merging classRoles entry: {class_id}={role}")
                if isinstance(role, dict):
                    role = role.get('role', 'student')
                new_memberships.append({'class_id': class_id, 'role': role})
                seen_classes.add(class_id)

    # Convert accessible_classes (legacy)
    if accessible_classes and isinstance(accessible_classes, list):
        for class_id in accessible_classes:
            if class_id and class_id not in seen_classes:
                changes.append(f"Converting accessible_classes entry: {class_id}")
                new_memberships.append({'class_id': class_id, 'role': 'student'})
                seen_classes.add(class_id)

    return new_memberships, changes


def run_migration(dry_run=False):
    """Run the migration to standardize class_memberships format."""
    from informatics_classroom.database.factory import get_database_adapter

    db = get_database_adapter()

    print("=" * 60)
    print("Class Memberships Standardization Migration")
    print("=" * 60)
    print(f"Mode: {'DRY RUN (no changes will be made)' if dry_run else 'LIVE'}")
    print()

    # Get all users
    users = db.query('users')
    print(f"Found {len(users)} users to process")
    print()

    updated_count = 0
    skipped_count = 0
    error_count = 0

    for user in users:
        user_id = user.get('id')
        email = user.get('email', 'unknown')

        try:
            new_memberships, changes = convert_to_list_format(user)

            # Check if update is needed
            old_memberships = user.get('class_memberships', [])
            has_class_roles = bool(user.get('classRoles'))
            has_accessible = bool(user.get('accessible_classes'))
            needs_update = changes or has_class_roles or has_accessible

            if not needs_update:
                skipped_count += 1
                continue

            print(f"User: {email} ({user_id})")
            for change in changes:
                print(f"  - {change}")
            print(f"  New memberships: {len(new_memberships)} classes")

            if not dry_run:
                # Update user record
                update_data = {
                    'class_memberships': new_memberships
                }

                # Remove legacy fields
                # Note: We can't remove fields with update(), so we'll need to set them to None
                # or handle this at the database level

                db.update('users', user_id, update_data)
                print(f"  ✓ Updated")
            else:
                print(f"  [DRY RUN - would update]")

            updated_count += 1
            print()

        except Exception as e:
            print(f"Error processing user {user_id}: {e}")
            error_count += 1

    print("=" * 60)
    print("Migration Summary")
    print("=" * 60)
    print(f"Total users:   {len(users)}")
    print(f"Updated:       {updated_count}")
    print(f"Skipped:       {skipped_count}")
    print(f"Errors:        {error_count}")
    print()

    if dry_run:
        print("This was a DRY RUN. No changes were made.")
        print("Run without --dry-run to apply changes.")
    else:
        print("Migration completed successfully.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Standardize class_memberships format')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview changes without modifying database')
    args = parser.parse_args()

    run_migration(dry_run=args.dry_run)
