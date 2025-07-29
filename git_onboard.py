#!/usr/bin/env python3
"""
Automate onboarding a local project to GitHub.

This script installs required prerequisites, manages SSH keys,
and automates the git workflow for pushing a local project
to a new remote repository. It also provides a clean,
interactive command‑line interface with robust logging.

The code is structured to be easily extended to other platforms
besides Ubuntu. Functions such as package installation and path
handling are abstracted so that additional operating systems can be
supported with minimal changes.

Unit tests are included at the end of the file and can be run
directly with pytest or the standard library `unittest` module.

Usage:
    python3 git_onboard.py [options]

Run `python3 git_onboard.py --help` for a full list of
available command‑line options.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import logging.handlers
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    # Optional dependency for YAML configuration files
    import yaml  # type: ignore
except ImportError:
    yaml = None  # YAML support is optional

# Remove PyGithub integration. SSH key uploads are handled manually
# by the user, so we do not depend on PyGithub. Define dummy
# placeholders to avoid NameError if referenced inadvertently.
Github = None  # type: ignore
class GithubException(Exception):
    """Fallback exception class when PyGithub is not available."""
    pass

# Simple console interface without rich dependency
class Console:
    def print(self, *args, **kwargs):
        print(*args)

class Prompt:
    @staticmethod
    def ask(prompt: str, default: Optional[str] = None) -> str:
        return input(f"{prompt} " + (f"[{default}] " if default else "")) or (default or "")

class Confirm:
    @staticmethod
    def ask(prompt: str, default: bool = False) -> bool:
        answer = input(f"{prompt} (y/N) ") or ("y" if default else "n")
        return answer.lower().startswith("y")

class Progress:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        pass
    def add_task(self, description: str, total: int):
        return None
    def update(self, task, advance: int):
        pass

class Table:
    def __init__(self, *args, **kwargs):
        self.rows = []
    def add_column(self, *args, **kwargs):
        pass
    def add_row(self, *args, **kwargs):
        pass
    def __str__(self) -> str:
        return "Configuration Summary"

# Initialize console
console = Console()

# Regular expression to strip rich markup tags when rich is unavailable
import re


def safe_print(message: str, style: Optional[str] = None) -> None:
    """Print a message with optional styling.
    
    Args:
        message: The text to print.
        style: Optional style name (ignored).
    """
    # Simple print without rich dependency
    print(message)


def setup_logging(log_file: Path, level: int = logging.INFO) -> None:
    """Configure logging to console and rotating file handler.
    
    Args:
        log_file: Path to the log file.
        level: Logging level.
    """
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # Console handler for output
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Rotating file handler
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=1024 * 1024,  # 1MB
        backupCount=5,
    )
    file_handler.setFormatter(formatter)
    
    # Configure logging
    logging.basicConfig(
        level=level,
        handlers=[console_handler, file_handler],
    )


def check_command_exists(command: str) -> bool:
    """Return True if the given command is available on the system."""
    return shutil.which(command) is not None


def detect_package_manager() -> str:
    """Detect an available package manager on the system.

    Returns the name of the first detected package manager in the
    following order: apt, dnf, yum, brew. If none are found, defaults
    to 'apt'.
    """
    candidates = [
        ("apt", "apt-get"),
        ("dnf", "dnf"),
        ("yum", "yum"),
        ("brew", "brew"),
    ]
    for name, command in candidates:
        if check_command_exists(command):
            return name
    return "apt"


def install_package(package: str, pkg_manager: str = "apt") -> None:
    """Install a package using the specified package manager.

    Args:
        package: Name of the package to install.
        pkg_manager: The package manager to use (e.g., "apt", "brew").
    """
    logger = logging.getLogger("installer")
    safe_print(f"Installing missing package: {package}...", style="bold")
    try:
        if pkg_manager == "apt":
            # apt-get may require update before install
            subprocess.run(["sudo", "apt-get", "update"], check=True)
            subprocess.run(["sudo", "apt-get", "install", "-y", package], check=True)
        elif pkg_manager == "dnf":
            subprocess.run(["sudo", "dnf", "install", "-y", package], check=True)
        elif pkg_manager == "yum":
            subprocess.run(["sudo", "yum", "install", "-y", package], check=True)
        elif pkg_manager == "brew":
            subprocess.run(["brew", "install", package], check=True)
        else:
            raise ValueError(f"Unsupported package manager: {pkg_manager}")
        logger.info("Successfully installed %s", package)
    except subprocess.CalledProcessError as exc:
        logger.error("Failed to install %s: %s", package, exc)
        raise


def ensure_prerequisites(pkg_manager: str = "apt") -> None:
    """Ensure that required system commands are available, installing them if necessary.

    Args:
        pkg_manager: The package manager to use.
    """
    required_cmds = ["git", "ssh-keygen"]
    for cmd in required_cmds:
        if not check_command_exists(cmd):
            install_package(cmd, pkg_manager)


def ensure_ssh_key(console: Console) -> Path:
    """Ensure SSH key exists and return the public key path.
    
    Args:
        console: Console for prompting and display.
        
    Returns:
        Path to the public SSH key.
    """
    home = Path.home()
    ssh_dir = home / ".ssh"
    ssh_dir.mkdir(mode=0o700, exist_ok=True)
    pub_key_path = ssh_dir / "id_rsa.pub"
    priv_key_path = ssh_dir / "id_rsa"
    if pub_key_path.exists() and priv_key_path.exists():
        # Ensure correct permissions
        os.chmod(ssh_dir, 0o700)
        os.chmod(priv_key_path, 0o600)
        os.chmod(pub_key_path, 0o600)
        return pub_key_path
    console.print(
        "SSH key not found at ~/.ssh/id_rsa.pub.", style="bold yellow"
    )
    if not Confirm.ask("Generate new SSH key?", default=False):
        raise SystemExit("SSH key is required to continue.")
    # Generate key non-interactively
    console.print("Generating a new SSH key...")
    try:
        subprocess.run(
            [
                "ssh-keygen",
                "-t",
                "rsa",
                "-b",
                "4096",
                "-f",
                str(priv_key_path),
                "-N",
                "",
                "-C",
                f"{os.getlogin()}@{platform.node()}"
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # Set proper permissions
        os.chmod(ssh_dir, 0o700)
        os.chmod(priv_key_path, 0o600)
        os.chmod(pub_key_path, 0o600)
    except subprocess.CalledProcessError as exc:
        logging.getLogger("ssh").error("Failed to generate SSH key: %s", exc)
        raise SystemExit("SSH key generation failed.")
    # Print the public key and wait for user acknowledgement
    with pub_key_path.open("r") as f:
        pub_key = f.read().strip()
    console.print("\nYour new SSH public key:")
    console.print(pub_key, style="bold green")
    console.print(
        "\nPlease add this public key to GitHub (https://github.com/settings/keys)."
    )
    Prompt.ask("Press Enter once you have added the key", default="Done")
    return pub_key_path


# We removed the automatic SSH key upload functionality. Users must
# manually add their public key to GitHub via the web interface.


def run_git_command(args: List[str], cwd: Optional[Path] = None) -> None:
    """Run a git command and handle errors gracefully.

    Args:
        args: List of git arguments (excluding the `git` binary itself).
        cwd: Directory in which to run the command.

    Raises:
        SystemExit: If the git command fails.
    """
    logger = logging.getLogger("git")
    try:
        logger.debug("Running git command: git %s", " ".join(args))
        subprocess.run(["git"] + args, cwd=cwd, check=True)
    except subprocess.CalledProcessError as exc:
        safe_print(
            f"Git command failed: {' '.join(args)}\n{exc}",
            style="red",
        )
        logger.error("Git command failed: git %s", " ".join(args))
        raise SystemExit(1)


def initialize_repo(project_path: Path) -> None:
    """Initialize a new git repository in the project directory.
    
    Args:
        project_path: Path to the project directory.
    """
    logger = logging.getLogger("git")
    
    # Check if git is already initialized
    git_dir = project_path / ".git"
    if git_dir.exists():
        console.print("Git repository already initialized in " + str(project_path) + ".")
        return
    
    console.print("Initializing new git repository in " + str(project_path) + "...")
    
    # Initialize git repository
    try:
        run_git_command(["init"], cwd=project_path)
        
        # Set default branch to main (modern standard)
        try:
            run_git_command(["branch", "-M", "main"], cwd=project_path)
        except SystemExit:
            # If main branch creation fails, keep the default (master)
            logger.warning("Failed to rename branch to main, keeping default branch")
        
        console.print("Git repository initialized successfully.")
    except SystemExit:
        safe_print("Failed to initialize git repository.", style="red")
        raise


def stage_and_commit(project_path: Path, commit_message: str, branch_name: str) -> None:
    """Stage all files and create initial commit.
    
    Args:
        project_path: Path to the project directory.
        commit_message: Message for the commit.
        branch_name: Name of the branch to commit to.
    """
    logger = logging.getLogger("stage_commit")
    
    # Check if there are any changes to commit
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"], 
            cwd=project_path, 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0 and not result.stdout.strip():
            # No changes to commit
            console.print("No changes to commit. Working tree is clean.", style="green")
            return
    except Exception as exc:
        logger.warning("Failed to check git status: %s", exc)
    
    # Stage all files
    console.print("Staging all files...")
    try:
        run_git_command(["add", "."], cwd=project_path)
        console.print("All files staged successfully.")
    except SystemExit:
        safe_print("Failed to stage files.", style="red")
        raise
    
    # Check if there are any staged changes
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"], 
            cwd=project_path, 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0 and not result.stdout.strip():
            # No staged changes
            console.print("No changes to commit after staging.", style="yellow")
            return
    except Exception as exc:
        logger.warning("Failed to check staged changes: %s", exc)
    
    # Create commit
    console.print(f"Creating commit: {commit_message}")
    try:
        run_git_command(["commit", "-m", commit_message], cwd=project_path)
        console.print("Commit created successfully.")
    except SystemExit:
        safe_print("Failed to create commit.", style="red")
        raise


def push_to_remote(project_path: Path, branch_name: str, remote_url: str) -> None:
    """Push the repository to the remote URL.
    
    Args:
        project_path: Path to the project directory.
        branch_name: Name of the branch to push.
        remote_url: URL of the remote repository.
    """
    logger = logging.getLogger("git")
    
    # Add or set remote
    try:
        run_git_command(["remote", "add", "origin", remote_url], cwd=project_path)
    except SystemExit:
        # Remote might already exist, try to set URL
        try:
            run_git_command(["remote", "set-url", "origin", remote_url], cwd=project_path)
        except SystemExit:
            safe_print("Failed to configure remote repository.", style="red")
            raise
    
    # Get current branch name
    try:
        current_branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=project_path, text=True).strip()
    except subprocess.CalledProcessError:
        # If no current branch, check if we have any commits
        try:
            result = subprocess.run(["git", "rev-parse", "--verify", "HEAD"], cwd=project_path, capture_output=True, text=True)
            if result.returncode == 0:
                # We have commits but no branch name, create main branch
                try:
                    run_git_command(["branch", "-M", "main"], cwd=project_path)
                    current_branch = "main"
                except SystemExit:
                    current_branch = "master"  # Fallback
            else:
                safe_print("No commits found. Cannot push to remote.", style="red")
                raise SystemExit(1)
        except Exception:
            safe_print("Failed to determine current branch.", style="red")
            raise SystemExit(1)
    
    # If target branch is different from current branch, create it
    if branch_name != current_branch:
        console.print(f"Current branch is '{current_branch}', target branch is '{branch_name}'", style="yellow")
        console.print(f"Creating branch '{branch_name}' from current branch...", style="blue")
        try:
            run_git_command(["branch", branch_name], cwd=project_path)
            run_git_command(["checkout", branch_name], cwd=project_path)
            current_branch = branch_name
        except SystemExit:
            safe_print(f"Failed to create branch '{branch_name}'. Pushing current branch '{current_branch}'.", style="yellow")
    
    console.print(f"Pushing branch '{current_branch}' to remote origin...")
    try:
        run_git_command(["push", "-u", "origin", current_branch], cwd=project_path)
        safe_print("Successfully pushed to remote!", style="bold green")
        return
    except SystemExit:
        # Check if it's a push rejection due to remote changes
        try:
            # Get the last git command output to check for rejection
            result = subprocess.run(
                ["git", "push", "-u", "origin", current_branch], 
                cwd=project_path, 
                capture_output=True, 
                text=True
            )
            if "rejected" in result.stderr and "fetch first" in result.stderr:
                safe_print(
                    "Push rejected: Remote repository has changes that you don't have locally.",
                    style="yellow"
                )
                console.print("This usually happens when the remote repository already exists with content.")
                
                # Offer options to the user
                console.print("\nOptions:", style="bold")
                console.print("1. Pull remote changes first (recommended)")
                console.print("2. Force push (overwrites remote content)")
                console.print("3. Cancel and exit")
                
                choice = Prompt.ask(
                    "Choose an option (1/2/3)", 
                    default="1"
                ).strip()
                
                if choice == "1":
                    # Pull remote changes first
                    console.print("Pulling remote changes...")
                    try:
                        run_git_command(["pull", "origin", current_branch, "--allow-unrelated-histories"], cwd=project_path)
                        console.print("Remote changes pulled successfully. Pushing again...")
                        run_git_command(["push", "-u", "origin", current_branch], cwd=project_path)
                        safe_print("Successfully pushed to remote!", style="bold green")
                    except SystemExit:
                        safe_print(
                            "Failed to pull remote changes.\n"
                            "You may need to resolve conflicts manually.",
                            style="red",
                        )
                        raise
                elif choice == "2":
                    # Force push
                    if Confirm.ask("Are you sure you want to overwrite remote content? This will lose any remote changes.", default=False):
                        console.print("Force pushing...")
                        try:
                            run_git_command(["push", "-u", "origin", current_branch, "--force"], cwd=project_path)
                            safe_print("Successfully force pushed to remote!", style="bold green")
                        except SystemExit:
                            safe_print("Force push failed.", style="red")
                            raise
                    else:
                        safe_print("Force push cancelled.", style="yellow")
                        raise SystemExit(1)
                else:
                    safe_print("Push cancelled by user.", style="yellow")
                    raise SystemExit(1)
            else:
                safe_print("Failed to push to remote. Check your authentication and network connection.", style="red")
                raise
        except Exception:
            safe_print("Failed to push to remote. Check your authentication and network connection.", style="red")
            raise


def load_config(config_path: Path) -> Dict[str, str]:
    """Load configuration defaults from a JSON or YAML file.

    Args:
        config_path: Path to the configuration file.

    Returns:
        A dictionary of configuration values.
    """
    config: Dict[str, str] = {}
    if not config_path or not config_path.exists():
        return config
    try:
        with config_path.open("r", encoding="utf-8") as f:
            if config_path.suffix.lower() in {".yaml", ".yml"}:
                if yaml is None:
                    safe_print(
                        "PyYAML not installed. Cannot read YAML config file.",
                        style="red",
                    )
                else:
                    config = yaml.safe_load(f) or {}
            elif config_path.suffix.lower() == ".json":
                config = json.load(f)
            else:
                safe_print(
                    f"Unsupported config file extension: {config_path.suffix}",
                    style="yellow",
                )
    except Exception as exc:
        logging.getLogger("config").error(
            "Failed to read config file %s: %s", config_path, exc
        )
    return config or {}


def is_git_repository(project_path: Path) -> bool:
    """Check if the project path contains a valid git repository.
    
    Args:
        project_path: Path to the project directory.
        
    Returns:
        True if .git directory exists and is valid, False otherwise.
    """
    git_dir = project_path / ".git"
    return git_dir.exists() and git_dir.is_dir()


def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        SHA256 hash as a hexadecimal string.
    """
    hash_sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except (IOError, OSError) as exc:
        logging.getLogger("hash").warning("Failed to calculate hash for %s: %s", file_path, exc)
        return ""


