"""
Module for renaming folders and replacing text in files.

This script renames folders and replaces text within files in the current directory,
excluding the `.git` folder and itself.
"""

import logging
import os
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def replace_text_in_file(file_path: Path, old_text: str, new_text: str) -> None:
    """
    Replace old_text with new_text in the given file.

    Parameters
    ----------
    file_path : Path
        Path to the file.
    old_text : str
        Text to be replaced.
    new_text : str
        Text to replace with.

    """
    try:
        with file_path.open('r', encoding='utf-8') as file:
            file_contents = file.read()
    except UnicodeDecodeError:
        logger.warning("Skipping file due to encoding error: %s", file_path)
        return

    if old_text in file_contents:
        new_contents = file_contents.replace(old_text, new_text)
        with file_path.open('w', encoding='utf-8') as file:
            file.write(new_contents)
        logger.info("Replaced %s in: %s", old_text, file_path)

def rename_folders(directory: Path, old_dir_name: str, new_dir_name: str) -> None:
    """
    Rename folders in the directory replacing old_dir_name with new_dir_name.

    Parameters
    ----------
    directory : Path
        Path to the directory.
    old_dir_name : str
        Folder name to be replaced.
    new_dir_name : str
        New folder name.

    """
    for dirpath, dirnames, _filenames in os.walk(directory, topdown=False):
        if '.git' in dirpath:
            continue
        for dirname in dirnames:
            if old_dir_name in dirname:
                new_dirname = dirname.replace(old_dir_name, new_dir_name)
                old_dir_path = Path(dirpath) / dirname
                new_dir_path = Path(dirpath) / new_dirname
                old_dir_path.rename(new_dir_path)
                logger.info("Renamed folder: %s to %s", old_dir_path, new_dir_path)

def replace_text_in_directory(directory: Path, old_text: str, new_text: str) -> None:
    """
    Replace old_text with new_text in all files within the directory.

    Parameters
    ----------
    directory : Path
        Path to the directory.
    old_text : str
        Text to be replaced.
    new_text : str
        Text to replace with.

    """
    script_path: Path = Path(__file__).resolve()
    for dirpath, _dirnames, filenames in os.walk(directory):
        if '.git' in dirpath:
            continue
        for filename in filenames:
            file_path = Path(dirpath) / filename
            if file_path == script_path:
                continue
            replace_text_in_file(file_path, old_text, new_text)

def clean_coverage_config(project_root: Path) -> None:
    """
    Remove init-project.py from coverage omit list in pyproject.toml.

    Parameters
    ----------
    project_root : Path
        Path to the project root directory containing pyproject.toml

    """
    config_file = project_root / "pyproject.toml"
    if not config_file.exists():
        return

    with config_file.open("r") as f:
        lines = f.readlines()

    modified = False
    in_coverage_section = False
    new_lines = []

    for line in lines:
        if line.strip().startswith("[tool.coverage.run]"):
            in_coverage_section = True
            new_lines.append(line)
        elif in_coverage_section and line.strip().startswith("omit"):
            # Remove init-project.py from the omit list
            if "init-project.py" in line:
                new_line = line.replace('"init-project.py",', "").replace('"init-project.py"', "")
                if 'omit = []' in new_line:
                    # Skip adding empty omit line
                    modified = True
                    continue
                new_lines.append(new_line)
                modified = True
            else:
                new_lines.append(line)
        else:
            if in_coverage_section and line.startswith("["):
                in_coverage_section = False
            new_lines.append(line)

    if modified:
        with config_file.open("w") as f:
            f.writelines(new_lines)
        logger.info("Cleaned coverage configuration in pyproject.toml")

if __name__ == "__main__":
    REQUIRED_ARG_COUNT = 4

    if len(sys.argv) != REQUIRED_ARG_COUNT:
        logger.error("Usage: python update-project.py <new-text> '<your-name>' <your-email>")
        sys.exit(1)

    old_text: str = "project-name"
    old_dir_name: str = "project_name"
    old_name: str = "Yannick De Backer"
    old_email: str = "yannick@kobozo.eu"
    new_text: str = sys.argv[1]
    new_name: str = sys.argv[2]
    new_email: str = sys.argv[3]
    new_dir_name: str = new_text.replace("-", "_")

    current_directory: Path = Path(__file__).resolve().parent

    # First rename folders to replace old_dir_name with new_dir_name
    rename_folders(current_directory, old_dir_name, new_dir_name)

    # Then replace text in files
    replace_text_in_directory(current_directory, old_text, new_text)
    replace_text_in_directory(current_directory, old_dir_name, new_dir_name)
    replace_text_in_directory(current_directory, old_name, new_name)
    replace_text_in_directory(current_directory, old_email, new_email)

    # Clean coverage configuration
    clean_coverage_config(current_directory)

    # Remove the current script file
    script_path: Path = Path(__file__).resolve()
    script_path.unlink()
    logger.info("Removed script file: %s", script_path)

