# Export Repository to Markdown (`repo2md.py`)

This script allows you to export files from a local directory or a Git repository to a Markdown file. Useful for analyzing repositories, documenting projects, or processing content for artificial intelligence applications.

---

## Features

- **Process Local Files or Git Repositories**.
- **Configuration Support**: Customize included extensions, excluded directories, and maximum file size via a `config.yaml` file.
- **Obey `.gitignore`**: Option to exclude files listed in `.gitignore`.
- **Markdown Export**: Includes code content and highlighted languages.
- **Support for Large-Scale Directories and Files**.

---

## Requirements

- Python 3.8 or higher.
- Additional Dependencies (installed with `pip`):
- `pyyaml`

---

## Installation

1. **Clone this Repository** or copy the files to your project directory.

2. **Install the Dependencies**:

```bash
pip install -r requirements.txt
```

3. **Configure the `config.yaml` File**:

This file contains the key parameters for execution.

**Example Configuration**:

```yaml
max_file_size: 1048576 # Maximum size in bytes (1 MB)
excluded_dirs:
- .venv
- .git
- node_modules
included_extensions:
.py: python
.yaml: yaml
.json: json
```

---

## Usage

Run the script from the command line with the following options:

### **Basic Example**

Process a local directory:

```bash
python3 repo2md.py ./ --output repository
```

### **Process a Git Repository**

Clone a repository and process its contents:

```bash
python3 repo2md.py https://github.com/user/repo.git --git --output repository
```

### **Respect `.gitignore`**

To exclude files listed in `.gitignore`:

```bash
python3 repo2md.py ./ --output repository --obey-gitignore
```

### **Custom Excluded Directories**
Exclude additional directories with `--exclude-dirs`:

```bash
python3 repo2md.py ./ --output repository --exclude-dirs dist build
```

---

## Script Options

| Option | Description |
|---------------------|------------------------------------------------------------------------------|
| `source` | Local path or URL of a Git repository. |
| `--config` | YAML configuration file (default: `config.yaml`). |
| `--output` | Base name for the generated Markdown file. |
| `--git` | Indicates that the origin is a Git repository (requires valid URL). |
| `--exclude-dirs` | List of additional directories to exclude. |
| `--obey-gitignore` | Respect exclusions defined in the repository's `.gitignore`. |

---

## License

This project is licensed under the [MIT License](LICENSE).
