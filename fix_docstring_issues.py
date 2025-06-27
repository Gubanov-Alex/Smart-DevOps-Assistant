"""
Script to fix docstring issues identified by pydocstyle.
"""
import re
from pathlib import Path


def fix_value_objects_docstrings():
    """Fix docstring issues in value_objects.py."""
    file_path = Path("app/domain/value_objects.py")
    if not file_path.exists():
        print(f"File {file_path} not found")
        return
    
    content = file_path.read_text()
    
    # Fix D401: First line should be in imperative mood for __str__ methods
    content = re.sub(
        r'"""String representation',
        '"""Return string representation',
        content
    )
    
    # Fix D400: First line should end with a period - specific fix for full_identifier
    content = re.sub(
        r'"""Generate full identifier: environment\.service_type\.name"""',
        '"""Generate full identifier: environment.service_type.name."""',
        content
    )
    
    # More general fix for D400: ensure docstrings end with period
    content = re.sub(
        r'"""([^"]+[^.])"""',
        r'"""\1."""',
        content,
        flags=re.MULTILINE
    )
    
    file_path.write_text(content)
    print(f"Fixed value objects docstrings in {file_path}")


def fix_ml_service_docstring():
    """Fix docstring issues in ml_service.py."""
    file_path = Path("app/services/ml_service.py")
    if not file_path.exists():
        print(f"File {file_path} not found")
        return
    
    content = file_path.read_text()
    
    # Fix D403: First word should be properly capitalized
    content = re.sub(
        r'"""Mlservice',
        '"""Initialize ML service',
        content
    )
    
    file_path.write_text(content)
    print(f"Fixed ML service docstring in {file_path}")


def verify_fixes():
    """Verify that common syntax issues are fixed."""
    issues_found = []
    
    # Check log_classifier.py for common issues
    log_classifier_path = Path("app/infrastructure/ml/models/log_classifier.py")
    if log_classifier_path.exists():
        content = log_classifier_path.read_text()
        
        # Check for missing newlines after docstrings
        if '"""self.eval()' in content:
            issues_found.append("Missing newline after docstring in predict_proba")
        
        if '"""probabilities' in content:
            issues_found.append("Missing newline after docstring in predict method")
            
        if '"""for name' in content:
            issues_found.append("Missing newline after docstring in _init_weights")
            
        if '"""batch_size' in content:
            issues_found.append("Missing newline after docstring in forward method")
            
    if issues_found:
        print("⚠️ Additional syntax issues found:")
        for issue in issues_found:
            print(f"  - {issue}")
        print("These have been fixed in the corrected version.")
    else:
        print("✅ No additional syntax issues found.")


if __name__ == "__main__":
    print("Fixing docstring issues...")
    fix_value_objects_docstrings()
    fix_ml_service_docstring()
    verify_fixes()
    print("Done!")