def verify_remote_repository(remote_url: str) -> Path:
    """Verify that the remote repository exists and is accessible by performing a shallow clone.
    
    Args:
        remote_url: URL of the remote repository.
        
    Returns:
        Path to the temporary clone directory.
        
    Raises:
        SystemExit: If the remote repository cannot be accessed.
    """
    logger = logging.getLogger("remote")
    console.print(f"Verifying remote repository: {remote_url}")
    
    # Create temporary directory for shallow clone
    temp_dir = Path(tempfile.mkdtemp(prefix="onboard_temp_clone_"))
    
    try:
        # Perform shallow clone (depth=1) to verify access
        run_git_command(["clone", "--depth", "1", remote_url, str(temp_dir)])
        logger.info("Successfully verified remote repository")
        return temp_dir
    except SystemExit:
        logger.error("Failed to access remote repository: %s", remote_url)
        safe_print(
            f"Cannot access remote repository: {remote_url}\n"
            "Please check the URL and your authentication settings.",
            style="red"
        )
        # Clean up temp directory
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        raise SystemExit(1)


def get_tracked_files_from_clone(clone_path: Path) -> List[Path]:
    """Get list of tracked files from the cloned repository.
    
    Args:
        clone_path: Path to the cloned repository.
        
    Returns:
        List of relative paths to tracked files.
    """
    try:
        # Get list of tracked files (excluding .git directory)
        result = subprocess.check_output(
            ["git", "ls-files"], cwd=clone_path, text=True
        )
        return [Path(line.strip()) for line in result.splitlines() if line.strip()]
    except subprocess.CalledProcessError as exc:
        logging.getLogger("git").error("Failed to get tracked files: %s", exc)
        return []


