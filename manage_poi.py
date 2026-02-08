#!/usr/bin/env python3
"""
Command-line utility to manage the planes of interest database.

Usage:
    python manage_poi.py list
    python manage_poi.py add <icao24> [--tail <tailnumber>] [--model <make/model>] [--notes <notes>]
    python manage_poi.py get <icao24|tailnumber>
    python manage_poi.py update <icao24> [--tail <tailnumber>] [--model <make/model>] [--notes <notes>]
    python manage_poi.py remove <icao24>
"""

import argparse
import sys
from pathlib import Path

# Add glycol to the path
sys.path.insert(0, str(Path(__file__).parent))

from glycol.poi import POIDatabase, PlaneOfInterest


def list_planes(db: POIDatabase):
    """List all planes in the database."""
    planes = db.list_all()
    if not planes:
        print("No planes in database")
        return

    print(f"\n{'Name':<20} {'ICAO24':<10} {'Tail Number':<12} {'Make/Model':<25} {'Notes':<20}")
    print("-" * 95)
    for plane in planes:
        print(
            f"{plane.name:<20} {plane.icao24:<10} {plane.tailnumber:<12} "
            f"{plane.make_model:<25} {plane.notes:<20}"
        )
    print(f"\nTotal: {len(planes)} planes")


def add_plane(db: POIDatabase, args):
    """Add a plane to the database."""
    plane = PlaneOfInterest(
        tailnumber=args.tail,
        name=args.name or "",
        icao24=args.icao24 or "",
        make_model=args.model or "",
        notes=args.notes or ""
    )

    if db.add(plane):
        print(f"Added plane: {plane.name or plane.tailnumber}")
    else:
        print(f"Plane with tail number {plane.tailnumber} already exists")
        sys.exit(1)


def get_plane(db: POIDatabase, args):
    """Get a plane by ICAO24 or tail number."""
    # Try ICAO24 first
    plane = db.get_by_icao24(args.identifier)
    if not plane:
        # Try tail number
        plane = db.get_by_tailnumber(args.identifier)

    if not plane:
        print(f"Plane not found: {args.identifier}")
        sys.exit(1)

    print(f"\nName:        {plane.name}")
    print(f"ICAO24:      {plane.icao24}")
    print(f"Tail Number: {plane.tailnumber}")
    print(f"Make/Model:  {plane.make_model}")
    print(f"Notes:       {plane.notes}")


def update_plane(db: POIDatabase, args):
    """Update a plane's details."""
    updates = {}
    if args.name is not None:
        updates["name"] = args.name
    if args.icao24 is not None:
        updates["icao24"] = args.icao24
    if args.model is not None:
        updates["make_model"] = args.model
    if args.notes is not None:
        updates["notes"] = args.notes

    if not updates:
        print("No updates provided")
        sys.exit(1)

    # Update by tail number
    plane = db.get_by_tailnumber(args.tail)
    if not plane:
        print(f"Plane not found: {args.tail}")
        sys.exit(1)

    for key, value in updates.items():
        setattr(plane, key, value)

    db.save()
    print(f"Updated plane: {args.tail}")


def remove_plane(db: POIDatabase, args):
    """Remove a plane from the database."""
    plane = db.get_by_tailnumber(args.tail)
    if not plane:
        print(f"Plane not found: {args.tail}")
        sys.exit(1)

    db.planes.remove(plane)
    db.save()
    print(f"Removed plane: {args.tail}")


def list_categories(db: POIDatabase):
    """List all available categories."""
    categories = db.list_categories()
    if not categories:
        print("No categories found")
        return

    print("\nAvailable categories:")
    for cat in categories:
        marker = " (current)" if cat == db.category else ""
        print(f"  - {cat}{marker}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Manage planes of interest database")
    parser.add_argument(
        "--data-dir",
        dest="data_dir",
        default=None,
        help="Directory containing data files (defaults to glycol/data/)",
    )
    parser.add_argument(
        "--category",
        dest="category",
        default="default",
        help="Category/dictionary to use (defaults to 'default')",
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # List command
    subparsers.add_parser("list", help="List all planes")

    # Categories command
    subparsers.add_parser("categories", help="List all available categories")

    # Add command
    add_parser = subparsers.add_parser("add", help="Add a plane")
    add_parser.add_argument("tail", help="Tail number (e.g., N123AB)")
    add_parser.add_argument("--name", help="Aircraft name (e.g., Clipper America)")
    add_parser.add_argument("--icao24", help="ICAO24 address (hex, optional)")
    add_parser.add_argument("--model", help="Make and model (e.g., Cessna 172)")
    add_parser.add_argument("--notes", help="Additional notes")

    # Get command
    get_parser = subparsers.add_parser("get", help="Get a plane by ICAO24 or tail number")
    get_parser.add_argument("identifier", help="ICAO24 address or tail number")

    # Update command
    update_parser = subparsers.add_parser("update", help="Update a plane")
    update_parser.add_argument("tail", help="Tail number")
    update_parser.add_argument("--name", help="Aircraft name")
    update_parser.add_argument("--icao24", help="ICAO24 address")
    update_parser.add_argument("--model", help="Make and model")
    update_parser.add_argument("--notes", help="Additional notes")

    # Remove command
    remove_parser = subparsers.add_parser("remove", help="Remove a plane")
    remove_parser.add_argument("tail", help="Tail number")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Initialize database
    db = POIDatabase(data_dir=args.data_dir, category=args.category)

    # Execute command
    if args.command == "list":
        list_planes(db)
    elif args.command == "categories":
        list_categories(db)
    elif args.command == "add":
        add_plane(db, args)
    elif args.command == "get":
        get_plane(db, args)
    elif args.command == "update":
        update_plane(db, args)
    elif args.command == "remove":
        remove_plane(db, args)


if __name__ == "__main__":
    main()
