#!/usr/bin/env python3
"""
Migration script to normalize user data models.

This script ensures:
1. All class_memberships entries have assigned_at and assigned_by fields
2. All users have isActive and permissions fields
3. Report on legacy format usage (classRoles, accessible_classes)

Usage:
    python migrations/normalize_user_data.py [--dry-run] [--fix-memberships] [--fix-fields] [--report-only]

Options:
    --dry-run         Preview changes without modifying database
    --fix-memberships Add missing metadata to class_memberships entries
    --fix-fields      Add missing isActive and permissions fields to users
    --report-only     Only report data issues, don't fix anything
    --all             Apply all fixes (equivalent to --fix-memberships --fix-fields)
"""

import os
import sys
import argparse
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


def analyze_class_memberships(db):
    """Analyze class_memberships for missing metadata."""
    print("\n--- Analyzing class_memberships metadata ---")

    users = db.query('users')

    total_users = len(users)
    users_with_memberships = 0
    memberships_missing_assigned_at = 0
    memberships_missing_assigned_by = 0
    total_memberships = 0
    users_needing_fix = []

    for user in users:
        user_id = user.get('id', user.get('email', 'unknown'))
        class_memberships = user.get('class_memberships', [])

        if not isinstance(class_memberships, list):
            continue

        if class_memberships:
            users_with_memberships += 1

        user_needs_fix = False
        for membership in class_memberships:
            total_memberships += 1
            if not isinstance(membership, dict):
                continue
            if 'assigned_at' not in membership:
                memberships_missing_assigned_at += 1
                user_needs_fix = True
            if 'assigned_by' not in membership:
                memberships_missing_assigned_by += 1
                user_needs_fix = True

        if user_needs_fix:
            users_needing_fix.append(user)

    print(f"\nTotal users: {total_users}")
    print(f"Users with class_memberships: {users_with_memberships}")
    print(f"Total memberships: {total_memberships}")
    print(f"Memberships missing assigned_at: {memberships_missing_assigned_at}")
    print(f"Memberships missing assigned_by: {memberships_missing_assigned_by}")
    print(f"Users needing metadata fix: {len(users_needing_fix)}")

    return users_needing_fix


def analyze_user_fields(db):
    """Analyze users for missing isActive and permissions fields."""
    print("\n--- Analyzing user fields (isActive, permissions) ---")

    users = db.query('users')

    total_users = len(users)
    missing_is_active = 0
    missing_permissions = 0
    users_needing_fix = []

    for user in users:
        user_id = user.get('id', user.get('email', 'unknown'))
        needs_fix = False

        if 'isActive' not in user:
            missing_is_active += 1
            needs_fix = True
        if 'permissions' not in user:
            missing_permissions += 1
            needs_fix = True

        if needs_fix:
            users_needing_fix.append(user)

    print(f"\nTotal users: {total_users}")
    print(f"Users missing isActive: {missing_is_active}")
    print(f"Users missing permissions: {missing_permissions}")
    print(f"Users needing field fix: {len(users_needing_fix)}")

    return users_needing_fix


def analyze_legacy_formats(db):
    """Report on legacy format usage (classRoles, accessible_classes)."""
    print("\n--- Analyzing legacy format usage ---")

    users = db.query('users')

    total_users = len(users)
    has_class_roles = 0
    has_accessible_classes = 0
    non_empty_class_roles = 0
    non_empty_accessible_classes = 0

    for user in users:
        user_id = user.get('id', user.get('email', 'unknown'))

        class_roles = user.get('classRoles')
        if class_roles is not None:
            has_class_roles += 1
            if class_roles and isinstance(class_roles, dict) and len(class_roles) > 0:
                non_empty_class_roles += 1

        accessible = user.get('accessible_classes')
        if accessible is not None:
            has_accessible_classes += 1
            if accessible and isinstance(accessible, list) and len(accessible) > 0:
                non_empty_accessible_classes += 1

    print(f"\nTotal users: {total_users}")
    print(f"Users with classRoles field: {has_class_roles} ({non_empty_class_roles} non-empty)")
    print(f"Users with accessible_classes field: {has_accessible_classes} ({non_empty_accessible_classes} non-empty)")
    print("\nNote: Legacy formats are kept for read compatibility. New writes go to class_memberships only.")

    return {
        'has_class_roles': has_class_roles,
        'non_empty_class_roles': non_empty_class_roles,
        'has_accessible_classes': has_accessible_classes,
        'non_empty_accessible_classes': non_empty_accessible_classes
    }