def compare_local_vs_remote(project_path: Path, clone_path: Path) -> Tuple[List[Path], List[Path], List[Path]]:
    """Compare local project files with files from remote clone.
    
    Args:
        project_path: Path to the local project directory.
        clone_path: Path to the temporary clone directory.
        
    Returns:
        Tuple of (modified_files, new_files, deleted_files).
    """
    logger = logging.getLogger("compare")
    
    # Get tracked files from remote clone
    remote_files = get_tracked_files_from_clone(clone_path)
    
    # Get all local files (excluding .git directory)
    local_files = []
    for file_path in project_path.rglob("*"):
        if file_path.is_file() and ".git" not in file_path.parts:
            rel_path = file_path.relative_to(project_path)
            local_files.append(rel_path)
    
    # Read .gitignore patterns to filter out ignored files
    gitignore_patterns = []
    gitignore_path = project_path / ".gitignore"
    if gitignore_path.exists():
        try:
            with gitignore_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        gitignore_patterns.append(line)
        except Exception as exc:
            logger.warning("Failed to read .gitignore: %s", exc)
    
    def is_ignored(file_path: Path) -> bool:
        """Check if a file should be ignored based on .gitignore patterns."""
        file_str = str(file_path)
        for pattern in gitignore_patterns:
            # Simple pattern matching (can be enhanced with fnmatch)
            if pattern.endswith("/"):
                # Directory pattern
                if file_str.startswith(pattern[:-1]) or pattern[:-1] in file_str.split("/"):
                    return True
            elif pattern.startswith("*"):
                # Wildcard pattern
                if file_str.endswith(pattern[1:]):
                    return True
            elif pattern in file_str:
                # Simple substring match
                return True
        return False
    
    # Filter out ignored files from local files
    filtered_local_files = [f for f in local_files if not is_ignored(f)]
    
    logger.info("Found %d local files (after filtering), %d remote files", 
                len(filtered_local_files), len(remote_files))
    
    # Find modified files (exist in both, different content)
    modified_files = []
    for local_file in filtered_local_files:
        if local_file in remote_files:
            local_hash = calculate_file_hash(project_path / local_file)
            remote_hash = calculate_file_hash(clone_path / local_file)
            if local_hash != remote_hash:
                modified_files.append(local_file)
    
    # Find new files (exist in local, not in remote)
    new_files = [f for f in filtered_local_files if f not in remote_files]
    
    # Find deleted files (exist in remote, not in local)
    deleted_files = [f for f in remote_files if f not in filtered_local_files]
    
    logger.info("Found %d modified, %d new, %d deleted files", 
                len(modified_files), len(new_files), len(deleted_files))
    
    return modified_files, new_files, deleted_files


