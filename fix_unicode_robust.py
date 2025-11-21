"""
Fix unicode characters in Python files - robust version
Writes directly to files without console output
"""
import re
from pathlib import Path
import sys

# Map of unicode symbols to ASCII equivalents
REPLACEMENTS = [
    ('✓', '[OK]'),
    ('✅', '[OK]'),
    ('❌', '[ERROR]'),
    ('⚠️', '[WARN]'),
    ('⚠', '[WARN]'),
    ('→', '->'),
    ('🔍', '[SEARCH]'),
    ('📋', '[INFO]'),
    ('💰', '[PRICE]'),
    ('📸', '[PHOTO]'),
    ('🏷️', '[TAG]'),
    ('👕', '[ITEM]'),
    ('✨', '[QUALITY]'),
    ('🎨', '[BRAND]'),
    ('🚀', '[START]'),
    ('🔄', '[PROCESS]'),
    ('🧪', '[TEST]'),
    ('🛡️', '[SECURITY]'),
    ('📦', '[PACKAGE]'),
    ('⏳', '[WAIT]'),
    ('🎯', '[TARGET]'),
    ('ℹ️', '[INFO]'),
    ('ℹ', '[INFO]'),
]

def fix_file(filepath):
    """Fix unicode in a file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original = content

        # Replace all unicode symbols
        for old, new in REPLACEMENTS:
            content = content.replace(old, new)

        # Only write if changed
        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        # Write error to file instead of console
        with open('unicode_fix_errors.log', 'a', encoding='utf-8') as log:
            log.write(f"Error fixing {filepath}: {e}\n")
        return False

def main():
    backend_dir = Path(__file__).parent / "backend"

    # Create results log
    with open('unicode_fix_results.log', 'w', encoding='utf-8') as log:
        log.write("Unicode Fix Results\n")
        log.write("=" * 60 + "\n\n")

        python_files = list(backend_dir.rglob("*.py"))
        log.write(f"Found {len(python_files)} Python files\n\n")

        fixed_count = 0
        for filepath in python_files:
            if fix_file(filepath):
                fixed_count += 1
                log.write(f"Fixed: {filepath.name}\n")

        log.write(f"\n{fixed_count} files updated\n")

    # Simple ASCII output
    print(f"Done! Fixed {fixed_count} files. Check unicode_fix_results.log for details.")

if __name__ == "__main__":
    main()
