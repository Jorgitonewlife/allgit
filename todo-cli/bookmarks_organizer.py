import json
import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from collections import defaultdict
from pathlib import Path

@dataclass
class Bookmark:
    """Represents a single bookmark (URL)."""
    id: str
    name: str
    url: str
    date_added: str
    date_last_used: Optional[str] = None
    meta_info: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def added_datetime(self) -> datetime:
        """Convert Chrome's microseconds since 1601 to datetime."""
        if self.date_added:
            try:
                # Chrome uses microseconds since Jan 1, 1601
                us = int(self.date_added)
                # Convert to Unix timestamp (seconds since 1970)
                epoch_start = 11644473600000000  # microseconds between 1601 and 1970
                return datetime.fromtimestamp((us - epoch_start) / 1_000_000)
            except:
                pass
        return None
    
    @property
    def domain(self) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            return urlparse(self.url).netloc
        except:
            return ""
    
    def __str__(self):
        return f"[TAG] {self.name} → {self.url}"


@dataclass
class Folder:
    """Represents a bookmark folder."""
    id: str
    name: str
    date_added: str
    date_modified: Optional[str] = None
    children: List['BookmarkNode'] = field(default_factory=list)
    meta_info: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def added_datetime(self) -> datetime:
        if self.date_added:
            try:
                us = int(self.date_added)
                epoch_start = 11644473600000000
                return datetime.fromtimestamp((us - epoch_start) / 1_000_000)
            except:
                pass
        return None
    
    def get_all_bookmarks(self) -> List[Bookmark]:
        """Recursively get all bookmarks in this folder and subfolders."""
        result = []
        for child in self.children:
            if isinstance(child, Bookmark):
                result.append(child)
            elif isinstance(child, Folder):
                result.extend(child.get_all_bookmarks())
        return result
    
    def get_subfolders(self) -> List['Folder']:
        """Get all subfolders recursively."""
        result = []
        for child in self.children:
            if isinstance(child, Folder):
                result.append(child)
                result.extend(child.get_subfolders())
        return result
    
    def __str__(self):
        count = len(self.get_all_bookmarks())
        return f"[DIR] {self.name} ({count} bookmarks)"


BookmarkNode = Bookmark | Folder


class BookmarkManager:
    """Manages Chrome bookmarks with full organization capabilities."""
    
    def __init__(self, bookmarks_data: Dict[str, Any]):
        self.raw_data = bookmarks_data
        self.checksum = bookmarks_data.get('checksum', '')
        self.version = bookmarks_data.get('version', 1)
        self.roots = bookmarks_data.get('roots', {})
        self._folders_cache: Dict[str, Folder] = {}
        self._bookmarks_cache: List[Bookmark] = []
        
    @classmethod
    def from_chrome_file(cls, path: str = None):
        """Load bookmarks from Chrome's AccountBookmarks file."""
        if path is None:
            path = os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Default\AccountBookmarks')
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(data)
    
    def build_tree(self) -> Dict[str, Folder]:
        """Build folder hierarchy from roots."""
        roots = {}
        for root_name, root_data in self.roots.items():
            if 'children' in root_data:
                folder = self._parse_folder(root_data, root_name)
                roots[root_name] = folder
        return roots
    
    def _parse_folder(self, data: Dict, name: str = None) -> Folder:
        """Recursively parse folder structure."""
        folder = Folder(
            id=data.get('id', ''),
            name=name or data.get('name', ''),
            date_added=data.get('date_added', ''),
            date_modified=data.get('date_modified', ''),
            meta_info={k: v for k, v in data.items() if k not in ['id', 'name', 'date_added', 'date_modified', 'children']}
        )
        
        if 'children' in data:
            for child in data['children']:
                if child.get('type') == 'url':
                    bookmark = Bookmark(
                        id=child.get('id', ''),
                        name=child.get('name', ''),
                        url=child.get('url', ''),
                        date_added=child.get('date_added', ''),
                        date_last_used=child.get('date_last_used'),
                        meta_info={k: v for k, v in child.items() if k not in ['id', 'name', 'url', 'type', 'date_added', 'date_last_used']}
                    )
                    folder.children.append(bookmark)
                elif child.get('type') == 'folder':
                    subfolder = self._parse_folder(child, child.get('name', ''))
                    folder.children.append(subfolder)
        
        return folder
    
    def get_all_bookmarks(self) -> List[Bookmark]:
        """Get all bookmarks across all roots."""
        if not self._bookmarks_cache:
            roots = self.build_tree()
            for root in roots.values():
                self._bookmarks_cache.extend(root.get_all_bookmarks())
        return self._bookmarks_cache
    
    def get_all_folders(self) -> List[Folder]:
        """Get all folders across all roots."""
        if not self._folders_cache:
            roots = self.build_tree()
            for root in roots.values():
                self._collect_folders(root)
        return list(self._folders_cache.values())
    
    def _collect_folders(self, folder: Folder):
        self._folders_cache[folder.id] = folder
        for child in folder.children:
            if isinstance(child, Folder):
                self._collect_folders(child)
    
    def search(self, query: str) -> List[Bookmark]:
        """Search bookmarks by name or URL."""
        query = query.lower()
        results = []
        for bm in self.get_all_bookmarks():
            if query in bm.name.lower() or query in bm.url.lower():
                results.append(bm)
        return results
    
    def by_domain(self) -> Dict[str, List[Bookmark]]:
        """Group bookmarks by domain."""
        domains = defaultdict(list)
        for bm in self.get_all_bookmarks():
            domains[bm.domain].append(bm)
        return dict(sorted(domains.items(), key=lambda x: -len(x[1])))
    
    def by_folder(self) -> Dict[str, List[Bookmark]]:
        """Group bookmarks by top-level folder."""
        result = {}
        roots = self.build_tree()
        for name, folder in roots.items():
            result[name] = folder.get_all_bookmarks()
        return result
    
    def get_recent(self, days: int = 30) -> List[Bookmark]:
        """Get bookmarks added in the last N days."""
        cutoff = datetime.now().timestamp() - (days * 86400)
        recent = []
        for bm in self.get_all_bookmarks():
            dt = bm.added_datetime
            if dt and dt.timestamp() > cutoff:
                recent.append(bm)
        return sorted(recent, key=lambda x: x.added_datetime, reverse=True)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        bookmarks = self.get_all_bookmarks()
        folders = self.get_all_folders()
        domains = self.by_domain()
        
        return {
            'total_bookmarks': len(bookmarks),
            'total_folders': len(folders),
            'total_domains': len(domains),
            'top_domains': [(d, len(bms)) for d, bms in list(domains.items())[:10]],
            'root_folders': {name: len(f.get_all_bookmarks()) for name, f in self.build_tree().items()},
            'oldest_bookmark': min(bookmarks, key=lambda b: b.added_datetime or datetime.max).added_datetime if bookmarks else None,
            'newest_bookmark': max(bookmarks, key=lambda b: b.added_datetime or datetime.min).added_datetime if bookmarks else None,
        }
    
    def export_markdown(self, output_path: str = None) -> str:
        """Export bookmarks as Markdown."""
        lines = ["# Chrome Bookmarks Export\n"]
        roots = self.build_tree()
        
        for name, folder in roots.items():
            self._export_folder_markdown(folder, lines, level=2)
        
        content = '\n'.join(lines)
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
        return content
    
    def _export_folder_markdown(self, folder: Folder, lines: List[str], level: int = 2):
        indent = '#' * level
        lines.append(f"{indent} {folder.name}")
        if folder.children:
            for child in folder.children:
                if isinstance(child, Bookmark):
                    lines.append(f"- [{child.name}]({child.url})")
                elif isinstance(child, Folder):
                    self._export_folder_markdown(child, lines, level + 1)
    
    def export_json(self, output_path: str = None) -> str:
        """Export organized bookmarks as JSON."""
        from datetime import datetime
        
        class DateTimeEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                return super().default(obj)
        
        data = {
            'stats': self.get_stats(),
            'by_domain': {d: [b.url for b in bms] for d, bms in self.by_domain().items()},
            'by_folder': {name: [b.url for b in bms] for name, bms in self.by_folder().items()},
            'recent': [b.url for b in self.get_recent(30)],
            'all_bookmarks': [
                {
                    'name': b.name,
                    'url': b.url,
                    'domain': b.domain,
                    'date_added': b.date_added,
                    'added_datetime': b.added_datetime.isoformat() if b.added_datetime else None,
                }
                for b in self.get_all_bookmarks()
            ]
        }
        content = json.dumps(data, indent=2, ensure_ascii=False, cls=DateTimeEncoder)
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
        return content


