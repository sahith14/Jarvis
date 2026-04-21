import os
import shutil
import difflib
import re
from pathlib import Path

BACKUP_SUFFIX = ".jarvis.bak"

def generate_diff(old: str, new: str) -> str:
    return ''.join(difflib.unified_diff(
        old.splitlines(keepends=True), new.splitlines(keepends=True),
        fromfile='original', tofile='modified'
    ))

def assess_danger(old: str, new: str) -> tuple[str, list[str]]:
    """Return danger level and list of warnings."""
    warnings = []
    # Check for deletion of large blocks
    old_lines = old.splitlines()
    new_lines = new.splitlines()
    if len(old_lines) - len(new_lines) > 20:
        warnings.append(f"Removes {len(old_lines) - len(new_lines)} lines")
    # Check for sensitive patterns
    sensitive = ["password", "secret", "api_key", "token", "private"]
    for pattern in sensitive:
        if pattern in new.lower() and pattern not in old.lower():
            warnings.append(f"Adds potentially sensitive '{pattern}'")
    # Check for shell execution
    if re.search(r"os\.system|subprocess\.|eval\(|exec\(", new):
        warnings.append("Contains system command execution")
    # Danger level
    if len(warnings) >= 3:
        level = "HIGH"
    elif warnings:
        level = "MEDIUM"
    else:
        level = "LOW"
    return level, warnings

def validate_code(content: str, file_path: str) -> tuple[bool, str]:
    ext = Path(file_path).suffix.lower()
    if ext == '.py':
        try:
            compile(content, file_path, 'exec')
            return True, ""
        except SyntaxError as e:
            return False, f"Python syntax error: {e}"
    elif ext in ['.js', '.jsx', '.ts', '.tsx']:
        if content.count('{') != content.count('}'):
            return False, "Unbalanced braces"
        return True, ""
    return True, ""

def backup_file(path: str) -> str:
    expanded = os.path.expanduser(path)
    backup_path = expanded + BACKUP_SUFFIX
    shutil.copy2(expanded, backup_path)
    return backup_path

def apply_patch(path: str, new_content: str) -> tuple[bool, str]:
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
        return False, f"Failed to write: {e}"

def rollback_file(path: str) -> bool:
    expanded = os.path.expanduser(path)
    backup_path = expanded + BACKUP_SUFFIX
    if not os.path.exists(backup_path):
        return False
    shutil.copy2(backup_path, expanded)
    return True