def display_file_changes(modified_files: List[Path], new_files: List[Path], deleted_files: List[Path]) -> None:
    """Display a summary of file changes.
    
    Args:
        modified_files: List of modified files.
        new_files: List of new files.
        deleted_files: List of deleted files.
    """
    console.print("\nFile Changes Summary", style="bold blue")
    
    # Count files by type
    modified_count = len(modified_files)
    new_count = len(new_files)
    deleted_count = len(deleted_files)
    total_count = modified_count + new_count + deleted_count
    
    if total_count == 0:
        console.print("No changes detected.", style="green")
        return
    
    # Create summary table
    table = Table(title="Changes Summary")
    table.add_column("Type", style="cyan", no_wrap=True)
    table.add_column("Count", style="magenta", justify="right")
    table.add_column("Description", style="white")
    
    if modified_count > 0:
        table.add_row("Modified", str(modified_count), "Files changed in both local and remote")
    if new_count > 0:
        table.add_row("New", str(new_count), "Files added locally")
    if deleted_count > 0:
        table.add_row("Deleted", str(deleted_count), "Files removed locally")
    
    console.print(table)
    
    # Show sample files for each category
    if modified_files:
        console.print(f"\nModified files (showing first 5 of {modified_count}):", style="yellow")
        for file in modified_files[:5]:
            console.print(f"  • {file}")
        if modified_count > 5:
            console.print(f"  ... and {modified_count - 5} more")
    
    if new_files:
        console.print(f"\nNew files (showing first 5 of {new_count}):", style="green")
        for file in new_files[:5]:
            console.print(f"  • {file}")
        if new_count > 5:
            console.print(f"  ... and {new_count - 5} more")
    
    if deleted_files:
        console.print(f"\nDeleted files (showing first 5 of {deleted_count}):", style="red")
        for file in deleted_files[:5]:
            console.print(f"  • {file}")
        if deleted_count > 5:
            console.print(f"  ... and {deleted_count - 5} more")
    
    # Show warning if many files are being added
    if new_count > 100:
        console.print(f"\nWarning: {new_count} new files detected!", style="bold yellow")
        console.print("This might include files that should be ignored (like node_modules).", style="yellow")
        console.print("Check your .gitignore file if this seems incorrect.", style="yellow")


def detect_recovery_scenario(project_path: Path, config_defaults: Dict[str, str]) -> Tuple[str, Optional[str]]:
    """Detect the recovery scenario for a detached repository.
    
    Args:
        project_path: Path to the project directory.
        config_defaults: Configuration defaults from config file.
        
    Returns:
        Tuple of (scenario_type, remote_url).
        scenario_type can be:
        - "remote_exists": Files exist in remote repository
        - "local_only": Files exist only locally
        - "unknown": Cannot determine scenario
    """
    logger = logging.getLogger("detection")
    
    console.print("\nDetecting recovery scenario...", style="bold blue")
    console.print("This will help determine the best recovery approach.", style="blue")
    
    # Get remote URL from user or config
    remote_url = config_defaults.get("remote_url")
    if not remote_url:
        console.print("\nPlease provide information about your repository:", style="bold")
        console.print("• If you have a GitHub repository URL, enter it below", style="blue")
        console.print("• If you don't have a remote repository, just press Enter", style="blue")
        console.print("• If you're unsure, press Enter to proceed with local-only recovery", style="blue")
        
        remote_url = Prompt.ask(
            "\nEnter GitHub repository clone URL (HTTPS or SSH) or press Enter if no remote exists", 
            default=""
        ).strip()
    
    if not remote_url:
        # No remote URL provided - assume local only
        console.print("\nNo remote URL provided. Proceeding with local-only recovery.", style="green")
        console.print("This will create a local git repository with all your files.", style="blue")
        return "local_only", None
    
    # Try to verify remote repository
    console.print(f"\nVerifying remote repository: {remote_url}", style="blue")
    temp_clone_path = None
    try:
        temp_clone_path = verify_remote_repository(remote_url)
        logger.info("Remote repository verified successfully")
        console.print("Remote repository verified successfully!", style="green")
        console.print("This will compare your local files with the remote repository.", style="blue")
        return "remote_exists", remote_url
    except SystemExit:
        # Remote verification failed
        console.print("\nCould not access remote repository.", style="yellow")
        console.print("This could mean:", style="yellow")
        console.print("1. The repository doesn't exist", style="yellow")
        console.print("2. You don't have access to it", style="yellow")
        console.print("3. The URL is incorrect", style="yellow")
        console.print("4. Network connectivity issues", style="yellow")
        
        console.print("\nWhat would you like to do?", style="bold")
        if Confirm.ask("Proceed as local-only repository?", default=True):
            console.print("Proceeding with local-only recovery.", style="green")
            return "local_only", None
        else:
            console.print("Recovery cancelled by user.", style="red")
            return "unknown", None
    finally:
        # Clean up temporary clone
        if temp_clone_path and temp_clone_path.exists():
            try:
                shutil.rmtree(temp_clone_path)
                logger.debug("Cleaned up temporary clone directory")
            except Exception as exc:
                logger.warning("Failed to clean up temporary directory %s: %s", temp_clone_path, exc)


def recover_detached_repository(project_path: Path, config_defaults: Dict[str, str]) -> bool:
    """Handle recovery of a detached repository (missing .git directory).
    
    Args:
        project_path: Path to the project directory.
        config_defaults: Configuration defaults from config file.
        
    Returns:
        True if recovery was successful, False otherwise.
    """
    logger = logging.getLogger("recovery")
    
    if is_git_repository(project_path):
        return False  # Not a detached repository
    
    console.print("\nDetected detached repository (missing .git directory).", style="bold yellow")
    console.print("This means your project folder is not connected to git.", style="yellow")
    console.print("Don't worry! We can help you recover your files.", style="green")
    
    # Detect recovery scenario
    scenario, remote_url = detect_recovery_scenario(project_path, config_defaults)
    
    if scenario == "unknown":
        safe_print("\nCannot determine recovery scenario. Please check your remote URL and try again.", style="red")
        return False
    
    if scenario == "local_only":
        console.print("\nStarting local-only recovery...", style="bold blue")
        return recover_local_only_repository(project_path, config_defaults)
    else:  # remote_exists
        console.print("\nStarting remote repository recovery...", style="bold blue")
        return recover_remote_exists_repository(project_path, remote_url, config_defaults)