def fix_membership_metadata(db, users_to_fix, dry_run=False):
    """Add missing assigned_at and assigned_by to class_memberships."""
    print("\n--- Fixing class_memberships metadata ---")

    if not users_to_fix:
        print("No users need membership metadata fixes.")
        return 0

    updated_count = 0
    error_count = 0
    migration_timestamp = datetime.now(timezone.utc).isoformat()

    for user in users_to_fix:
        user_id = user.get('id', user.get('email', 'unknown'))
        class_memberships = user.get('class_memberships', [])

        if not isinstance(class_memberships, list):
            continue

        modified = False
        for membership in class_memberships:
            if not isinstance(membership, dict):
                continue
            if 'assigned_at' not in membership:
                membership['assigned_at'] = migration_timestamp
                modified = True
            if 'assigned_by' not in membership:
                membership['assigned_by'] = 'migration-backfill'
                modified = True

        if modified:
            if dry_run:
                print(f"  [DRY RUN] Would update {user_id}: add metadata to {len(class_memberships)} memberships")
            else:
                try:
                    user['class_memberships'] = class_memberships
                    db.upsert('users', user)
                    updated_count += 1
                    print(f"  Updated {user_id}: added metadata to memberships")
                except Exception as e:
                    print(f"  Error updating {user_id}: {e}")
                    error_count += 1

    if dry_run:
        print(f"\n[DRY RUN] Would update {len(users_to_fix)} users")
    else:
        print(f"\nUpdated {updated_count} users, {error_count} errors")

    return updated_count


def fix_user_fields(db, users_to_fix, dry_run=False):
    """Add missing isActive and permissions fields to users."""
    print("\n--- Fixing user fields (isActive, permissions) ---")

    if not users_to_fix:
        print("No users need field fixes.")
        return 0

    updated_count = 0
    error_count = 0

    for user in users_to_fix:
        user_id = user.get('id', user.get('email', 'unknown'))
        modified = False

        if 'isActive' not in user:
            user['isActive'] = True
            modified = True
        if 'permissions' not in user:
            user['permissions'] = []
            modified = True

        if modified:
            if dry_run:
                print(f"  [DRY RUN] Would update {user_id}: add isActive and/or permissions")
            else:
                try:
                    db.upsert('users', user)
                    updated_count += 1
                    print(f"  Updated {user_id}: added missing fields")
                except Exception as e:
                    print(f"  Error updating {user_id}: {e}")
                    error_count += 1

    if dry_run:
        print(f"\n[DRY RUN] Would update {len(users_to_fix)} users")
    else:
        print(f"\nUpdated {updated_count} users, {error_count} errors")

    return updated_count


def run_migration(dry_run=False, fix_memberships=False, fix_fields=False, report_only=False):
    """Run the user data normalization analysis and fixes."""
    from informatics_classroom.database.factory import get_database_adapter

    db = get_database_adapter()

    print("=" * 60)
    print("User Data Normalization")
    print("=" * 60)
    print(f"Mode: {'REPORT ONLY' if report_only else 'DRY RUN' if dry_run else 'LIVE'}")
    print()

    # Get total user count
    users = db.query('users')
    print(f"Total users in database: {len(users)}")

    # Analyze class_memberships metadata
    users_needing_membership_fix = analyze_class_memberships(db)

    # Analyze user fields
    users_needing_field_fix = analyze_user_fields(db)

    # Report on legacy formats
    legacy_stats = analyze_legacy_formats(db)

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    if users_needing_membership_fix:
        print(f"\nclass_memberships metadata issues: {len(users_needing_membership_fix)} users")
        if fix_memberships and not report_only:
            fix_membership_metadata(db, users_needing_membership_fix, dry_run=dry_run)
        elif not report_only:
            print("  To fix, run with --fix-memberships flag")
    else:
        print("\nclass_memberships: All entries have proper metadata")

    if users_needing_field_fix:
        print(f"\nUser field issues: {len(users_needing_field_fix)} users missing isActive/permissions")
        if fix_fields and not report_only:
            fix_user_fields(db, users_needing_field_fix, dry_run=dry_run)
        elif not report_only:
            print("  To fix, run with --fix-fields flag")
    else:
        print("\nUser fields: All users have isActive and permissions")

    if legacy_stats['non_empty_class_roles'] > 0 or legacy_stats['non_empty_accessible_classes'] > 0:
        print(f"\nLegacy formats still in use:")
        print(f"  - {legacy_stats['non_empty_class_roles']} users with non-empty classRoles")
        print(f"  - {legacy_stats['non_empty_accessible_classes']} users with non-empty accessible_classes")
        print("  Note: These are read-only for backward compatibility. class_memberships is authoritative.")

    if report_only:
        print("\nThis was a REPORT ONLY run. No changes were made.")
    elif dry_run:
        print("\nThis was a DRY RUN. No changes were made.")
        print("Run without --dry-run to apply changes.")

    print("\n" + "=" * 60)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Normalize user data models')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview changes without modifying database')
    parser.add_argument('--fix-memberships', action='store_true',
                        help='Add missing metadata to class_memberships')
    parser.add_argument('--fix-fields', action='store_true',
                        help='Add missing isActive and permissions to users')
    parser.add_argument('--report-only', action='store_true',
                        help='Only report issues, do not fix anything')
    parser.add_argument('--all', action='store_true',
                        help='Apply all fixes')
    args = parser.parse_args()

    if args.all:
        args.fix_memberships = True
        args.fix_fields = True

    run_migration(
        dry_run=args.dry_run,
        fix_memberships=args.fix_memberships,
        fix_fields=args.fix_fields,
        report_only=args.report_only
    )