def main():
    print("=" * 60)
    print("[BOOKS] Chrome Bookmarks Analyzer & Organizer")
    print("=" * 60)
    
    # Load bookmarks
    print("\n[FOLDER] Loading Chrome bookmarks...")
    manager = BookmarkManager.from_chrome_file()
    
    # Build tree
    print("[TREE] Building folder hierarchy...")
    roots = manager.build_tree()
    
    # Stats
    stats = manager.get_stats()
    print(f"\n[STATS] Statistics:")
    print(f"   Total bookmarks: {stats['total_bookmarks']}")
    print(f"   Total folders: {stats['total_folders']}")
    print(f"   Unique domains: {stats['total_domains']}")
    print(f"   Oldest bookmark: {stats['oldest_bookmark']}")
    print(f"   Newest bookmark: {stats['newest_bookmark']}")
    print(f"   Root folders:")
    for name, count in stats['root_folders'].items():
        print(f"   • {name}: {count} bookmarks")
    
    # Top domains
    print(f"\n[WEB] Top 10 Domains:")
    for domain, count in stats['top_domains']:
        print(f"   {domain}: {count} bookmarks")
    
    # By folder
    print(f"\n[DIR] By Folder:")
    by_folder = manager.by_folder()
    for folder, bookmarks in by_folder.items():
        print(f"   {folder}: {len(bookmarks)} bookmarks")
    
    # Recent
    recent = manager.get_recent(30)
    print(f"\n[TIME] Recent (30 days): {len(recent)} bookmarks")
    for bm in recent[:5]:
        dt = bm.added_datetime
        print(f"   • {bm.name} ({dt.strftime('%Y-%m-%d') if dt else 'unknown'})")
    
    # Export options
    print("\n" + "=" * 60)
    print("[SAVE] Export Options:")
    print("   manager.export_markdown('bookmarks.md')  # Markdown")
    print("   manager.export_json('bookmarks.json')    # JSON with stats")
    print("   manager.search('python')                 # Search")
    print("   manager.by_domain()                      # By domain")
    print("   manager.get_recent(7)                    # Last 7 days")
    
    # Save organized JSON
    print("\n[SAVE] Saving organized bookmarks to bookmarks_organized.json...")
    manager.export_json('bookmarks_organized.json')
    print("[OK] Done!")
    
    return manager


if __name__ == '__main__':
    manager = main()