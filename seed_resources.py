#!/usr/bin/env python3
"""
Script to seed default ExCITE resources into the database.
"""

import sys
import os

# Add the project to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from informatics_classroom.classroom.resources_routes import seed_default_resources

def main():
    """Seed default resources"""
    print("Seeding default ExCITE resources...")
    print("-" * 60)

    try:
        results = seed_default_resources()

        print("\n✓ Seeding Complete!")
        print("-" * 60)

        if results['seeded']:
            print(f"\n✓ Created {len(results['seeded'])} resources:")
            for resource in results['seeded']:
                print(f"  - {resource}")

        if results['existing']:
            print(f"\nℹ {len(results['existing'])} resources already exist:")
            for resource in results['existing']:
                print(f"  - {resource}")

        if results['errors']:
            print(f"\n✗ {len(results['errors'])} errors occurred:")
            for error in results['errors']:
                print(f"  - {error['resource']}: {error['error']}")

        print("\n" + "-" * 60)
        print(f"Summary: {len(results['seeded'])} created, {len(results['existing'])} existing, {len(results['errors'])} errors")

    except Exception as e:
        print(f"\n✗ Error seeding resources: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