def recover_local_only_repository(project_path: Path, config_defaults: Dict[str, str]) -> bool:
    """Recover a local-only repository (no remote exists).
    
    Args:
        project_path: Path to the project directory.
        config_defaults: Configuration defaults from config file.
        
    Returns:
        True if recovery was successful, False otherwise.
    """
    logger = logging.getLogger("recovery_local")
    
    console.print("Recovering local-only repository...", style="bold blue")
    console.print("This will create a new git repository with all your local files.", style="blue")
    
    # Get all files in the project (excluding .git and .gitignore)
    local_files = []
    for file_path in project_path.rglob("*"):
        if file_path.is_file() and ".git" not in file_path.parts and file_path.name != ".gitignore":
            rel_path = file_path.relative_to(project_path)
            local_files.append(rel_path)
    
    if not local_files:
        safe_print("No files found in project directory.", style="yellow")
        return True
    
    # Display files found
    console.print(f"Found {len(local_files)} files in project directory.")
    if len(local_files) <= 10:
        for file in local_files:
            console.print(f"   • {file}")
    else:
        for file in local_files[:5]:
            console.print(f"   • {file}")
        console.print(f"   ... and {len(local_files) - 5} more files")
    
    # Prompt user for recovery
    console.print("\nWhat would you like to do?", style="bold")
    if not Confirm.ask("Initialize git repository and create initial commit?", default=True):
        safe_print("Recovery cancelled by user.", style="yellow")
        return False
    
    # Perform recovery
    console.print("\nStarting recovery process...", style="bold green")
    
    # Initialize new git repository
    try:
        initialize_repo(project_path)
    except SystemExit:
        safe_print("Failed to initialize git repository.", style="red")
        return False
    
    # Stage all files
    console.print("Staging all files...")
    staged_files = []
    for file_path in local_files:
        try:
            run_git_command(["add", str(file_path)], cwd=project_path)
            staged_files.append(str(file_path))
            console.print(f"  Staged: {file_path}")
        except SystemExit:
            console.print(f"  Failed to stage: {file_path}", style="red")
            logger.warning("Failed to stage file: %s", file_path)
    
    if not staged_files:
        safe_print("No files were successfully staged. Cannot create commit.", style="red")
        return False
    
    console.print(f"Successfully staged {len(staged_files)} files.")
    
    # Commit changes
    commit_message = config_defaults.get("message", "Initial commit")
    console.print(f"Creating initial commit: {commit_message}")
    try:
        run_git_command(["commit", "-m", commit_message], cwd=project_path)
    except SystemExit:
        safe_print("Failed to create commit. No changes to commit or git configuration issue.", style="red")
        return False
    
    safe_print("Successfully recovered local repository!", style="bold green")
    console.print("Note: This is a local-only repository. To push to GitHub, create a remote repository first.", style="yellow")
    console.print("You can create a repository on GitHub and then run: git remote add origin <URL>", style="blue")
    logger.info("Local-only repository recovery completed successfully")
    return True


def recover_remote_exists_repository(project_path: Path, remote_url: str, config_defaults: Dict[str, str]) -> bool:
    """Recover a repository that has a remote counterpart.
    
    Args:
        project_path: Path to the project directory.
        remote_url: URL of the remote repository.
        config_defaults: Configuration defaults from config file.
        
    Returns:
        True if recovery was successful, False otherwise.
    """
    logger = logging.getLogger("recovery_remote")
    
    console.print("Recovering repository with remote counterpart...", style="bold blue")
    
    # Verify remote repository
    temp_clone_path = None
    try:
        temp_clone_path = verify_remote_repository(remote_url)
    except SystemExit:
        safe_print("Failed to verify remote repository. Please check the URL and try again.", style="red")
        return False
    
    # Get default branch from remote
    default_branch = "main"  # Modern default
    try:
        result = subprocess.run(
            ["git", "ls-remote", "--symref", remote_url, "HEAD"], 
            capture_output=True, 
            text=True
        )
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.startswith('ref: refs/heads/'):
                    default_branch = line.split('refs/heads/')[1].strip()
                    break
    except Exception:
        # Use config default or fallback to main
        default_branch = config_defaults.get("branch", "main")
    
    console.print(f"Remote default branch: {default_branch}", style="blue")
    
    # Compare local vs remote
    modified_files, new_files, deleted_files = compare_local_vs_remote(
        project_path, temp_clone_path
    )
    
    total_changes = len(modified_files) + len(new_files) + len(deleted_files)
    
    if total_changes == 0:
        safe_print("No local changes detected; the project is already up to date on GitHub.", 
                  style="green")
        console.print("However, local .git directory is missing. Initializing git repository...", style="yellow")
        
        # Initialize git repository even if no changes
        try:
            initialize_repo(project_path)
        except SystemExit:
            safe_print("Failed to initialize git repository.", style="red")
            return False
        
        # Add remote
        try:
            run_git_command(["remote", "add", "origin", remote_url], cwd=project_path)
        except SystemExit:
            # Remote might already exist, try to set URL
            try:
                run_git_command(["remote", "set-url", "origin", remote_url], cwd=project_path)
            except SystemExit:
                safe_print("Failed to configure remote repository.", style="red")
                return False
        
        safe_print("Git repository initialized successfully!", style="bold green")
        console.print("Your project is now connected to the remote repository.", style="blue")
        logger.info("Repository recovery completed successfully (no changes needed)")
        return True
    
    # Display changes
    display_file_changes(modified_files, new_files, deleted_files)
    
    # Prompt user for recovery
    if not Confirm.ask(f"Commit and push these {total_changes} changes to GitHub?", default=False):
        safe_print("Recovery cancelled by user.", style="yellow")
        return False
    
    # Perform recovery
    console.print("Recovering repository...")
    
    # Initialize new git repository
    try:
        initialize_repo(project_path)
    except SystemExit:
        safe_print("Failed to initialize git repository.", style="red")
        return False
    
    # Add remote
    try:
        run_git_command(["remote", "add", "origin", remote_url], cwd=project_path)
    except SystemExit:
        # Remote might already exist, try to set URL
        try:
            run_git_command(["remote", "set-url", "origin", remote_url], cwd=project_path)
        except SystemExit:
            safe_print("Failed to configure remote repository.", style="red")
            return False
    
    # Stage only the changed files
    all_changed_files = modified_files + new_files
    if not all_changed_files:
        safe_print("No files to stage. Recovery completed without changes.", style="yellow")
        return True
        
    if all_changed_files:
        console.print("Staging changed files...")
        staged_files = []
        for file_path in all_changed_files:
            full_path = project_path / file_path
            if full_path.exists():
                try:
                    run_git_command(["add", str(file_path)], cwd=project_path)
                    staged_files.append(str(file_path))
                    console.print(f"  Staged: {file_path}")
                except SystemExit:
                    console.print(f"  Failed to stage: {file_path}", style="red")
                    logger.warning("Failed to stage file: %s", file_path)
        
        if not staged_files:
            safe_print("No files were successfully staged. Cannot create commit.", style="red")
            return False
        
        console.print(f"Successfully staged {len(staged_files)} files.")
    
    # Commit changes
    console.print("Creating recovery commit...")
    try:
        run_git_command(["commit", "-m", "Recover and push local changes"], cwd=project_path)
    except SystemExit:
        safe_print("Failed to create commit. No changes to commit or git configuration issue.", style="red")
        return False
    
    # Get current branch name
    try:
        current_branch = subprocess.check_output(
            ["git", "branch", "--show-current"], 
            cwd=project_path, 
            text=True
        ).strip()
    except subprocess.CalledProcessError:
        # Fallback to default branch
        current_branch = default_branch
    
    # Push to current branch
    console.print(f"Pushing to {current_branch} branch...")
    try:
        run_git_command(["push", "-u", "origin", current_branch], cwd=project_path)
    except SystemExit:
        # Check if it's a push rejection due to remote changes
        try:
            # Get the last git command output to check for rejection
            result = subprocess.run(
                ["git", "push", "-u", "origin", current_branch], 
                cwd=project_path, 
                capture_output=True, 
                text=True
            )
            if "rejected" in result.stderr and "fetch first" in result.stderr:
                safe_print(
                    "Push rejected: Remote repository has changes that you don't have locally.",
                    style="yellow"
                )
                console.print("This usually happens when the remote repository already exists with content.")
                
                # Offer options to the user
                console.print("\nOptions:", style="bold")
                console.print("1. Pull remote changes first (recommended)")
                console.print("2. Force push (overwrites remote content)")
                console.print("3. Cancel and exit")
                
                choice = Prompt.ask(
                    "Choose an option (1/2/3)", 
                    default="1"
                ).strip()
                
                if choice == "1":
                    # Pull remote changes first
                    console.print("Pulling remote changes...")
                    try:
                        run_git_command(["pull", "origin", current_branch, "--allow-unrelated-histories"], cwd=project_path)
                        console.print("Remote changes pulled successfully. Pushing again...")
                        run_git_command(["push", "-u", "origin", current_branch], cwd=project_path)
                        safe_print("Successfully pushed to remote!", style="bold green")
                    except SystemExit:
                        safe_print(
                            "Failed to pull remote changes.\n"
                            "You may need to resolve conflicts manually.",
                            style="red",
                        )
                        return False
                elif choice == "2":
                    # Force push
                    if Confirm.ask("Are you sure you want to overwrite remote content? This will lose any remote changes.", default=False):
                        console.print("Force pushing...")
                        try:
                            run_git_command(["push", "-u", "origin", current_branch, "--force"], cwd=project_path)
                            safe_print("Successfully force pushed to remote!", style="bold green")
                        except SystemExit:
                            safe_print("Force push failed.", style="red")
                            return False
                    else:
                        safe_print("Force push cancelled.", style="yellow")
                        return False
                else:
                    safe_print("Push cancelled by user.", style="yellow")
                    return False
            else:
                safe_print("Failed to push to remote. Check your authentication and network connection.", style="red")
                return False
        except Exception:
            safe_print("Failed to push to remote. Check your authentication and network connection.", style="red")
            return False
    
    safe_print("Successfully recovered and pushed local changes!", style="bold green")
    logger.info("Repository recovery completed successfully")
    
    # Clean up temporary clone
    if temp_clone_path and temp_clone_path.exists():
        try:
            shutil.rmtree(temp_clone_path)
            logger.debug("Cleaned up temporary clone directory")
        except Exception as exc:
            logger.warning("Failed to clean up temporary directory %s: %s", temp_clone_path, exc)
    
    return True


