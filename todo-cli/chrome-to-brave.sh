#!/usr/bin/env bash
# chrome-to-brave-bookmarks.sh - Export Chrome bookmarks and import to Brave
# Usage: bash chrome-to-brave.sh

set -euo pipefail

CHROME_BOOKMARKS="${HOME}/AppData/Local/Google/Chrome/User Data/Default/AccountBookmarks"
BRAVE_BOOKMARKS="${HOME}/AppData/Local/BraveSoftware/Brave-Browser/User Data/Default/Bookmarks"

# Find Brave profile (could be Default, Profile 1, etc.)
BRAVE_USER_DATA="${HOME}/AppData/Local/BraveSoftware/Brave-Browser/User Data"
BRAVE_PROFILE_DIR=$(find "$BRAVE_USER_DATA" -maxdepth 1 -name "Profile*" -o -name "Default" 2>/dev/null | head -1)
BRAVE_BOOKMARKS="${BRAVE_PROFILE_DIR}/Bookmarks"

echo "=========================================="
echo "  Chrome → Brave Bookmarks Migration"
echo "=========================================="

# Check Chrome bookmarks exist
if [[ ! -f "$CHROME_BOOKMARKS" ]]; then
    echo "❌ Chrome bookmarks not found at: $CHROME_BOOKMARKS"
    exit 1
fi
echo "✅ Chrome bookmarks found"

# Check Brave bookmarks file exists
if [[ ! -f "$BRAVE_BOOKMARKS" ]]; then
    echo "❌ Brave bookmarks not found at: $BRAVE_BOOKMARKS"
    echo "   Open Brave once to create the profile, then retry."
    exit 1
fi
echo "✅ Brave bookmarks found at: $BRAVE_BOOKMARKS"

# Backup Brave bookmarks
BACKUP="${BRAVE_BOOKMARKS}.backup.$(date +%Y%m%d_%H%M%S)"
cp "$BRAVE_BOOKMARKS" "$BACKUP"
echo "📦 Backup created: $BACKUP"

# Read both files
echo "📖 Reading bookmarks..."
CHROME_DATA=$(cat "$CHROME_BOOKMARKS")
BRAVE_DATA=$(cat "$BRAVE_BOOKMARKS")

# Merge using Python (more reliable for JSON)
python3 << 'PYEOF'
import json
import sys

# Read files
with open(sys.argv[1], 'r', encoding='utf-8') as f:
    chrome = json.load(f)

with open(sys.argv[2], 'r', encoding='utf-8') as f:
    brave = json.load(f)

# Function to recursively collect all bookmarks from Chrome
def collect_bookmarks(node, path=""):
    bookmarks = []
    if node.get('type') == 'url':
        bookmarks.append({
            'name': node.get('name', ''),
            'url': node.get('url', ''),
            'date_added': node.get('date_added', ''),
            'path': path
        })
    elif node.get('type') == 'folder' and 'children' in node:
        folder_name = node.get('name', '')
        new_path = f"{path}/{node.get('name', '')}" if path else node.get('name', '')
        for child in node.get('children', []):
            bookmarks.extend(collect_bookmarks(child, new_path))
    return bookmarks

# Collect all Chrome bookmarks
chrome_bookmarks = []
for root_name, root_data in chrome.get('roots', {}).items():
    if 'children' in root_data:
        for child in root_data['children']:
            chrome_bookmarks.extend(collect_bookmarks(child, root_name))

print(f"Found {len(chrome_bookmarks)} Chrome bookmarks")

# Build lookup of existing Brave URLs to avoid duplicates
existing_urls = set()
def collect_brave_urls(node):
    if node.get('type') == 'url':
        existing_urls.add(node.get('url', ''))
    elif node.get('type') == 'folder' and 'children' in node:
        for child in node['children']:
            collect_brave_urls(child)

for root_data in brave.get('roots', {}).values():
    if 'children' in root_data:
        for child in root_data['children']:
            collect_brave_urls(child)

print(f"Existing Brave URLs: {len(existing_urls)}")

# Filter new bookmarks
new_bookmarks = [b for b in chrome_bookmarks if b['url'] not in existing_urls]
print(f"New bookmarks to import: {len(new_bookmarks)}")

if not new_bookmarks:
    print("✅ No new bookmarks to import")
    sys.exit(0)

# Function to add bookmarks to Brave's bookmark_bar
def add_to_folder(brave_roots, folder_name, bookmarks):
    if folder_name not in brave['roots']:
        return 0
    folder = brave['roots'][folder_name]
    if 'children' not in folder:
        folder['children'] = []
    
    added = 0
    for bm in bookmarks:
        # Create bookmark entry matching Brave format
        new_bm = {
            'type': 'url',
            'name': bm['name'],
            'url': bm['url'],
            'date_added': bm['date_added'] or str(int(__import__('time').time() * 1000000 + 11644473600000000))
        }
        folder['children'].append(new_bm)
        added += 1
    return added

# Import into bookmark_bar (main bar)
added = add_to_folder(brave, 'bookmark_bar', chrome_bookmarks)
print(f"Added {added} bookmarks to bookmark_bar")

# Write back
with open(sys.argv[2], 'w', encoding='utf-8') as f:
    json.dump(brave, f, indent=2, ensure_ascii=False)

print("✅ Import complete!")
PYEOF "$CHROME_BOOKMARKS" "$BRAVE_BOOKMARKS"

echo ""
echo "=========================================="
echo "✅ Migration complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Restart Brave browser"
echo "2. Check Bookmarks bar (Ctrl+Shift+B)"
echo "3. If duplicates: brave://bookmarks → Organize → Remove duplicates"
echo ""
echo "Backup saved at: $BACKUP"