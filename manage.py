#!/usr/bin/env python3
"""
Interactive management utility for Glycol databases.

Supports managing both planes of interest (POI) and aircraft type groups/glossary
through either command-line arguments or an interactive menu-driven interface.
"""

import argparse
import sys
from pathlib import Path

# Add glycol to the path
sys.path.insert(0, str(Path(__file__).parent))

from glycol.poi import POIDatabase, PlaneOfInterest
from glycol.groups import GroupsDatabase, AircraftType


# =============================================================================
# POI Management Functions
# =============================================================================

def poi_list(db: POIDatabase):
    """List all planes in the database."""
    planes = db.list_all()
    if not planes:
        print("\nNo planes in database")
        return

    print(f"\n{'Name':<20} {'ICAO24':<10} {'Tail Number':<12} {'Make/Model':<25} {'Notes':<30}")
    print("-" * 107)
    for plane in planes:
        print(
            f"{plane.name:<20} {plane.icao24:<10} {plane.tailnumber:<12} "
            f"{plane.make_model:<25} {plane.notes:<30}"
        )
    print(f"\nTotal: {len(planes)} planes")


def poi_add_interactive(db: POIDatabase):
    """Interactively add a plane."""
    print("\n=== Add Plane ===")
    tail = input("Tail number (required): ").strip()
    if not tail:
        print("Error: Tail number is required")
        return

    name = input("Name (optional): ").strip()
    icao24 = input("ICAO24 address (optional): ").strip()
    model = input("Make/Model (optional): ").strip()
    notes = input("Notes (optional): ").strip()

    plane = PlaneOfInterest(
        tailnumber=tail,
        name=name,
        icao24=icao24,
        make_model=model,
        notes=notes
    )

    if db.add(plane):
        print(f"\n✓ Added plane: {plane.name or plane.tailnumber}")
    else:
        print(f"\n✗ Plane with tail number {plane.tailnumber} already exists")


def poi_get_interactive(db: POIDatabase):
    """Interactively get a plane's details."""
    print("\n=== Get Plane Details ===")
    identifier = input("Enter tail number or ICAO24: ").strip()

    plane = db.get_by_icao24(identifier)
    if not plane:
        plane = db.get_by_tailnumber(identifier)

    if not plane:
        print(f"\n✗ Plane not found: {identifier}")
        return

    print(f"\nName:        {plane.name}")
    print(f"ICAO24:      {plane.icao24}")
    print(f"Tail Number: {plane.tailnumber}")
    print(f"Make/Model:  {plane.make_model}")
    print(f"Notes:       {plane.notes}")


def poi_update_interactive(db: POIDatabase):
    """Interactively update a plane."""
    print("\n=== Update Plane ===")
    tail = input("Tail number: ").strip()

    plane = db.get_by_tailnumber(tail)
    if not plane:
        print(f"\n✗ Plane not found: {tail}")
        return

    print(f"\nCurrent values:")
    print(f"  Name:       {plane.name}")
    print(f"  ICAO24:     {plane.icao24}")
    print(f"  Make/Model: {plane.make_model}")
    print(f"  Notes:      {plane.notes}")

    print("\nEnter new values (press Enter to keep current):")
    name = input(f"Name [{plane.name}]: ").strip()
    icao24 = input(f"ICAO24 [{plane.icao24}]: ").strip()
    model = input(f"Make/Model [{plane.make_model}]: ").strip()
    notes = input(f"Notes [{plane.notes}]: ").strip()

    if name:
        plane.name = name
    if icao24:
        plane.icao24 = icao24
    if model:
        plane.make_model = model
    if notes:
        plane.notes = notes

    db.save()
    print(f"\n✓ Updated plane: {tail}")


def poi_remove_interactive(db: POIDatabase):
    """Interactively remove a plane."""
    print("\n=== Remove Plane ===")
    tail = input("Tail number: ").strip()

    plane = db.get_by_tailnumber(tail)
    if not plane:
        print(f"\n✗ Plane not found: {tail}")
        return

    confirm = input(f"Remove {plane.name or tail}? (yes/no): ").strip().lower()
    if confirm == "yes":
        db.planes.remove(plane)
        db.save()
        print(f"\n✓ Removed plane: {tail}")
    else:
        print("\nCancelled")


def poi_categories(db: POIDatabase):
    """List all POI categories."""
    categories = db.list_categories()
    if not categories:
        print("\nNo categories found")
        return

    print("\nAvailable POI categories:")
    for cat in categories:
        marker = " (current)" if cat == db.category else ""
        print(f"  - {cat}{marker}")
    print()


# =============================================================================
# Groups Management Functions
# =============================================================================

