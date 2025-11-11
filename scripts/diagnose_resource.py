#!/usr/bin/env python3
"""
Diagnostic script to check TIME2025 resource visibility issue.

Usage:
    python scripts/diagnose_resource.py <user_email>
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from informatics_classroom.database.factory import get_database_adapter
from informatics_classroom.classroom.routes import get_classes_for_user, get_current_user

def diagnose_resource_issue(user_email):
    """Diagnose why TIME2025 resources aren't showing for a user."""

    print(f"\n{'='*60}")
    print(f"DIAGNOSING RESOURCE VISIBILITY FOR: {user_email}")
    print(f"{'='*60}\n")

    db = get_database_adapter()
    user_id = user_email.split('@')[0]

    # Step 1: Check if TIME2025 resources exist
    print("Step 1: Checking for TIME2025 resources in database...")
    all_resources = db.query('resources', filters={})
    time2025_resources = [r for r in all_resources if r.get('course_specific') == 'TIME2025']

    print(f"   Total resources in database: {len(all_resources)}")
    print(f"   TIME2025 resources found: {len(time2025_resources)}")

    if time2025_resources:
        print("\n   TIME2025 Resources:")
        for r in time2025_resources:
            print(f"     - {r.get('name')} (ID: {r.get('id')}, Active: {r.get('is_active')})")
    else:
        print("   ❌ NO TIME2025 resources found in database!")
        print("   This means the resource was not saved with course_specific='TIME2025'")

    # Step 2: Check user enrollment
    print(f"\nStep 2: Checking user enrollment for {user_email}...")
    users = get_current_user(user_id)

    if not users:
        print(f"   ❌ User {user_email} not found in database!")
        return

    user = users[0]
    class_memberships = user.get('class_memberships', [])
    enrolled_classes = [m.get('class_id') for m in class_memberships]

    print(f"   User enrolled in: {enrolled_classes}")
    print(f"   Is enrolled in TIME2025: {'✅ YES' if 'TIME2025' in enrolled_classes else '❌ NO'}")

    if 'TIME2025' not in enrolled_classes:
        print("\n   ⚠️  User is NOT enrolled in TIME2025!")
        print("   This is why TIME2025 resources don't appear.")
        print("\n   To fix: Enroll user in TIME2025 or check class_memberships field.")

    # Step 3: Check what get_classes_for_user returns
    print(f"\nStep 3: Checking get_classes_for_user() function...")
    user_classes = get_classes_for_user(user_id)
    print(f"   Classes returned by get_classes_for_user: {user_classes}")

    # Step 4: Simulate what the API would return
    print(f"\nStep 4: Simulating API response...")
    print("   This shows what the /api/resources endpoint would return:\n")

    general_resources = [r for r in all_resources if r.get('course_specific') is None and r.get('is_active', True)]
    course_specific_resources = {}

    for course in user_classes:
        course_specific_resources[course] = [
            r for r in all_resources
            if r.get('course_specific') == course and r.get('is_active', True)
        ]

    print(f"   General resources: {len(general_resources)}")
    print(f"   Course-specific resources:")
    for course, resources in course_specific_resources.items():
        print(f"     - {course}: {len(resources)} resources")

    # Summary
    print(f"\n{'='*60}")
    print("DIAGNOSIS SUMMARY:")
    print(f"{'='*60}")

    if not time2025_resources:
        print("❌ ISSUE: TIME2025 resource was not created in database")
        print("   Fix: Create resource through ResourcesTab with classId='TIME2025'")
    elif 'TIME2025' not in enrolled_classes:
        print("❌ ISSUE: User is not enrolled in TIME2025")
        print("   Fix: Add TIME2025 to user's class_memberships")
    else:
        print("✅ Everything looks correct!")
        print("   Resource exists and user is enrolled.")
        print("   If still not showing, check frontend filtering logic.")

    print("")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python scripts/diagnose_resource.py <user_email>")
        sys.exit(1)

    diagnose_resource_issue(sys.argv[1])