def create_default_gitignore(project_path: Path, custom_patterns: List[str] = None) -> None:
    """Create a default .gitignore file with common patterns.
    
    Args:
        project_path: Path to the project directory.
        custom_patterns: Optional list of custom patterns to add.
    """
    gitignore_path = project_path / ".gitignore"
    
    # Check if .gitignore already exists
    if gitignore_path.exists():
        try:
            with gitignore_path.open("r", encoding="utf-8") as f:
                existing_content = f.read().strip()
            
            if existing_content:
                console.print("Found existing .gitignore file.", style="green")
                console.print("Skipping .gitignore creation.", style="blue")
                return
            else:
                # Empty .gitignore file, can be replaced
                pass
        except Exception as exc:
            logging.getLogger("gitignore").warning("Failed to read existing .gitignore: %s", exc)
            # Continue with creating new .gitignore
    
    # Common patterns for various project types
    default_patterns = [
        "# Dependencies",
        "node_modules/",
        "npm-debug.log*",
        "yarn-debug.log*",
        "yarn-error.log*",
        "",
        "# Build outputs",
        "dist/",
        "build/",
        ".next/",
        "out/",
        "",
        "# Environment files",
        ".env",
        ".env.local",
        ".env.development.local",
        ".env.test.local",
        ".env.production.local",
        "",
        "# IDE files",
        ".vscode/",
        ".idea/",
        "*.swp",
        "*.swo",
        "*~",
        "",
        "# OS files",
        ".DS_Store",
        "Thumbs.db",
        "",
        "# Logs",
        "*.log",
        "logs/",
        "",
        "# Runtime data",
        "pids",
        "*.pid",
        "*.seed",
        "*.pid.lock",
        "",
        "# Coverage directory used by tools like istanbul",
        "coverage/",
        "",
        "# Temporary folders",
        "tmp/",
        "temp/",
        "",
        "# Python",
        "__pycache__/",
        "*.py[cod]",
        "*$py.class",
        "*.so",
        ".Python",
        "env/",
        "venv/",
        "ENV/",
        "env.bak/",
        "venv.bak/",
        "",
        "# Java",
        "*.class",
        "*.jar",
        "target/",
        "",
        "# Go",
        "*.exe",
        "*.exe~",
        "*.dll",
        "*.so",
        "*.dylib",
        "",
        "# Docker",
        ".dockerignore",
        "",
        "# Git",
        ".git/",
        ".gitignore",
    ]
    
    # Add custom patterns if provided
    if custom_patterns:
        default_patterns.extend([
            "",
            "# Custom patterns",
        ] + custom_patterns)
    
    try:
        with gitignore_path.open("w", encoding="utf-8") as f:
            f.write("\n".join(default_patterns))
        console.print("Created .gitignore file.", style="green")
    except Exception as exc:
        logging.getLogger("gitignore").warning("Failed to create .gitignore: %s", exc)


