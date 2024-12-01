import os
import subprocess
import yaml
import shutil
import tempfile
import logging
from datetime import datetime


class RepositoryExporter:
    def __init__(self, source, output_file, config_file, is_git, cli_excluded_dirs, obey_gitignore):
        # Set up logging first
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(__name__)

        # Initialize other attributes
        self.source = source
        self.output_file = self.generate_output_filename(output_file)
        self.is_git = is_git
        self.temp_dir = None
        self.snapshot_time = datetime.now()
        self.config = self.load_config(config_file)
        self.excluded_dirs = cli_excluded_dirs or self.config.get("excluded_dirs", [])
        self.included_extensions = self.config.get("included_extensions", {})
        self.obey_gitignore = obey_gitignore
        self.gitignore_patterns = self.load_gitignore() if obey_gitignore else []

    def load_config(self, config_file="config.yaml"):
        """
        Load the configuration from a YAML file.
        """
        try:
            with open(config_file, "r", encoding="utf-8") as file:
                config = yaml.safe_load(file)
                if not config:
                    self.logger.error(f"Configuration file {config_file} is empty or invalid.")
                    raise ValueError(f"Configuration file {config_file} is empty or invalid.")
                self.logger.info(f"Loaded config: {config}")
                return config
        except FileNotFoundError:
            self.logger.error(f"Configuration file not found: {config_file}")
            raise ValueError(f"Configuration file not found: {config_file}")
        except yaml.YAMLError as e:
            self.logger.error(f"Error parsing YAML file {config_file}: {e}")
            raise ValueError(f"Error parsing YAML file {config_file}: {e}")

    def load_gitignore(self):
        """
        Load patterns from .gitignore if present.
        """
        gitignore_path = os.path.join(self.source, ".gitignore")
        if os.path.exists(gitignore_path):
            try:
                with open(gitignore_path, "r", encoding="utf-8") as file:
                    patterns = [line.strip() for line in file if line.strip() and not line.startswith("#")]
                    self.logger.info(f"Loaded .gitignore patterns: {patterns}")
                    return patterns
            except Exception as e:
                self.logger.error(f"Error reading .gitignore: {e}")
        return []

    @staticmethod
    def generate_output_filename(base_name):
        """
        Generate a filename with the current date and time appended.
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"{base_name}_{timestamp}.md"

    def clone_repository(self):
        """
        Clone the Git repository into a temporary directory.
        """
        self.temp_dir = tempfile.mkdtemp()
        self.logger.info(f"Cloning repository from {self.source} into {self.temp_dir}...")
        try:
            subprocess.run(["git", "clone", self.source, self.temp_dir], check=True)
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error cloning repository: {e}")
            raise

    def cleanup(self):
        """
        Clean up temporary directory.
        """
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def is_excluded(self, path):
        """
        Check if a path matches excluded directories or .gitignore patterns.
        """
        # Check against excluded directories
        for excluded_dir in self.excluded_dirs:
            if path.startswith(os.path.join(self.source, excluded_dir)):
                self.logger.debug(f"Excluding directory (by config): {path}")
                return True

        # Check against .gitignore patterns
        for pattern in self.gitignore_patterns:
            if os.path.fnmatch.fnmatch(path, os.path.join(self.source, pattern)):
                self.logger.debug(f"Excluding file (by .gitignore): {path}")
                return True

        return False

    def is_file_valid(self, file_path):
        """
        Check if a file is valid based on size, included extensions, and exclusions.
        """
        if self.is_excluded(file_path):
            self.logger.info(f"Excluding file (by exclusion rules): {file_path}")
            return False

        try:
            file_size = os.path.getsize(file_path)
            if file_size > self.config.get("max_file_size", 1048576):
                self.logger.info(f"Excluding file (by size): {file_path}")
                return False

            file_extension = os.path.splitext(file_path)[-1].lower()
            if file_extension in self.included_extensions.keys():
                self.logger.info(f"Including file: {file_path}")
                return True
            else:
                self.logger.info(f"Excluding file (by extension): {file_path}")
                return False
        except (FileNotFoundError, PermissionError) as e:
            self.logger.error(f"Error accessing file {file_path}: {e}")
            return False

    def get_language_from_extension(self, file_extension):
        """
        Get the programming language for syntax highlighting based on the file extension.
        """
        return self.included_extensions.get(file_extension, "")  # Default: no language

    def export(self):
        """
        Export repository files to a Markdown file.
        """
        source_dir = self.temp_dir if self.is_git else self.source

        if not os.path.exists(source_dir):
            self.logger.error(f"Source directory does not exist: {source_dir}")
            raise ValueError(f"Source directory does not exist: {source_dir}")

        snapshot_time_str = self.snapshot_time.strftime("%Y-%m-%d %H:%M:%S")
        with open(self.output_file, "w", encoding="utf-8") as markdown_file:
            # Add snapshot time to the Markdown header
            markdown_file.write(f"# Repository Snapshot\n\n")
            markdown_file.write(f"**Snapshot taken on:** {snapshot_time_str}\n\n")
            markdown_file.write("---\n\n")

            for root, dirs, files in os.walk(source_dir):
                self.logger.info(f"Checking directory: {root}")
                dirs[:] = [d for d in dirs if not self.is_excluded(os.path.join(root, d))]

                for file in files:
                    file_path = os.path.join(root, file)
                    file_extension = os.path.splitext(file)[-1].lower()
                    self.logger.info(f"Found file: {file_path} with extension: {file_extension}")

                    if self.is_file_valid(file_path):
                        self.logger.info(f"Including file: {file_path}")
                        try:
                            with open(file_path, "r", encoding="utf-8") as code_file:
                                content = code_file.read()

                            relative_path = os.path.relpath(file_path, source_dir)
                            language = self.get_language_from_extension(file_extension)

                            markdown_file.write(f"## File: `{relative_path}`\n\n")
                            markdown_file.write(f"```{language}\n{content}\n```\n\n")
                        except Exception as e:
                            self.logger.error(f"Error reading file {file_path}: {e}")

        self.logger.info(f"Repository content exported to {self.output_file}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Export files from a local directory or Git repository to a Markdown file.")
    parser.add_argument("source", help="Path to the local directory or URL of the Git repository.")
    parser.add_argument("--config", default="config.yaml", help="Path to the YAML configuration file (default: config.yaml).")
    parser.add_argument("--output", default="repository", help="Base name for the output Markdown file (timestamp will be appended).")
    parser.add_argument("--git", action="store_true", help="Specify if the source is a Git repository URL.")
    parser.add_argument("--exclude-dirs", nargs="*", help="Directories to exclude from processing.")
    parser.add_argument("--obey-gitignore", action="store_true", help="Respect the .gitignore file in the repository.")

    args = parser.parse_args()

    exporter = RepositoryExporter(args.source, args.output, args.config, args.git, args.exclude_dirs, args.obey_gitignore)

    try:
        if args.git:
            exporter.clone_repository()
        exporter.export()
    finally:
        if args.git:
            exporter.cleanup()
