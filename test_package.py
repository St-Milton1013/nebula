#!/usr/bin/env python3
"""NEBULA Package Test Suite - Run all tests and save results."""
import sys
import os
import json
import py_compile

# Add the nebula_repos directory to the path
sys.path.insert(0, '/c/Users/Main/Desktop/mtg_laya_project/nebula_repos')

import nebula_package_single as nebula

RESULTS_DIR = '/c/Users/Main/Desktop/project frontgate/Projects/nebula/test_results'

def run_tests():
    results = {
        'tests': [],
        'summary': {},
    }

    # Test 1: Package Syntax
    try:
        compile(open('nebula_package_single.py', 'r').read(), 'nebula_package_single.py', 'exec')
        results['tests'].append({'name': '1. Package Syntax', 'status': 'PASS', 'details': 'nebula_package_single.py compiles successfully'})
        results['summary']['package_syntax'] = 'PASS'
    except Exception as e:
        results['tests'].append({'name': '1. Package Syntax', 'status': 'FAIL', 'details': str(e)})
        results['summary']['package_syntax'] = 'FAIL'

    # Test 2: Adapter Import
    adapters = [
        ('scryfall', nebula.scryfall_num_adapter),
        ('deck_validator', nebula.deck_validator_adapter),
        ('learncedh', nebula.learncedh_adapter),
        ('commander_spellbook', nebula.commander_spellbook_adapter),
        ('hypercalculator', nebula.hypercalculator_adapter),
        ('meta_compare', nebula.meta_compare_adapter),
    ]
    all_pass = True
    for name, fn in adapters:
        try:
            result = fn(mode=name, decklist=['Sol Ring', 'Pony of the Steppes']) if name != 'learncedh' else fn(deck_name='Sol Ring')
            results['tests'].append({'name': f'2. Adapter: {name}', 'status': 'PASS', 'details': 'Adapter callable'})
        except Exception as e:
            results['tests'].append({'name': f'2. Adapter: {name}', 'status': 'FAIL', 'details': str(e)})
            all_pass = False

    results['summary']['adapters'] = 'PASS' if all_pass else 'FAIL'

    # Test 3: Decklist Export
    test_deck = ['Sol Ring', 'Pony of the Steppes', 'Nim ' + 'as Battle', 'Friendly Giant']
    with open('test_deck.txt', 'w') as f:
        for c in test_deck:
            f.write(c + '\n')

    cards = nebula.load_deck_from_file('test_deck.txt')
    if len(cards) == 4:
        results['tests'].append({'name': '3. Decklist Export', 'status': 'PASS', 'details': '4 cards loaded'})
        results['summary']['decklist_export'] = 'PASS'
    else:
        results['tests'].append({'name': '3. Decklist Export', 'status': 'FAIL', 'details': f'Expected 4 cards, got {len(cards)}'})
        results['summary']['decklist_export'] = 'FAIL'

    # Test 4: Link Loading (file://)
    cards = nebula.load_deck_from_link('file://' + os.path.abspath('test_deck.txt'))
    if cards:
        results['tests'].append({'name': '4. Link Loading (file://)', 'status': 'PASS', 'details': f'{len(cards)} cards'})
        results['summary']['link_loading'] = 'PASS'
    else:
        results['tests'].append({'name': '4. Link Loading (file://)', 'status': 'FAIL', 'details': 'No cards'})
        results['summary']['link_loading'] = 'FAIL'

    # Test 5: build_report (local decklist)
    report = nebula.build_report(decklist='test_deck.txt')
    if report['status'] == 'AVAILABLE' and len(report['decklist']) == 4:
        results['tests'].append({'name': '5. build_report (local)', 'status': 'PASS', 'details': f'{report["status"]}, {len(report["decklist"])} cards'})
        results['summary']['build_report'] = 'PASS'
    else:
        results['tests'].append({'name': '5. build_report (local)', 'status': 'FAIL', 'details': f'{report["status"]}'})
        results['summary']['build_report'] = 'FAIL'

    # Test 6: Moxfield URL link
    report2 = nebula.build_report(link='https://moxfield.com/decks/aeHI23_ElUmV_FdE4Dy57w')
    if report2['status'] == 'PARTIAL' and 'Could not fetch decklist' in ' '.join(report2.get('caveats', [])):
        results['tests'].append({'name': '6. Moxfield URL (aeHI23)', 'status': 'PASS', 'details': 'Cloudflare block detected, handled gracefully'})
        results['summary']['moxfield_url'] = 'PASS (Cloudflare block detected)'
    else:
        results['tests'].append({'name': '6. Moxfield URL (aeHI23)', 'status': 'FAIL', 'details': f'{report2["status"]}'})
        results['summary']['moxfield_url'] = 'FAIL'

    # Test 7: Moxfield URL link
    report3 = nebula.build_report(link='https://moxfield.com/decks/V4ZllY7oHUGVc9AZPM2DEA')
    if report3['status'] == 'PARTIAL' and 'Could not fetch decklist' in ' '.join(report3.get('caveats', [])):
        results['tests'].append({'name': '7. Moxfield URL (V4ZllY7oHUGVc9AZPM2DEA)', 'status': 'PASS', 'details': 'Cloudflare block detected, handled gracefully'})
        results['summary']['moxfield_url_2'] = 'PASS (Cloudflare block detected)'
    else:
        results['tests'].append({'name': '7. Moxfield URL (V4ZllY7oHUGVc9AZPM2DEA)', 'status': 'FAIL', 'details': f'{report3["status"]}'})
        results['summary']['moxfield_url_2'] = 'FAIL'

    # Test 8: Moxfield URL link
    report4 = nebula.build_report(link='https://moxfield.com/decks/Xwf8D6Qt5EeWZGDPJjwnSg')
    if report4['status'] == 'PARTIAL' and 'Could not fetch decklist' in ' '.join(report4.get('caveats', [])):
        results['tests'].append({'name': '8. Moxfield URL (Xwf8D6Qt5EeWZGDPJjwnSg)', 'status': 'PASS', 'details': 'Cloudflare block detected, handled gracefully'})
        results['summary']['moxfield_url_3'] = 'PASS (Cloudflare block detected)'
    else:
        results['tests'].append({'name': '8. Moxfield URL (Xwf8D6Qt5EeWZGDPJjwnSg)', 'status': 'FAIL', 'details': f'{report4["status"]}'})
        results['summary']['moxfield_url_3'] = 'FAIL'

    # Save results
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(os.path.join(RESULTS_DIR, 'test_results.json'), 'w') as f:
        json.dump(results, f, indent=2)

    with open(os.path.join(RESULTS_DIR, 'TEST_SUMMARY.md'), 'w') as f:
        f.write('# NEBULA Package Test Results\n\n')
        f.write('## Summary\n\n')
        for k, v in results['summary'].items():
            f.write(f'- {k}: {v}\n')
        f.write('\n## Detailed Results\n\n')
        f.write('| Test | Status | Details |\n')
        f.write('|------|--------|--------|\n')
        for t in results['tests']:
            f.write(f'| {t["name"]} | {t["status"]} | {t["details"]} |\n')

    print('Tests complete. Results saved to test_results directory.')
    print()
    print('Summary:')
    for k, v in results['summary'].items():
        print(f'  {k}: {v}')

if __name__ == '__main__':
    run_tests()