def groups_list(db: GroupsDatabase):
    """List all groups."""
    groups = db.list_groups()
    if not groups:
        print("\nNo groups in database")
        return

    print("\nAircraft Groups:")
    print("-" * 60)
    for group in sorted(groups):
        codes = db.get_group(group)
        print(f"{group:<20} ({len(codes)} aircraft)")
    print(f"\nTotal: {len(groups)} groups")


def groups_view_interactive(db: GroupsDatabase):
    """View aircraft in a group."""
    print("\n=== View Group ===")
    groups = db.list_groups()
    if not groups:
        print("No groups available")
        return

    print("\nAvailable groups:")
    for i, group in enumerate(sorted(groups), 1):
        print(f"  {i}. {group}")

    choice = input("\nEnter group name or number: ").strip()

    # Handle numeric choice
    if choice.isdigit():
        idx = int(choice) - 1
        sorted_groups = sorted(groups)
        if 0 <= idx < len(sorted_groups):
            group_name = sorted_groups[idx]
        else:
            print("Invalid selection")
            return
    else:
        group_name = choice

    codes = db.get_group(group_name)
    if codes is None:
        print(f"\n✗ Group not found: {group_name}")
        return

    print(f"\n=== {group_name} ===")
    print(f"{'Code':<8} {'Make':<20} {'Model':<30} {'Notes':<40}")
    print("-" * 98)

    for code in sorted(codes):
        aircraft = db.get_aircraft_type(code)
        if aircraft:
            print(f"{code:<8} {aircraft.make:<20} {aircraft.model:<30} {aircraft.notes:<40}")
        else:
            print(f"{code:<8} (not in glossary)")

    print(f"\nTotal: {len(codes)} aircraft")


def groups_create_interactive(db: GroupsDatabase):
    """Interactively create a group."""
    print("\n=== Create Group ===")
    name = input("Group name: ").strip()
    if not name:
        print("Error: Group name is required")
        return

    if db.create_group(name):
        print(f"\n✓ Created group: {name}")
    else:
        print(f"\n✗ Group already exists: {name}")


def groups_add_aircraft_interactive(db: GroupsDatabase):
    """Add aircraft to a group."""
    print("\n=== Add Aircraft to Group ===")
    groups = db.list_groups()
    if not groups:
        print("No groups available. Create a group first.")
        return

    print("\nAvailable groups:")
    for i, group in enumerate(sorted(groups), 1):
        print(f"  {i}. {group}")

    choice = input("\nEnter group name or number: ").strip()

    # Handle numeric choice
    if choice.isdigit():
        idx = int(choice) - 1
        sorted_groups = sorted(groups)
        if 0 <= idx < len(sorted_groups):
            group_name = sorted_groups[idx]
        else:
            print("Invalid selection")
            return
    else:
        group_name = choice

    if group_name not in groups:
        print(f"\n✗ Group not found: {group_name}")
        return

    code = input("Aircraft type code: ").strip().upper()
    if not code:
        print("Error: Aircraft code is required")
        return

    if db.add_to_group(group_name, code):
        print(f"\n✓ Added {code} to {group_name}")
    else:
        print(f"\n✗ Could not add {code} to {group_name}")


def groups_remove_aircraft_interactive(db: GroupsDatabase):
    """Remove aircraft from a group."""
    print("\n=== Remove Aircraft from Group ===")
    groups = db.list_groups()
    if not groups:
        print("No groups available")
        return

    print("\nAvailable groups:")
    for i, group in enumerate(sorted(groups), 1):
        print(f"  {i}. {group}")

    choice = input("\nEnter group name or number: ").strip()

    # Handle numeric choice
    if choice.isdigit():
        idx = int(choice) - 1
        sorted_groups = sorted(groups)
        if 0 <= idx < len(sorted_groups):
            group_name = sorted_groups[idx]
        else:
            print("Invalid selection")
            return
    else:
        group_name = choice

    codes = db.get_group(group_name)
    if codes is None:
        print(f"\n✗ Group not found: {group_name}")
        return

    if not codes:
        print(f"\nGroup {group_name} is empty")
        return

    print(f"\nAircraft in {group_name}:")
    for code in sorted(codes):
        print(f"  - {code}")

    code = input("\nAircraft type code to remove: ").strip().upper()
    if db.remove_from_group(group_name, code):
        print(f"\n✓ Removed {code} from {group_name}")
    else:
        print(f"\n✗ Could not remove {code} from {group_name}")


