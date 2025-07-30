<div align="center">

  ![Project Icon](./assets/icon.png)
</div>

# Git Onboard
<div align="center">

[![][Commit Activity]](https://github.com/1BitCode-Com/git-onboard)
[![][Watchers]](https://github.com/1BitCode-Com/git-onboard)
[![][License]](https://github.com/1BitCode-Com/git-onboard/blob/master/LICENSE)
[![][Stars]](https://github.com/1BitCode-Com/git-onboard)
[![][Forks]](https://github.com/1BitCode-Com/git-onboard)
![Python](https://img.shields.io/badge/-Python-red?style=flat&logo=python&logoColor=white)

[![GitHub](https://img.shields.io/badge/GitHub-git--onboard-blue?style=flat-square&logo=github)](https://github.com/1BitCode-Com/git-onboard)
[![GitLab](https://img.shields.io/badge/GitLab-git--onboard-orange?style=flat-square&logo=gitlab)](https://gitlab.com/1BitCode-Com/git-onboard)
</div>

> **Automate the onboarding of local project folders to (GitHub, GitLab, Bitbucket) with intelligent recovery capabilities…**

**Git Onboard** is a Python script designed to streamline the process of pushing local project folders to (GitHub, GitLab, Bitbucket). It handles everything from ensuring required tools are installed and generating SSH keys, to initializing a Git repository, committing your code, and pushing it to a remote repository—all through a friendly, interactive command‑line interface.

## 🚀 New Features (Latest Update)

### **Intelligent Repository Recovery**
- **Detached Repository Detection**: Automatically detects when `.git` folder is missing but local files exist
- **Dual Recovery Scenarios**: Handles both remote repository recovery and local-only recovery
- **Smart Branch Management**: Automatically creates `main` branch (modern standard) and handles branch conflicts
- **Push Conflict Resolution**: Offers options to pull remote changes or force push when conflicts occur

### **Enhanced .gitignore Management**
- **Smart Detection**: Automatically detects existing `.gitignore` files and skips prompts
- **Pattern Filtering**: Applies `.gitignore` patterns during file comparison to exclude ignored files
- **Custom Patterns**: Interactive prompts for custom ignore patterns with multiple format support

### **Improved Error Handling**
- **Robust Git Operations**: Better handling of git command failures with informative error messages
- **Conflict Resolution**: Automatic detection and resolution of push conflicts
- **Branch Compatibility**: Seamless handling of different default branches (main/master)

## Features

- **Environment Preparation**: Detects and installs missing prerequisites (such as `git` and `ssh-keygen`) using the appropriate package manager (`apt`, `dnf`, `yum`, or `brew`).
- **SSH Key Management**: Checks for an existing SSH key and generates one if needed, printing the public key for easy addition to your (GitHub, GitLab, Bitbucket) account.
- **Git Repository Initialization**: Initializes the project directory as a Git repository if it isn't already.
- **Custom `.gitignore` Support**: Interactively prompts you to specify directories, files, or file patterns (e.g., `*.mp3; report.pdf; *.jpeg`) that should be ignored by Git and appends them to a `.gitignore` file.
- **Commit and Push Automation**: Stages all files, creates a commit with a message of your choice on a specified branch, and pushes to the remote repository.
- **Logging and User Prompts**: Provides readable output and logs actions to a rotating log file.
- **Cross-Platform Ready**: Structured to support multiple package managers, making it easy to adapt for different Linux distributions and macOS.
- **Unit Tests Included**: Contains a suite of unit tests for core functionality using Python's `unittest` module.

### **Recovery Workflow Features**
- **Missing .git Detection**: Automatically detects when Git repository is missing but files exist
- **Remote Repository Verification**: Validates remote repository accessibility before recovery
- **File Comparison**: Compares local files with remote repository to identify changes
- **Selective Staging**: Only stages modified/new files during recovery
- **Conflict Resolution**: Handles push conflicts with pull/force push options

## Prerequisites

- Python 3.7+
- At least one of the following package managers installed: `apt`, `dnf`, `yum`, or `brew`

## Installation

### Quick Start

```bash
# Clone the repository
git clone https://github.com/1BitCode-Com/git-onboard.git
cd git-onboard

# Run directly
python3 git_onboard.py
```

### From Source

1. Clone or download this repository to your local machine.
2. Ensure the script `git_onboard.py` is located at the root of your project directory (the folder you wish to push to GitHub, GitLab, Bitbucket).

### Using pip (when published)

```bash
pip install git-onboard
git-onboard
```

## Usage

### Basic Usage

Run the script from the root of your project directory:

```bash
python3 git_onboard.py
```

### Advanced Usage

```bash
# Specify project path
python3 git_onboard.py -p /path/to/your/project

# Custom commit message and branch
python3 git_onboard.py -m "Initial commit" -b main

# Use configuration file
python3 git_onboard.py -c config.json

# Custom log file
python3 git_onboard.py --log-file /path/to/log.txt
```

The script will guide you through the following steps:

1. **Checking Prerequisites**: Verifies and installs `git` and `ssh-keygen` if they are missing.
2. **SSH Key Setup**: Detects whether you have an existing SSH key. If not, it generates one and prints the public key for you to add to GitHub (`https://github.com/settings/keys`).
3. **Initialize Repository**: Initializes a new Git repository in your project directory, if needed.
4. **`.gitignore` Configuration**: Prompts you to specify any directories, files, or extensions you want Git to ignore (e.g. `node_modules/`, `dist/`, `*.mp3; report.pdf`), and updates/creates a `.gitignore` file accordingly.
5. **Commit and Push**: Prompts you for a commit message and branch name (default is `main`), then stages and commits your changes.
6. **Remote Setup**: Asks for the clone URL of your remote (GitHub, GitLab, Bitbucket) repository (SSH or HTTPS) and pushes your commit. Make sure you have created a repository on (GitHub, GitLab, Bitbucket) ahead of time and copy its clone URL.

### Recovery Scenarios

The script now handles two recovery scenarios:

#### **Scenario 1: Remote Repository Exists**
- Detects missing `.git` folder but local files exist
- Prompts for (GitHub, GitLab, Bitbucket) repository URL
- Verifies remote repository accessibility
- Compares local files with remote
- Stages only modified/new files
- Commits and pushes changes

#### **Scenario 2: Local-Only Repository**
- Detects missing `.git` folder with no remote
- Creates new local Git repository
- Stages all files
- Creates initial commit
- Provides instructions for later (GitHub, GitLab, Bitbucket) setup

### Command‑Line Options

You can customize the script's behavior using these optional arguments:

- `--project` (`-p`): Specify a different project folder (default: current directory).
- `--message` (`-m`): Specify a custom commit message (default: "Initial commit").
- `--branch` (`-b`): Specify the branch name to push to (default: `main`).
- `--config` (`-c`): Provide a JSON or YAML file with default values for the above options.
- `--log-file`: Specify a custom path for the log file (default: `~/.git-onboard.log`).

Run `python3 git_onboard.py --help` to see the full list of available options.

## Configuration File

You can create a configuration file (JSON or YAML) to set default values:

```json
{
  "project": "/path/to/project",
  "message": "Initial commit",
  "branch": "main"
}
```

## Creating a (GitHub, GitLab, Bitbucket) Repository

Before pushing, create a new repository on (GitHub, GitLab, Bitbucket):

1. Log in to (GitHub, GitLab, Bitbucket) and click **New Repository**.
2. Enter a repository name (e.g. `git-onboard`) and an optional description.
3. Leave the options to add a README, `.gitignore`, or license unchecked (the script manages these).
4. Click **Create repository**.
5. Copy the repository's clone URL (SSH or HTTPS) and paste it into the script when prompted.

## Development

### Running Tests

```bash
# Run all tests
python3 git_onboard.py test

# Run external tests
python3 -m pytest tests/ -v
```

### Building

```bash
# Install in development mode
pip install -e .

# Build package
python setup.py sdist bdist_wheel
```

### Using Make

```bash
# Show all available commands
make help

# Run tests
make test

# Clean build artifacts
make clean

# Build package
make build
```

## Testing

Run the included test suite:

```bash
python3 git_onboard.py test
```

The tests cover:
- SSH key generation
- Git repository operations
- File comparison and recovery
- Error handling scenarios

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Quick Start for Contributors

```bash
# Fork and clone the repository
git clone https://github.com/1BitCode-Com/git-onboard.git
cd git-onboard

# Install in development mode
pip install -e .

# Run tests
python3 git_onboard.py test
```

## Security

Please see our [Security Policy](SECURITY.md) for reporting vulnerabilities.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Code of Conduct

This project adheres to the Contributor Covenant Code of Conduct. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes and version history.

---

This script aims to automate the mundane parts of onboarding your project to (GitHub, GitLab, Bitbucket), so you can focus on coding. If you find it useful or have suggestions, please let us know!

<div align="center">

**If you'd like to share this project:**


[![Share on Twitter](https://img.shields.io/badge/Twitter-Share-black?style=flat-square&logo=x&logoColor=white)](https://x.com/intent/tweet?url=https%3A%2F%2Fgithub.com%2F1BitCode-Com%2Fgit-onboard&text=Check%20out%20Git%20Onboard)  [![Share on Facebook](https://img.shields.io/badge/Facebook-Share-blue?style=flat-square&logo=facebook&logoColor=white)](https://www.facebook.com/sharer/sharer.php?u=https%3A%2F%2Fgithub.com%2F1BitCode-Com%2Fgit-onboard)  [![Share on LinkedIn](https://img.shields.io/badge/LinkedIn-Share-blue?style=flat-square&logo=linkedin&logoColor=white)](https://www.linkedin.com/sharing/share-offsite/?url=https%3A%2F%2Fgithub.com%2F1BitCode-Com%2Fgit-onboard)  [![Share on Reddit](https://img.shields.io/badge/Reddit-Share-orange?style=flat-square&logo=reddit&logoColor=white)](https://www.reddit.com/submit?url=https%3A%2F%2Fgithub.com%2F1BitCode-Com%2Fgit-onboard&title=Git%20Onboard)  [![Share on WhatsApp](https://img.shields.io/badge/WhatsApp-Share-green?style=flat-square&logo=whatsapp&logoColor=white)](https://api.whatsapp.com/send?text=Check%20out%20Git%20Onboard%20https%3A%2F%2Fgithub.com%2F1BitCode-Com%2Fgit-onboard)  [![Share via Email](https://img.shields.io/badge/Email-Share-red?style=flat-square&logo=gmail&logoColor=white)](mailto:?subject=Check%20out%20Git%20Onboard&body=I%20found%20this%20project%3A%20https%3A%2F%2Fgithub.com%2F1BitCode-Com%2Fgit-onboard)

</div>




[Commit Activity]: https://badgen.net/github/last-commit/1BitCode-Com/git-onboard?label=Commit%20Activity&color=red
[Watchers]: https://badgen.net/github/watchers/1BitCode-Com/git-onboard?label=Watchers&color=red
[License]: https://badgen.net/github/license/1BitCode-Com/git-onboard?label=License&color=red
[Stars]: https://badgen.net/github/stars/1BitCode-Com/git-onboard?label=GitHub%20Stars&color=red
[Forks]: https://badgen.net/github/forks/1BitCode-Com/git-onboard?label=Forks&color=red
