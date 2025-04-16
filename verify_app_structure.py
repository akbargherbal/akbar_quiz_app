import os
import sys
from pathlib import Path


def verify_app_engine_structure():
    """Verify the Django app structure meets GCP App Engine requirements."""

    # Get current directory
    current_dir = Path(os.getcwd()).resolve()
    print(f"Current directory: {current_dir}")

    # Check if we're in the project root
    # First, determine what we're looking at
    is_project_root = (current_dir / "src").exists() and (current_dir / "src").is_dir()
    is_src_dir = current_dir.name == "src"

    if is_project_root:
        print("Current location: Project root directory (correct for app.yaml)")
        src_dir = current_dir / "src"
    elif is_src_dir:
        print("Current location: src directory (correct for Django files)")
        src_dir = current_dir
        project_root = current_dir.parent
    else:
        print(
            "WARNING: Not in project root or src directory. Structure validation may be inaccurate."
        )
        src_dir = None
        project_root = None

    # Check files at project root
    if is_project_root or (not is_src_dir and project_root):
        root_to_check = current_dir if is_project_root else project_root
        print("\nChecking project root files:")
        root_files = {
            "app.yaml": "Required for App Engine deployment",
            ".gcloudignore": "Recommended to exclude unnecessary files",
        }

        for file_name, description in root_files.items():
            file_path = root_to_check / file_name
            exists = file_path.exists()
            status = "✓" if exists else "✗"
            print(f"  {status} {file_name}: {description}")

    # Check files in src directory
    if is_src_dir or (is_project_root and src_dir):
        dir_to_check = current_dir if is_src_dir else src_dir
        print("\nChecking src directory files:")
        src_files = {
            "manage.py": "Django management script",
            "requirements.txt": "Required for App Engine dependencies",
        }

        for file_name, description in src_files.items():
            file_path = dir_to_check / file_name
            exists = file_path.exists()
            status = "✓" if exists else "✗"
            print(f"  {status} {file_name}: {description}")

        # Check Django project structure
        print("\nChecking Django project structure:")
        django_dirs = {
            "core": "Django project core",
            "staticfiles": "Collected static files (created by collectstatic)",
        }

        for dir_name, description in django_dirs.items():
            dir_path = dir_to_check / dir_name
            exists = dir_path.exists() and dir_path.is_dir()
            status = "✓" if exists else "✗"
            print(f"  {status} {dir_name}: {description}")

    # Verify app.yaml content if it exists
    if is_project_root:
        app_yaml_path = current_dir / "app.yaml"
    elif is_src_dir:
        app_yaml_path = current_dir.parent / "app.yaml"
    else:
        app_yaml_path = Path("app.yaml")  # Fallback

    if app_yaml_path.exists():
        print("\nChecking app.yaml content:")
        with open(app_yaml_path, "r") as f:
            content = f.read()

            # Check for critical configurations
            checks = {
                "runtime: python": "runtime" in content,
                "entrypoint contains cd src": "cd src" in content,
                "entrypoint contains gunicorn": "gunicorn" in content,
                "core.wsgi:application": "core.wsgi:application" in content,
                "DB_HOST configuration": "DB_HOST" in content,
                "APPENGINE_URL configuration": "APPENGINE_URL" in content,
                "cloud_sql_instances": "cloud_sql_instances" in content,
            }

            for check, result in checks.items():
                status = "✓" if result else "✗"
                print(f"  {status} {check}")

    # Final recommendations
    print("\nRecommendations:")

    if is_project_root:
        # Check if everything is in the right place
        if not (current_dir / "app.yaml").exists():
            print("- Create app.yaml in the project root directory (current directory)")
        if not (current_dir / ".gcloudignore").exists():
            print(
                "- Create .gcloudignore in the project root directory (current directory)"
            )
        if not (current_dir / "src" / "requirements.txt").exists():
            print("- Ensure requirements.txt is in the src directory")
    elif is_src_dir:
        # We're in src, so parent is project root
        if not (current_dir.parent / "app.yaml").exists():
            print(
                "- Create app.yaml in the project root directory (parent of current directory)"
            )
        if not (current_dir.parent / ".gcloudignore").exists():
            print(
                "- Create .gcloudignore in the project root directory (parent of current directory)"
            )
        if not (current_dir / "requirements.txt").exists():
            print("- Create requirements.txt in the src directory (current directory)")
    else:
        print(
            "- Navigate to either the project root or src directory before running this script"
        )

    print("\nCorrect structure should be:")
    print("project-root/")
    print("├── app.yaml               # At project root")
    print("├── .gcloudignore          # At project root")
    print("└── src/                   # Django project directory")
    print("    ├── manage.py")
    print("    ├── requirements.txt   # Inside src/")
    print("    ├── core/              # Your Django project core")
    print("    │   ├── settings.py")
    print("    │   ├── urls.py")
    print("    │   └── wsgi.py")
    print("    └── your_apps/         # Your Django apps")


if __name__ == "__main__":
    verify_app_engine_structure()