def prompt_gitignore_patterns(project_path: Path) -> List[str]:
    """Prompt user for custom .gitignore patterns.
    
    Args:
        project_path: Path to the project directory.
        
    Returns:
        List of custom patterns to add to .gitignore.
    """
    custom_patterns = []
    
    # Check if .gitignore already exists in project directory
    gitignore_path = project_path / ".gitignore"
    if gitignore_path.exists():
        try:
            with gitignore_path.open("r", encoding="utf-8") as f:
                existing_content = f.read().strip()
            
            if existing_content:
                console.print("Found existing .gitignore file.", style="green")
                console.print("Skipping .gitignore configuration.", style="blue")
                return []
        except Exception as exc:
            logging.getLogger("gitignore").warning("Failed to read existing .gitignore: %s", exc)
    
    console.print("\nGitignore Configuration", style="bold blue")
    console.print("Let's configure which files and folders to ignore in your repository.")
    console.print("This helps keep your repository clean and focused on source code.")
    
    # Common suggestions based on project type
    suggestions = {
        "node_modules": "Node.js dependencies",
        "dist": "Build output directory",
        "build": "Build output directory", 
        ".env": "Environment variables",
        "*.log": "Log files",
        "coverage": "Test coverage reports",
        "tmp": "Temporary files",
        "temp": "Temporary files",
        "__pycache__": "Python cache files",
        "*.pyc": "Python compiled files",
        "target": "Java build output",
        "*.class": "Java compiled files",
        ".DS_Store": "macOS system files",
        "Thumbs.db": "Windows system files",
        ".vscode": "VS Code settings",
        ".idea": "IntelliJ IDEA settings",
    }
    
    console.print("\nCommon patterns to ignore:", style="bold")
    for pattern, description in suggestions.items():
        console.print(f"  • {pattern} - {description}")
    
    console.print("\nWould you like to add custom ignore patterns?", style="bold")
    if not Confirm.ask("Configure custom .gitignore patterns?", default=False):
        return []
    
    console.print("\nEnter patterns to ignore (one per line, press Enter twice to finish):")
    console.print("Examples: *.tmp, cache/, .env.local")
    
    while True:
        pattern = Prompt.ask("Pattern (or press Enter to finish)").strip()
        if not pattern:
            break
        
        if pattern not in custom_patterns:
            custom_patterns.append(pattern)
            console.print(f"Added: {pattern}", style="green")
        else:
            console.print(f"Pattern already added: {pattern}", style="yellow")
    
    if custom_patterns:
        console.print(f"\nAdded {len(custom_patterns)} custom patterns to .gitignore")
    
    return custom_patterns


def parse_args() -> argparse.Namespace:
    """Define and parse command‑line arguments."""
    parser = argparse.ArgumentParser(
        description="Automate onboarding of a local project folder to GitHub.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--project", "-p", type=str, default=".", help="Path to the project folder."
    )
    parser.add_argument(
        "--message", "-m", type=str, default="Initial commit", help="Commit message."
    )
    parser.add_argument(
        "--branch", "-b", type=str, default="main", help="Branch name to push."
    )
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default=None,
        help="Path to JSON or YAML config file with defaults.",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=str(Path.home() / ".git-onboard.log"),
        help="Path to log file.",
    )
    return parser.parse_args()


def main() -> None:
    """Main entry point for the script."""
    args = parse_args()
    log_file_path = Path(args.log_file)
    setup_logging(log_file_path)
    logger = logging.getLogger(__name__)
    logger.info("Starting onboarding script")
    
    # Load configuration defaults if provided
    config_defaults = load_config(Path(args.config)) if args.config else {}
    
    # Merge CLI arguments with config defaults (CLI takes precedence)
    project_path = Path(args.project or config_defaults.get("project", ".")).expanduser().resolve()
    commit_message = args.message or config_defaults.get("message", "Initial commit")
    branch_name = args.branch or config_defaults.get("branch", "main")
    
    # Determine package manager: CLI config -> config file -> auto detect
    if "package_manager" in config_defaults:
        pkg_manager = config_defaults["package_manager"]
    else:
        pkg_manager = detect_package_manager()
    
    # Display configuration summary
    table = Table(title="Configuration Summary")
    table.add_column("Setting", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")
    table.add_row("Project path", str(project_path))
    table.add_row("Commit message", commit_message)
    table.add_row("Branch", branch_name)
    table.add_row("Package manager", pkg_manager)
    console.print(table)
    
    # Prompt for .gitignore patterns first
    custom_patterns = prompt_gitignore_patterns(project_path)
    
    # Create .gitignore with custom patterns
    create_default_gitignore(project_path, custom_patterns)
    
    # Check for detached repository and attempt recovery
    if not is_git_repository(project_path):
        if recover_detached_repository(project_path, config_defaults):
            logger.info("Repository recovery completed")
            safe_print("Onboarding complete!", style="bold green")
            return
        else:
            # Recovery failed or was cancelled, continue with normal flow
            pass
    
    # If we reach here, either it's a normal repository or recovery was cancelled
    # Check if repository is already initialized and has commits
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"], 
            cwd=project_path, 
            capture_output=True, 
            text=True
        )
        if result.returncode == 0:
            # Repository has commits, ask user what to do
            console.print("\nRepository already has commits.", style="yellow")
            if not Confirm.ask("Continue with normal onboarding flow?", default=False):
                safe_print("Onboarding cancelled by user.", style="yellow")
                return
    except Exception:
        # Git command failed, continue with normal flow
        pass
    
    # Ensure prerequisites
    ensure_prerequisites(pkg_manager)
    
    # Ensure SSH key exists
    pub_key_path = ensure_ssh_key(console)
    
    # Do not attempt to upload SSH key automatically. The user should
    # manually add the SSH key to their GitHub account.
    
    # Initialize git repository
    initialize_repo(project_path)
    
    # Stage, commit, and ask for remote
    stage_and_commit(project_path, commit_message, branch_name)
    
    # Prompt user for remote URL
    remote_url = Prompt.ask(
        "Enter GitHub repository clone URL (HTTPS or SSH)", default=""
    ).strip()
    if not remote_url:
        safe_print("No remote URL provided. Exiting.", style="red")
        raise SystemExit(1)
    
    # Push to remote
    push_to_remote(project_path, branch_name, remote_url)
    logger.info("Completed onboarding process")
    safe_print("Onboarding complete!", style="bold green")