def groups_delete_interactive(db: GroupsDatabase):
    """Delete a group."""
    print("\n=== Delete Group ===")
    groups = db.list_groups()
    if not groups:
        print("No groups available")
        return

    print("\nAvailable groups:")
    for i, group in enumerate(sorted(groups), 1):
        print(f"  {i}. {group}")

    choice = input("\nEnter group name or number: ").strip()

    # Handle numeric choice
    if choice.isdigit():
        idx = int(choice) - 1
        sorted_groups = sorted(groups)
        if 0 <= idx < len(sorted_groups):
            group_name = sorted_groups[idx]
        else:
            print("Invalid selection")
            return
    else:
        group_name = choice

    confirm = input(f"Delete group '{group_name}'? (yes/no): ").strip().lower()
    if confirm == "yes":
        if db.delete_group(group_name):
            print(f"\n✓ Deleted group: {group_name}")
        else:
            print(f"\n✗ Could not delete group: {group_name}")
    else:
        print("\nCancelled")


# =============================================================================
# Glossary Management Functions
# =============================================================================

def glossary_list(db: GroupsDatabase):
    """List all aircraft types in glossary."""
    types = db.list_all_types()
    if not types:
        print("\nNo aircraft types in glossary")
        return

    print(f"\n{'Code':<8} {'Make':<20} {'Model':<30} {'Notes':<40}")
    print("-" * 98)
    for aircraft in sorted(types, key=lambda a: a.code):
        print(f"{aircraft.code:<8} {aircraft.make:<20} {aircraft.model:<30} {aircraft.notes:<40}")
    print(f"\nTotal: {len(types)} aircraft types")


def glossary_get_interactive(db: GroupsDatabase):
    """Get details for an aircraft type."""
    print("\n=== Get Aircraft Type ===")
    code = input("Aircraft type code: ").strip().upper()

    aircraft = db.get_aircraft_type(code)
    if not aircraft:
        print(f"\n✗ Aircraft type not found: {code}")
        return

    print(f"\nCode:  {aircraft.code}")
    print(f"Make:  {aircraft.make}")
    print(f"Model: {aircraft.model}")
    print(f"Notes: {aircraft.notes}")


def glossary_add_interactive(db: GroupsDatabase):
    """Add an aircraft type to glossary."""
    print("\n=== Add Aircraft Type ===")
    code = input("Type code (required): ").strip().upper()
    if not code:
        print("Error: Type code is required")
        return

    make = input("Make: ").strip()
    model = input("Model: ").strip()
    notes = input("Notes: ").strip()

    aircraft = AircraftType(code=code, make=make, model=model, notes=notes)

    if db.add_aircraft_type(aircraft):
        print(f"\n✓ Added aircraft type: {code}")
    else:
        print(f"\n✗ Aircraft type already exists: {code}")


def glossary_update_interactive(db: GroupsDatabase):
    """Update an aircraft type."""
    print("\n=== Update Aircraft Type ===")
    code = input("Type code: ").strip().upper()

    aircraft = db.get_aircraft_type(code)
    if not aircraft:
        print(f"\n✗ Aircraft type not found: {code}")
        return

    print(f"\nCurrent values:")
    print(f"  Make:  {aircraft.make}")
    print(f"  Model: {aircraft.model}")
    print(f"  Notes: {aircraft.notes}")

    print("\nEnter new values (press Enter to keep current):")
    make = input(f"Make [{aircraft.make}]: ").strip()
    model = input(f"Model [{aircraft.model}]: ").strip()
    notes = input(f"Notes [{aircraft.notes}]: ").strip()

    updates = {}
    if make:
        updates["make"] = make
    if model:
        updates["model"] = model
    if notes:
        updates["notes"] = notes

    if updates:
        db.update_aircraft_type(code, **updates)
        print(f"\n✓ Updated aircraft type: {code}")
    else:
        print("\nNo changes made")


def glossary_remove_interactive(db: GroupsDatabase):
    """Remove an aircraft type from glossary."""
    print("\n=== Remove Aircraft Type ===")
    code = input("Type code: ").strip().upper()

    aircraft = db.get_aircraft_type(code)
    if not aircraft:
        print(f"\n✗ Aircraft type not found: {code}")
        return

    confirm = input(f"Remove {code} ({aircraft.model})? (yes/no): ").strip().lower()
    if confirm == "yes":
        db.remove_aircraft_type(code)
        print(f"\n✓ Removed aircraft type: {code}")
    else:
        print("\nCancelled")


