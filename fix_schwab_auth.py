#!/usr/bin/env python3
"""Script to add Schwab authentication to main.py"""

with open('src/api/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the line with Schwab client initialized
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    new_lines.append(line)

    # Find the line: logger.info(" Schwab API client initialized")
    if 'logger.info(" Schwab API client initialized")' in line:
        # Replace with new code
        indent = '            '
        new_lines[-1] = indent + 'logger.info("✅ Schwab API client initialized")\n'
        new_lines.append('\n')
        new_lines.append(indent + '# Authenticate with refresh token\n')
        new_lines.append(indent + 'schwab_refresh_token = os.getenv(\'SCHWAB_REFRESH_TOKEN\')\n')
        new_lines.append(indent + 'if schwab_refresh_token:\n')
        new_lines.append(indent + '    schwab_client.refresh_token = schwab_refresh_token\n')
        new_lines.append(indent + '    if schwab_client.authenticate():\n')
        new_lines.append(indent + '        logger.info("✅ Schwab API authenticated successfully")\n')
        new_lines.append(indent + '    else:\n')
        new_lines.append(indent + '        logger.warning("⚠️  Schwab authentication failed, will use fallback")\n')
        new_lines.append(indent + '        schwab_client = None\n')
        new_lines.append(indent + 'else:\n')
        new_lines.append(indent + '    logger.warning("⚠️  No Schwab refresh token found, will use fallback")\n')
        new_lines.append(indent + '    schwab_client = None\n')

        # Skip the next 3 lines (else block)
        i += 1
        while i < len(lines) and 'schwab_client = None' not in lines[i]:
            i += 1
        # Skip the line with schwab_client = None
        if i < len(lines):
            i += 1
        continue

    i += 1

# Write back
with open('src/api/main.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✅ Successfully updated main.py with Schwab authentication")
