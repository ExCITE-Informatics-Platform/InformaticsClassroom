#!/usr/bin/env python3
"""
Migration script to normalize answer data types.

This script standardizes:
1. 'correct' field: All values -> '0' or '1' (string format for JSONB consistency)
2. 'module' field: Report on text modules (no automatic conversion - data may be intentional)

Usage:
    python migrations/normalize_answer_types.py [--dry-run] [--fix-correct] [--report-only]

Options:
    --dry-run       Preview changes without modifying database
    --fix-correct   Normalize 'correct' field values
    --report-only   Only report data issues, don't fix anything
"""

import os
import sys
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


def analyze_correct_values(db):
    """Analyze the distribution of 'correct' field values."""
    print("\n--- Analyzing 'correct' field values ---")

    # Query to get distinct correct values and counts
    query = """
        SELECT
            data->>'correct' as correct_value,
            COUNT(*) as count
        FROM answer
        WHERE data->>'correct' IS NOT NULL
        GROUP BY data->>'correct'
        ORDER BY count DESC
    """
    results = db.query_raw('answer', query, [])

    print(f"\nDistinct 'correct' values found:")
    print(f"{'Value':<20} {'Count':>10}")
    print("-" * 32)

    needs_normalization = []
    for row in results:
        value = row['correct_value']
        count = row['count']
        print(f"{repr(value):<20} {count:>10}")

        # Check if value needs normalization
        if value not in ('0', '1'):
            needs_normalization.append((value, count))

    return needs_normalization


def analyze_module_values(db):
    """Analyze the distribution of 'module' field values."""
    print("\n--- Analyzing 'module' field values ---")

    # Query to find non-numeric module values
    query = """
        SELECT
            data->>'module' as module_value,
            data->>'course' as course,
            COUNT(*) as count
        FROM answer
        WHERE data->>'module' ~ '[^0-9]'
        GROUP BY data->>'module', data->>'course'
        ORDER BY count DESC
    """
    results = db.query_raw('answer', query, [])

    if not results:
        print("All module values are numeric. No issues found.")
        return []

    print(f"\nNon-numeric 'module' values found:")
    print(f"{'Module':<20} {'Course':<20} {'Count':>10}")
    print("-" * 52)

    for row in results:
        print(f"{row['module_value']:<20} {row['course']:<20} {row['count']:>10}")

    return results


def normalize_correct_values(db, dry_run=False):
    """Normalize all 'correct' field values to '0' or '1'."""
    print("\n--- Normalizing 'correct' field values ---")

    # Mapping of values to normalized form
    value_mapping = {
        'true': '1',
        'True': '1',
        'TRUE': '1',
        'false': '0',
        'False': '0',
        'FALSE': '0',
        '1': '1',
        '0': '0',
        1: '1',
        0: '0',
        True: '1',
        False: '0',
    }

    # Find records that need updating
    query = """
        SELECT id, data->>'correct' as correct_value
        FROM answer
        WHERE data->>'correct' NOT IN ('0', '1')
          AND data->>'correct' IS NOT NULL
    """
    results = db.query_raw('answer', query, [])

    print(f"Found {len(results)} records to normalize")

    if not results:
        print("No records need normalization.")
        return 0

    updated_count = 0
    error_count = 0

    for row in results:
        record_id = row['id']
        old_value = row['correct_value']

        # Determine new value
        new_value = value_mapping.get(old_value)
        if new_value is None:
            # Try to interpret as truthy/falsy
            if old_value and old_value.lower() in ('true', 'yes', '1', 't', 'y'):
                new_value = '1'
            else:
                new_value = '0'

        if dry_run:
            print(f"  [DRY RUN] Would update {record_id}: {repr(old_value)} -> {repr(new_value)}")
        else:
            try:
                # Update the record
                update_query = """
                    UPDATE answer
                    SET data = jsonb_set(data, '{correct}', $1::jsonb)
                    WHERE id = $2
                """
                # Note: We need to wrap the value in quotes for JSONB
                db.query_raw('answer', update_query, [
                    {'name': '$1', 'value': f'"{new_value}"'},
                    {'name': '$2', 'value': record_id}
                ])
                updated_count += 1
            except Exception as e:
                print(f"  Error updating {record_id}: {e}")
                error_count += 1

    if dry_run:
        print(f"\n[DRY RUN] Would update {len(results)} records")
    else:
        print(f"\nUpdated {updated_count} records, {error_count} errors")

    return updated_count


def run_migration(dry_run=False, fix_correct=False, report_only=False):
    """Run the data type normalization analysis and fixes."""
    from informatics_classroom.database.factory import get_database_adapter

    db = get_database_adapter()

    print("=" * 60)
    print("Answer Data Type Normalization")
    print("=" * 60)
    print(f"Mode: {'REPORT ONLY' if report_only else 'DRY RUN' if dry_run else 'LIVE'}")
    print()

    # Get total answer count
    count_query = "SELECT COUNT(*) as total FROM answer"
    result = db.query_raw('answer', count_query, [])
    total_answers = result[0]['total'] if result else 0
    print(f"Total answers in database: {total_answers}")

    # Analyze correct values
    correct_issues = analyze_correct_values(db)

    # Analyze module values
    module_issues = analyze_module_values(db)

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    if correct_issues:
        print(f"\n'correct' field issues: {len(correct_issues)} distinct non-standard values")
        total_affected = sum(count for _, count in correct_issues)
        print(f"  Total records affected: {total_affected}")

        if fix_correct and not report_only:
            normalize_correct_values(db, dry_run=dry_run)
        elif not report_only:
            print("\n  To fix, run with --fix-correct flag")
    else:
        print("\n'correct' field: All values are normalized (0 or 1)")

    if module_issues:
        print(f"\n'module' field: {len(module_issues)} non-numeric values found")
        print("  NOTE: These may be intentional (e.g., 'ohdsi24_2', 'pmap_11')")
        print("  Review manually before making changes")
    else:
        print("\n'module' field: All values are numeric")

    if report_only:
        print("\nThis was a REPORT ONLY run. No changes were made.")
    elif dry_run:
        print("\nThis was a DRY RUN. No changes were made.")
        print("Run without --dry-run to apply changes.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Normalize answer data types')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview changes without modifying database')
    parser.add_argument('--fix-correct', action='store_true',
                        help='Normalize correct field values to 0/1')
    parser.add_argument('--report-only', action='store_true',
                        help='Only report issues, do not fix anything')
    args = parser.parse_args()

    run_migration(dry_run=args.dry_run, fix_correct=args.fix_correct,
                  report_only=args.report_only)
