#!/usr/bin/env python3
"""
NEBULA EXPORT PACKAGE GENERATOR

Generates a self-contained export of a deck for inspection.
Usage:
    python export_generator.py --decklist <file> --output <file>
    python export_generator.py --link <url> --output <file>
    python export_generator.py --single <file> --output <file>
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import argparse
import json
import sys
import os

# Add the package to path so we can import nebula_package_single
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import from the single-file package
import nebula_package_single as nebula
from nebula_package_single import (
    load_deck_from_file,
    load_deck_from_link,
    build_report,
    print_report,
)

def export_json(deck_cards, output_file):
    """Export deck as JSON."""
    report = {
        'source': 'exported',
        'decklist': deck_cards,
        'count': len(deck_cards),
    }
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    print(f'Exported {len(deck_cards)} cards to {output_file}')

def export_text(deck_cards, output_file):
    """Export deck as text (one card per line)."""
    with open(output_file, 'w') as f:
        for card in deck_cards:
            f.write(card + chr(10))
    print(f'Exported {len(deck_cards)} cards to {output_file}')

def export_report(link=None, decklist=None, output_file='report.json', format='json'):
    """Build and export a full analysis report."""
    report = build_report(link=link, decklist=decklist)
    with open(output_file, 'w') as f:
        if format == 'json':
            json.dump(report, f, indent=2, default=str)
        else:
            f.write(print_report(report, 'text'))
    print(f'Saved report to {output_file}')
    return report

def main():
    parser = argparse.ArgumentParser(
        description='NEBULA Export Package Generator'
    )
    parser.add_argument(
        '--decklist', '-d',
        help='Local decklist file to export'
    )
    parser.add_argument(
        '--link', '-l',
        help='Moxfield/Archidekt deck link to fetch and export'
    )
    parser.add_argument(
        '--single', '-s',
        help='Single file to concatenate into one package (creates nebula_package_single.py)'
    )
    parser.add_argument(
        '--output', '-o',
        default='nebula_export.json',
        help='Output file path'
    )
    parser.add_argument(
        '--format', '-f',
        default='json',
        choices=['json', 'text'],
        help='Output format'
    )
    args = parser.parse_args()

    if args.decklist:
        cards = load_deck_from_file(args.decklist)
        if args.format == 'json':
            export_json(cards, args.output)
        else:
            export_text(cards, args.output)
    elif args.link:
        deck = load_deck_from_link(args.link)
        if deck is None:
            print('ERROR: Could not fetch decklist from link')
            print('Note: Moxfield/Archidekt URLs often require Cloudflare bypass')
            print('Falling back to local decklist if provided')
            if args.decklist:
                cards = load_deck_from_file(args.decklist)
                if args.format == 'json':
                    export_json(cards, args.output)
                else:
                    export_text(cards, args.output)
            else:
                print('No decklist provided for fallback')
        else:
            print(f'Fetched {len(deck)} cards from link')
            if args.format == 'json':
                export_json(deck, args.output)
            else:
                export_text(deck, args.output)
    elif args.single:
        # Generate the single-file package
        with open(args.single, 'r') as f:
            package_content = f.read()
        output_path = os.path.splitext(args.output)[0] + '_package.py'
        with open(output_path, 'w') as f:
            f.write(package_content)
        print(f'Generated single-file package: {output_path}')
    else:
        parser.error('Provide --decklist, --link, or --single')

if __name__ == '__main__':
    main()
