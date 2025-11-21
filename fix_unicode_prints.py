"""
Fix all unicode characters in print statements for Windows compatibility
"""
import re
from pathlib import Path

# Map of unicode symbols to ASCII equivalents
UNICODE_MAP = {
    '✓': '[OK]',
    '✅': '[OK]',
    '❌': '[ERROR]',
    '⚠️': '[WARN]',
    '⚠': '[WARN]',
    '→': '->',
    '🔍': '[SEARCH]',
    '📋': '[INFO]',
    '💰': '[PRICE]',
    '📸': '[PHOTO]',
    '🏷️': '[TAG]',
    '👕': '[ITEM]',
    '✨': '[QUALITY]',
    '🎨': '[BRAND]',
    '🚀': '[START]',
    '🔄': '[PROCESS]',
    '🧪': '[TEST]',
    '🛡️': '[SECURITY]',
    '📦': '[PACKAGE]',
    '⏳': '[WAIT]',
    '🎯': '[TARGET]',
}

def fix_file(filepath: Path):
    """Fix unicode chars in a Python file"""
    try:
        content = filepath.read_text(encoding='utf-8')
        original = content

        # Replace all unicode symbols
        for unicode_char, ascii_replacement in UNICODE_MAP.items():
            content = content.replace(unicode_char, ascii_replacement)

        # Only write if changes were made
        if content != original:
            filepath.write_text(content, encoding='utf-8')
            print(f"Fixed: {filepath}")
            return True
        return False
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
        return False

def main():
    print("=" * 60)
    print("Fixing Unicode Characters for Windows Compatibility")
    print("=" * 60)

    # Find all Python files in backend
    backend_dir = Path(__file__).parent / "backend"
    python_files = list(backend_dir.rglob("*.py"))

    print(f"\nFound {len(python_files)} Python files")
    print("Processing...\n")

    fixed_count = 0
    for filepath in python_files:
        if fix_file(filepath):
            fixed_count += 1

    print(f"\n{fixed_count} files updated")
    print("=" * 60)

if __name__ == "__main__":
    main()
