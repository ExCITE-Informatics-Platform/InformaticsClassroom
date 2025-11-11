#!/usr/bin/env python3
"""
Student Enrollment Migration Script

Purpose: Backfill student enrollments in class_memberships from answer submissions

Background:
- Users have submitted answers for classes but don't have class_membership entries
- This causes them to not see their enrolled classes in the student dashboard
- Example: sliu197 has 164 answers for 'cda' but no class_membership for it

Solution:
- Query answer table for all (student, course) pairs
- For each pair, check if user has class_membership
- If not, add {"class_id": course, "role": "student"}
- Respect role hierarchy (don't downgrade instructor/TA to student)

Usage:
    python scripts/migrate_student_enrollments.py [--dry-run] [--min-submissions N]

    --dry-run: Show what would be changed without actually updating
    --min-submissions: Minimum answer count to consider enrollment (default: 5)
"""

import os
import sys
import argparse
from typing import Dict, List, Set, Tuple
import psycopg2
import psycopg2.extras
from datetime import datetime

# Direct database access (avoid Flask imports)
def get_database_connection():
    """Get direct PostgreSQL connection."""
    return psycopg2.connect(
        host=os.environ['POSTGRES_HOST'],
        port=int(os.environ['POSTGRES_PORT']),
        user=os.environ['POSTGRES_USER'],
        password=os.environ['POSTGRES_PASSWORD'],
        database=os.environ['POSTGRES_DB']
    )


def db_get(user_id: str) -> Dict:
    """Get user from database."""
    conn = get_database_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT data FROM users WHERE id = %s", (user_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return dict(result['data']) if result else None


def db_update(user_id: str, user_data: Dict):
    """Update user in database."""
    import json
    conn = get_database_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET data = %s, updated_at = NOW() WHERE id = %s",
        (json.dumps(user_data), user_id)
    )
    conn.commit()
    cur.close()
    conn.close()


# Placeholder patterns to exclude (not real users)
PLACEHOLDER_PATTERNS = [
    'JHED ID',
    'jhed id',
    'Your',
    'YOUR',
    'YourJHED',
    '##',
    'TERI 2023',
    'TIME2024',
]


def is_placeholder(username: str) -> bool:
    """Check if username is a placeholder/test value."""
    if not username or username.strip() == '':
        return True

    # Single character or very short
    if len(username) <= 2:
        return True

    # Contains placeholder patterns
    for pattern in PLACEHOLDER_PATTERNS:
        if pattern in username:
            return True

    return False


def get_enrollments_from_answers(min_submissions: int = 5) -> List[Tuple[str, str, int]]:
    """
    Query answer table to find (student, course, submission_count) enrollments.

    Args:
        min_submissions: Minimum number of submissions to consider enrollment

    Returns:
        List of (student_id, course_id, submission_count) tuples
    """
    conn = psycopg2.connect(
        host=os.environ['POSTGRES_HOST'],
        port=int(os.environ['POSTGRES_PORT']),
        user=os.environ['POSTGRES_USER'],
        password=os.environ['POSTGRES_PASSWORD'],
        database=os.environ['POSTGRES_DB']
    )

    cur = conn.cursor()
    cur.execute("""
        SELECT
            data->>'team' as student,
            data->>'course' as course,
            COUNT(*) as submission_count
        FROM answer
        WHERE data->>'team' IS NOT NULL
          AND data->>'team' != ''
        GROUP BY data->>'team', data->>'course'
        HAVING COUNT(*) >= %s
        ORDER BY student, course;
    """, (min_submissions,))

    enrollments = cur.fetchall()
    cur.close()
    conn.close()

    # Filter out placeholders
    valid_enrollments = [
        (student, course, count)
        for student, course, count in enrollments
        if not is_placeholder(student)
    ]

    return valid_enrollments


def analyze_user_enrollment(user: Dict, course: str) -> Tuple[bool, str]:
    """
    Analyze if user needs student enrollment for course.

    Args:
        user: User record from database
        course: Course ID

    Returns:
        (needs_enrollment, reason) tuple
    """
    class_memberships = user.get('class_memberships', [])

    # Check if user already has membership for this course
    for membership in class_memberships:
        if membership.get('class_id') == course:
            role = membership.get('role', '').lower()

            if role in ['instructor', 'ta']:
                return (False, f"already_{role}")
            elif role == 'student':
                return (False, "already_student")
            else:
                return (True, f"unknown_role_{role}")

    # No existing membership
    return (True, "missing_enrollment")