def glossary_search_interactive(db: GroupsDatabase):
    """Search for aircraft types."""
    print("\n=== Search Aircraft Types ===")
    query = input("Search query: ").strip()

    results = db.search_types(query)
    if not results:
        print(f"\nNo results found for: {query}")
        return

    print(f"\n{'Code':<8} {'Make':<20} {'Model':<30} {'Notes':<40}")
    print("-" * 98)
    for aircraft in sorted(results, key=lambda a: a.code):
        print(f"{aircraft.code:<8} {aircraft.make:<20} {aircraft.model:<30} {aircraft.notes:<40}")
    print(f"\nFound: {len(results)} results")


# =============================================================================
# Interactive Mode
# =============================================================================

def interactive_mode(data_dir=None):
    """Run in interactive menu mode."""
    poi_db = POIDatabase(data_dir=data_dir)
    groups_db = GroupsDatabase(data_dir=data_dir)

    while True:
        print("\n" + "=" * 60)
        print("GLYCOL DATABASE MANAGER")
        print("=" * 60)
        print("\nMain Menu:")
        print("  1. Planes of Interest (POI)")
        print("  2. Aircraft Groups")
        print("  3. Aircraft Glossary")
        print("  0. Exit")

        choice = input("\nSelect option: ").strip()

        if choice == "1":
            poi_menu(poi_db)
        elif choice == "2":
            groups_menu(groups_db)
        elif choice == "3":
            glossary_menu(groups_db)
        elif choice == "0":
            print("\nGoodbye!")
            break
        else:
            print("\nInvalid choice")


def poi_menu(db: POIDatabase):
    """POI management menu."""
    while True:
        print("\n" + "-" * 60)
        print(f"PLANES OF INTEREST - Category: {db.category}")
        print("-" * 60)
        print("\n  1. List all planes")
        print("  2. Get plane details")
        print("  3. Add plane")
        print("  4. Update plane")
        print("  5. Remove plane")
        print("  6. List categories")
        print("  7. Switch category")
        print("  0. Back to main menu")

        choice = input("\nSelect option: ").strip()

        if choice == "1":
            poi_list(db)
        elif choice == "2":
            poi_get_interactive(db)
        elif choice == "3":
            poi_add_interactive(db)
        elif choice == "4":
            poi_update_interactive(db)
        elif choice == "5":
            poi_remove_interactive(db)
        elif choice == "6":
            poi_categories(db)
        elif choice == "7":
            categories = db.list_categories()
            print("\nAvailable categories:")
            for cat in categories:
                print(f"  - {cat}")
            new_cat = input("\nEnter category name: ").strip()
            if new_cat:
                db.switch_category(new_cat)
                print(f"\n✓ Switched to category: {new_cat}")
        elif choice == "0":
            break
        else:
            print("\nInvalid choice")


def groups_menu(db: GroupsDatabase):
    """Groups management menu."""
    while True:
        print("\n" + "-" * 60)
        print("AIRCRAFT GROUPS")
        print("-" * 60)
        print("\n  1. List all groups")
        print("  2. View group details")
        print("  3. Create group")
        print("  4. Add aircraft to group")
        print("  5. Remove aircraft from group")
        print("  6. Delete group")
        print("  0. Back to main menu")

        choice = input("\nSelect option: ").strip()

        if choice == "1":
            groups_list(db)
        elif choice == "2":
            groups_view_interactive(db)
        elif choice == "3":
            groups_create_interactive(db)
        elif choice == "4":
            groups_add_aircraft_interactive(db)
        elif choice == "5":
            groups_remove_aircraft_interactive(db)
        elif choice == "6":
            groups_delete_interactive(db)
        elif choice == "0":
            break
        else:
            print("\nInvalid choice")


def glossary_menu(db: GroupsDatabase):
    """Glossary management menu."""
    while True:
        print("\n" + "-" * 60)
        print("AIRCRAFT GLOSSARY")
        print("-" * 60)
        print("\n  1. List all aircraft types")
        print("  2. Get aircraft type details")
        print("  3. Search aircraft types")
        print("  4. Add aircraft type")
        print("  5. Update aircraft type")
        print("  6. Remove aircraft type")
        print("  0. Back to main menu")

        choice = input("\nSelect option: ").strip()

        if choice == "1":
            glossary_list(db)
        elif choice == "2":
            glossary_get_interactive(db)
        elif choice == "3":
            glossary_search_interactive(db)
        elif choice == "4":
            glossary_add_interactive(db)
        elif choice == "5":
            glossary_update_interactive(db)
        elif choice == "6":
            glossary_remove_interactive(db)
        elif choice == "0":
            break
        else:
            print("\nInvalid choice")


# =============================================================================
# CLI Mode (backward compatibility)
# =============================================================================

