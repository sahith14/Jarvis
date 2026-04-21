import os
import shutil
import difflib
from pathlib import Path

BACKUP_SUFFIX = ".jarvis.bak"

def generate_diff(old: str, new: str) -> str:
    """Generate unified diff."""
    return ''.join(difflib.unified_diff(
        old.splitlines(keepends=True),
        new.splitlines(keepends=True),
        fromfile='original',
        tofile='modified'
    ))

def validate_code(content: str, file_path: str) -> tuple[bool, str]:
    """Perform basic syntax validation based on file extension."""
    ext = Path(file_path).suffix.lower()
    if ext == '.py':
        try:
            compile(content, file_path, 'exec')
            return True, ""
        except SyntaxError as e:
            return False, f"Python syntax error: {e}"
    elif ext in ['.js', '.jsx', '.ts', '.tsx']:
        if content.count('{') != content.count('}'):
            return False, "JavaScript/TypeScript: unbalanced braces"
        return True, ""
    return True, ""

def backup_file(path: str) -> str:
    """Create a backup of the file."""
    expanded = os.path.expanduser(path)
    backup_path = expanded + BACKUP_SUFFIX
    shutil.copy2(expanded, backup_path)
    return backup_path

def apply_patch(path: str, new_content: str) -> tuple[bool, str]:
    """Apply new content after validation and backup."""
    expanded = os.path.expanduser(path)
    if not os.path.exists(expanded):
        return False, f"File not found: {expanded}"

    valid, error = validate_code(new_content, expanded)
    if not valid:
        return False, f"Validation failed: {error}"

    backup_file(expanded)

    try:
        with open(expanded, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True, "Patch applied successfully."
    except Exception as e:
        return False, f"Failed to write file: {str(e)}"

def rollback_file(path: str) -> bool:
    """Restore from backup."""
    expanded = os.path.expanduser(path)
    backup_path = expanded + BACKUP_SUFFIX
    if not os.path.exists(backup_path):
        return False
    shutil.copy2(backup_path, expanded)
    return True