if __name__ == "__main__" and not sys.flags.interactive:
    # If run as a script, execute main() unless being imported or run in interactive mode.
            # Provide a way to run tests via python3 git-onboard.py test
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Remove the 'test' argument and run tests
        sys.argv.pop(1)
        import unittest

        class TestGitOnboard(unittest.TestCase):
            def setUp(self) -> None:
                # Create temporary directory for HOME
                self.tempdir = Path(tempfile.mkdtemp())
                self.original_home = os.environ.get("HOME")
                os.environ["HOME"] = str(self.tempdir)
                
                # Create .ssh directory
                ssh_dir = self.tempdir / ".ssh"
                ssh_dir.mkdir()
            
            def tearDown(self) -> None:
                # Restore HOME
                if self.original_home:
                    os.environ["HOME"] = self.original_home
                else:
                    del os.environ["HOME"]
                # Clean up temp directory
                shutil.rmtree(self.tempdir)
            
            def _mock_subprocess(self, fake_run_func, fake_check_output_func=None):
                """Helper method to mock subprocess functions."""
                original_run = subprocess.run
                original_check_output = subprocess.check_output
                
                subprocess.run = fake_run_func  # type: ignore
                if fake_check_output_func:
                    subprocess.check_output = fake_check_output_func  # type: ignore
                
                return original_run, original_check_output
            
            def _restore_subprocess(self, original_run, original_check_output=None):
                """Helper method to restore subprocess functions."""
                subprocess.run = original_run  # type: ignore
                if original_check_output:
                    subprocess.check_output = original_check_output  # type: ignore
            
            def test_ssh_key_generation(self) -> None:
                """Test SSH key generation."""
                # Remove any existing keys in temp
                ssh_dir = Path(os.environ["HOME"]) / ".ssh"
                for file in ssh_dir.glob("id_rsa*"):
                    file.unlink()
                
                # Mock subprocess.run to avoid actual key generation
                called: Dict[str, List[str]] = {}
                def fake_run(cmd, check=False, stdout=None, stderr=None, cwd=None):
                    called['cmd'] = cmd
                    # Simulate creation of key files
                    priv = ssh_dir / "id_rsa"
                    pub = ssh_dir / "id_rsa.pub"
                    priv.write_text("PRIVATEKEY")
                    pub.write_text("PUBLICKEY")
                    return None
                
                # Mock Confirm.ask to return True
                original_confirm_ask = Confirm.ask
                Confirm.ask = lambda prompt, default=False: True
                
                # Mock Prompt.ask to return immediately
                original_prompt_ask = Prompt.ask
                Prompt.ask = lambda prompt, default=None: "Done"
                
                original_run, _ = self._mock_subprocess(fake_run)
                try:
                    path = ensure_ssh_key(Console())
                    self.assertTrue(path.exists())
                    self.assertIn('ssh-keygen', ' '.join(called['cmd']))
                finally:
                    self._restore_subprocess(original_run)
                    Confirm.ask = original_confirm_ask
                    Prompt.ask = original_prompt_ask

            def test_dependency_install_stub(self) -> None:
                """Test installation function stubs out on unsupported manager."""
                with self.assertRaises(ValueError):
                    install_package('dummy', pkg_manager='unknown')

            def test_git_init_commit_push(self) -> None:
                """Test git workflow commands (init, add, commit, push) are invoked."""
                project = self.tempdir / "project"
                project.mkdir()
                # Create dummy file
                (project / "README.md").write_text("# Test")
                
                # Track calls
                calls: List[List[str]] = []
                def fake_run(args, cwd=None, check=False, capture_output=False, text=False):
                    calls.append(args)
                    # Return a mock result object
                    class MockResult:
                        def __init__(self):
                            self.returncode = 0
                            self.stdout = ""
                            self.stderr = ""
                    return MockResult()
                
                def fake_check_output(args, cwd=None, text=False):
                    return ""  # No remotes
                
                original_run, original_check_output = self._mock_subprocess(fake_run, fake_check_output)
                try:
                    # Initialize
                    initialize_repo(project)
                    stage_and_commit(project, "msg", "main")
                    # Push (simulate failure to avoid removal prompt)
                    push_to_remote(project, "main", "git@example.com:repo.git")
                except SystemExit:
                    pass  # Expected due to push failure and cleanup prompt
                finally:
                    self._restore_subprocess(original_run, original_check_output)
                
                # Ensure at least one git command was called
                self.assertTrue(any("git" in cmd[0] for cmd in calls))

            def test_is_git_repository(self) -> None:
                """Test git repository detection."""
                # Test with non-existent directory
                non_existent = Path("/tmp/non_existent_repo_test")
                self.assertFalse(is_git_repository(non_existent))
                
                # Test with directory without .git
                no_git_dir = self.tempdir / "no_git"
                no_git_dir.mkdir()
                self.assertFalse(is_git_repository(no_git_dir))
                
                # Test with directory containing .git
                with_git_dir = self.tempdir / "with_git"
                with_git_dir.mkdir()
                git_dir = with_git_dir / ".git"
                git_dir.mkdir()
                self.assertTrue(is_git_repository(with_git_dir))

            def test_calculate_file_hash(self) -> None:
                """Test file hash calculation."""
                test_file = self.tempdir / "test.txt"
                test_file.write_text("Hello, World!")
                
                hash1 = calculate_file_hash(test_file)
                hash2 = calculate_file_hash(test_file)
                
                self.assertEqual(hash1, hash2)
                self.assertIsInstance(hash1, str)
                self.assertEqual(len(hash1), 64)  # SHA256 hex length

            def test_compare_local_vs_remote(self) -> None:
                """Test file comparison between local and remote."""
                # Create local project
                local_project = self.tempdir / "local_project"
                local_project.mkdir()
                (local_project / "README.md").write_text("# Local Project")
                
                # Create remote clone
                remote_clone = self.tempdir / "remote_clone"
                remote_clone.mkdir()
                (remote_clone / "README.md").write_text("# Remote Project")
                (remote_clone / "new_file.txt").write_text("New file")
                
                # Mock git ls-files to return tracked files
                def fake_check_output(args, cwd=None, text=False):
                    if "ls-files" in args:
                        return "README.md\nnew_file.txt"
                    return ""
                
                original_run, original_check_output = self._mock_subprocess(lambda *args, **kwargs: None, fake_check_output)
                try:
                    modified, new, deleted = compare_local_vs_remote(local_project, remote_clone)
                    
                    # Should detect modified README.md
                    self.assertIn(Path("README.md"), modified)
                    # Should not have new files (local has no new_file.txt)
                    self.assertEqual(len(new), 0)
                    # Should have deleted files (new_file.txt exists in remote but not local)
                    self.assertIn(Path("new_file.txt"), deleted)
                finally:
                    self._restore_subprocess(original_run, original_check_output)

            def test_detect_recovery_scenario(self) -> None:
                """Test recovery scenario detection."""
                project = self.tempdir / "test_project"
                project.mkdir()
                
                # Mock Prompt.ask to return empty string (local-only scenario)
                original_prompt_ask = Prompt.ask
                Prompt.ask = lambda prompt, default=None: ""
                
                # Mock verify_remote_repository to raise SystemExit
                import sys
                module = sys.modules[__name__]
                original_verify = module.verify_remote_repository
                
                def fake_verify_remote(url):
                    raise SystemExit(1)
                
                module.verify_remote_repository = fake_verify_remote
                
                try:
                    scenario, remote_url = detect_recovery_scenario(project, {})
                    self.assertEqual(scenario, "local_only")
                    self.assertIsNone(remote_url)
                finally:
                    Prompt.ask = original_prompt_ask
                    module.verify_remote_repository = original_verify

            def test_recover_local_only_repository(self) -> None:
                """Test local-only repository recovery."""
                project = self.tempdir / "test_project"
                project.mkdir()
                (project / "test.txt").write_text("Test content")
                
                # Mock Confirm.ask to return True
                original_confirm_ask = Confirm.ask
                Confirm.ask = lambda prompt, default=True: True
                
                # Mock git commands
                def fake_run(args, cwd=None, check=False):
                    return None
                
                original_run, _ = self._mock_subprocess(fake_run)
                try:
                    result = recover_local_only_repository(project, {})
                    self.assertTrue(result)
                finally:
                    self._restore_subprocess(original_run)
                    Confirm.ask = original_confirm_ask

        unittest.main()
    else:
        main()
