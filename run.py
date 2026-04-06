"""
Application entry point.
Ensures the working directory is set to the project root before launching the app.
"""
import os
import sys

def main() -> None:
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    sys.path.insert(0, project_root)

    from src.app.main import bootstrap
    bootstrap()

if __name__ == "__main__":
    main()