def cli_mode():
    """Run in CLI mode with arguments."""
    parser = argparse.ArgumentParser(
        description="Manage Glycol databases (POI and aircraft groups)",
        epilog="Run without arguments to enter interactive mode"
    )
    parser.add_argument(
        "--data-dir",
        dest="data_dir",
        default=None,
        help="Directory containing data files (defaults to glycol/data/)",
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Run in interactive mode"
    )
    parser.add_argument(
        "--category",
        dest="category",
        default="default",
        help="POI category/dictionary to use (defaults to 'default')",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # POI commands
    poi_parser = subparsers.add_parser("poi", help="Planes of Interest commands")
    poi_sub = poi_parser.add_subparsers(dest="poi_command")

    poi_sub.add_parser("list", help="List all planes")
    poi_sub.add_parser("categories", help="List POI categories")

    poi_add = poi_sub.add_parser("add", help="Add a plane")
    poi_add.add_argument("tail", help="Tail number")
    poi_add.add_argument("--name", help="Aircraft name")
    poi_add.add_argument("--icao24", help="ICAO24 address")
    poi_add.add_argument("--model", help="Make and model")
    poi_add.add_argument("--notes", help="Notes")

    poi_get = poi_sub.add_parser("get", help="Get plane details")
    poi_get.add_argument("identifier", help="Tail number or ICAO24")

    # Groups commands
    groups_parser = subparsers.add_parser("groups", help="Aircraft groups commands")
    groups_sub = groups_parser.add_subparsers(dest="groups_command")

    groups_sub.add_parser("list", help="List all groups")

    groups_view = groups_sub.add_parser("view", help="View group details")
    groups_view.add_argument("name", help="Group name")

    # Glossary commands
    glossary_parser = subparsers.add_parser("glossary", help="Aircraft glossary commands")
    glossary_sub = glossary_parser.add_subparsers(dest="glossary_command")

    glossary_sub.add_parser("list", help="List all aircraft types")

    glossary_get = glossary_sub.add_parser("get", help="Get aircraft type details")
    glossary_get.add_argument("code", help="Aircraft type code")

    glossary_search = glossary_sub.add_parser("search", help="Search aircraft types")
    glossary_search.add_argument("query", help="Search query")

    args = parser.parse_args()

    # Interactive mode if no command or -i flag
    if args.interactive or not args.command:
        interactive_mode(args.data_dir)
        return

    # CLI mode
    if args.command == "poi":
        db = POIDatabase(data_dir=args.data_dir, category=args.category)
        if args.poi_command == "list":
            poi_list(db)
        elif args.poi_command == "categories":
            poi_categories(db)
        elif args.poi_command == "add":
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
                print(f"Plane already exists: {args.tail}")
                sys.exit(1)
        elif args.poi_command == "get":
            plane = db.get_by_icao24(args.identifier) or db.get_by_tailnumber(args.identifier)
            if plane:
                print(f"\nCode:        {plane.tailnumber}")
                print(f"Name:        {plane.name}")
                print(f"ICAO24:      {plane.icao24}")
                print(f"Make/Model:  {plane.make_model}")
                print(f"Notes:       {plane.notes}")
            else:
                print(f"Plane not found: {args.identifier}")
                sys.exit(1)

    elif args.command == "groups":
        db = GroupsDatabase(data_dir=args.data_dir)
        if args.groups_command == "list":
            groups_list(db)
        elif args.groups_command == "view":
            codes = db.get_group(args.name)
            if codes:
                print(f"\n{args.name}:")
                for code in sorted(codes):
                    aircraft = db.get_aircraft_type(code)
                    if aircraft:
                        print(f"  {code:<8} - {aircraft.make} {aircraft.model}")
                    else:
                        print(f"  {code}")
            else:
                print(f"Group not found: {args.name}")
                sys.exit(1)

    elif args.command == "glossary":
        db = GroupsDatabase(data_dir=args.data_dir)
        if args.glossary_command == "list":
            glossary_list(db)
        elif args.glossary_command == "get":
            aircraft = db.get_aircraft_type(args.code)
            if aircraft:
                print(f"\nCode:  {aircraft.code}")
                print(f"Make:  {aircraft.make}")
                print(f"Model: {aircraft.model}")
                print(f"Notes: {aircraft.notes}")
            else:
                print(f"Aircraft type not found: {args.code}")
                sys.exit(1)
        elif args.glossary_command == "search":
            results = db.search_types(args.query)
            if results:
                for aircraft in sorted(results, key=lambda a: a.code):
                    print(f"{aircraft.code:<8} - {aircraft.make} {aircraft.model}")
            else:
                print(f"No results found for: {args.query}")


def main():
    """Main entry point."""
    cli_mode()


if __name__ == "__main__":
    main()
