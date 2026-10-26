import io

path = 'EXPORT_GENERATOR_PLAN.md'
with io.open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old = '''6. **Banned cards**: Check against the Commander ban list (if cached)

**Output:** A validation report with:

- Status: AVAILABLE / PARTIAL (for any format issue found)
- Card count
- Commander count
- Partners/companions count
- Duplicates list (if any)
- Color identity
- Banned cards (if any)'''

new = '''6. **Banned cards**: Check against the Commander ban list (if cached)

**validate_deck tool**: The program uses the `validate_deck` tool from the mtg-mcp package (nathanmartins/mtg-mcp) for Commander format validation. This tool:

- 100-card deck size check
- Commander eligibility (rule 903.3) and ban check
- Singleton rule, exempting basic lands (including Snow-Covered) and cards like Relentless Rats
- Every card checked against the commander's color identity and the Commander banned list
- Flags names Scryfall does not recognize
- Looks cards up in batches of 75, so a full deck costs two Scryfall requests
- Supports JSON array or text format decklists

**Output:** A validation report with:

- Status: AVAILABLE / PARTIAL (for any format issue found)
- Card count
- Commander count
- Partners/companions count
- Duplicates list (if any)
- Color identity
- Banned cards (if any)'''

if old in content:
    content = content.replace(old, new)
    with io.open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Success: validate_deck tool section added')
else:
    print('Error: old_string not found')
    lines = content.split('\n')
    for i in range(92, 106):
        print(f'{i}: {repr(lines[i])}')
