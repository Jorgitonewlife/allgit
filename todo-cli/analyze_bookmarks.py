import sqlite3
import os
import json

def analyze_bookmarks():
    path = os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Default\AccountBookmarks')
    print('File size:', os.path.getsize(path), 'bytes')
    
    # Try SQLite
    try:
        conn = sqlite3.connect('file:' + path + '?mode=ro', uri=True)
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM sqlite_master WHERE type="table";')
        tables = cursor.fetchall()
        print('Tables:', tables)
        for table in tables:
            cursor.execute('SELECT * FROM ' + table[0] + ' LIMIT 5')
            rows = cursor.fetchall()
            print('Table', table[0], ':', rows)
            # Get column names
            cursor.execute('PRAGMA table_info(' + table[0] + ')')
            cols = cursor.fetchall()
            print('Columns:', [c[1] for c in cols])
    except Exception as e:
        print('Not SQLite or error:', e)
        with open(path, 'rb') as f:
            header = f.read(200)
            print('Header (hex):', header.hex()[:500])
    
    # Check EncryptedAccountBookmarks2
    path2 = os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Default\EncryptedAccountBookmarks2')
    if os.path.exists(path2):
        print('\n--- EncryptedAccountBookmarks2 ---')
        print('File size:', os.path.getsize(path2), 'bytes')
        with open(path2, 'rb') as f:
            header = f.read(200)
            print('Header (hex):', header.hex()[:500])
    
    # Check BookmarkMergedSurfaceOrdering
    path3 = os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Default\BookmarkMergedSurfaceOrdering')
    if os.path.exists(path3):
        print('\n--- BookmarkMergedSurfaceOrdering ---')
        print('File size:', os.path.getsize(path3), 'bytes')
        with open(path3, 'rb') as f:
            content = f.read()
            print('Content:', content)
            try:
                print('As JSON:', json.loads(content.decode()))
            except:
                pass

    # Check Preferences for bookmark-related settings
    prefs_path = os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Default\Preferences')
    if os.path.exists(prefs_path):
        print('\n--- Preferences (bookmark related) ---')
        with open(prefs_path, 'r', encoding='utf-8') as f:
            prefs = json.load(f)
            # Search for bookmark-related keys
            def find_keys(obj, path=''):
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        new_path = path + '.' + k if path else k
                        if 'bookmark' in k.lower():
                            print(f'  {new_path}: {type(v)}')
                        if isinstance(v, (dict, list)):
                            find_keys(v, new_path)
                elif isinstance(obj, list):
                    for i, v in enumerate(obj):
                        find_keys(v, path + '[' + str(i) + ']')
            find_keys(prefs)

if __name__ == '__main__':
    analyze_bookmarks()