def migrate_enrollments(dry_run: bool = True, min_submissions: int = 5):
    """
    Main migration function.

    Args:
        dry_run: If True, show changes without applying
        min_submissions: Minimum submissions to consider enrollment
    """
    print("=" * 80)
    print("STUDENT ENROLLMENT MIGRATION")
    print("=" * 80)
    print(f"Mode: {'DRY RUN (no changes)' if dry_run else 'LIVE (will update database)'}")
    print(f"Minimum submissions: {min_submissions}")
    print(f"Started: {datetime.now()}")
    print()

    # Step 1: Get enrollments from answers
    print("Step 1: Analyzing answer submissions...")
    enrollments = get_enrollments_from_answers(min_submissions)
    print(f"Found {len(enrollments)} (student, course) pairs from answer table")
    print()

    # Step 2: Process each enrollment
    print("Step 2: Processing enrollments...")
    print()

    stats = {
        'total': len(enrollments),
        'user_not_found': 0,
        'already_instructor': 0,
        'already_ta': 0,
        'already_student': 0,
        'unknown_role': 0,
        'needs_enrollment': 0,
        'updated': 0,
        'errors': 0
    }

    updates_to_apply = []

    for student, course, submission_count in enrollments:
        # Get user
        user = db_get(student)

        if not user:
            stats['user_not_found'] += 1
            print(f"⚠️  User not found: {student} (course: {course}, {submission_count} submissions)")
            continue

        # Analyze enrollment
        needs_enrollment, reason = analyze_user_enrollment(user, course)

        if not needs_enrollment:
            if reason.startswith('already_'):
                role = reason.replace('already_', '')
                stats[f'already_{role}'] += 1
                print(f"✓  {student:<20} {course:<15} {role:>12} ({submission_count} submissions)")
            else:
                stats['unknown_role'] += 1
                print(f"⚠️  {student:<20} {course:<15} {reason:>12} ({submission_count} submissions)")
        else:
            stats['needs_enrollment'] += 1
            print(f"➕ {student:<20} {course:<15} {'ADD_STUDENT':>12} ({submission_count} submissions)")

            updates_to_apply.append({
                'user_id': student,
                'user': user,
                'course': course,
                'submission_count': submission_count
            })

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total enrollments analyzed:     {stats['total']}")
    print(f"  User not found:               {stats['user_not_found']}")
    print(f"  Already instructor:           {stats['already_instructor']}")
    print(f"  Already TA:                   {stats['already_ta']}")
    print(f"  Already student:              {stats['already_student']}")
    print(f"  Unknown role:                 {stats['unknown_role']}")
    print(f"  Need student enrollment:      {stats['needs_enrollment']}")
    print()

    # Step 3: Apply updates
    if updates_to_apply:
        if dry_run:
            print(f"🔍 DRY RUN: Would add {len(updates_to_apply)} student enrollments")
            print()
            print("Sample updates (first 10):")
            for update in updates_to_apply[:10]:
                print(f"  {update['user_id']:<20} → {update['course']:<15} as student")
            if len(updates_to_apply) > 10:
                print(f"  ... and {len(updates_to_apply) - 10} more")
        else:
            print(f"💾 Applying {len(updates_to_apply)} updates...")
            print()

            for update in updates_to_apply:
                try:
                    user = update['user']
                    user_id = update['user_id']
                    course = update['course']

                    # Add student enrollment
                    if 'class_memberships' not in user:
                        user['class_memberships'] = []

                    user['class_memberships'].append({
                        'class_id': course,
                        'role': 'student'
                    })

                    # Update database
                    db_update(user_id, user)

                    stats['updated'] += 1
                    print(f"✅ Updated {user_id} → {course}")

                except Exception as e:
                    stats['errors'] += 1
                    print(f"❌ Error updating {user_id} → {course}: {e}")

            print()
            print(f"✅ Successfully updated: {stats['updated']}")
            if stats['errors'] > 0:
                print(f"❌ Errors: {stats['errors']}")

    print()
    print("=" * 80)
    print("VALIDATION")
    print("=" * 80)

    # Validation: Check specific test cases
    test_users = ['sliu197', 'aalagha2', 'aliu62']

    for user_id in test_users:
        user = db_get(user_id)
        if user:
            class_memberships = user.get('class_memberships', [])
            print(f"\n{user_id}:")
            if class_memberships:
                for membership in class_memberships:
                    print(f"  - {membership.get('class_id'):<15} as {membership.get('role')}")
            else:
                print("  (no class memberships)")
        else:
            print(f"\n{user_id}: NOT FOUND")

    print()
    print("=" * 80)
    print(f"Completed: {datetime.now()}")
    print("=" * 80)


def main():
    """Parse arguments and run migration."""
    parser = argparse.ArgumentParser(
        description='Migrate student enrollments from answer submissions to class_memberships',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without actually updating'
    )

    parser.add_argument(
        '--min-submissions',
        type=int,
        default=5,
        help='Minimum number of submissions to consider enrollment (default: 5)'
    )

    args = parser.parse_args()

    # Verify environment variables
    required_env = ['POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_DB']
    missing_env = [var for var in required_env if var not in os.environ]

    if missing_env:
        print(f"❌ Missing required environment variables: {', '.join(missing_env)}")
        print()
        print("Please set:")
        print("  export DATABASE_TYPE=postgresql")
        print("  export POSTGRES_HOST=localhost")
        print("  export POSTGRES_PORT=5432")
        print("  export POSTGRES_USER=informatics_admin")
        print("  export POSTGRES_PASSWORD=informatics_local_dev")
        print("  export POSTGRES_DB=informatics_classroom")
        sys.exit(1)

    # Run migration
    migrate_enrollments(dry_run=args.dry_run, min_submissions=args.min_submissions)


if __name__ == '__main__':
    main()
