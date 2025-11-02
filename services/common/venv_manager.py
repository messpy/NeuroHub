#!/usr/bin/env python3
"""Virtual environment manager for automatic venv creation and package installation.

This module detects pip install commands or import errors and automatically
creates/activates virtual environments.

Features:
- Detect pip install commands in code
- Detect import errors
- Auto-create venv if not exists
- Auto-install missing packages
- Activate venv for subprocess execution
"""

import subprocess
import sys
import os
from pathlib import Path
from typing import List, Optional, Tuple
import re


class VenvManager:
    """Manage virtual environments automatically."""

    def __init__(self, project_root: Optional[Path] = None, venv_name: str = "venv"):
        """Initialize venv manager.
        
        Args:
            project_root: Project root directory. Defaults to NeuroHub root.
            venv_name: Virtual environment directory name.
        """
        if project_root is None:
            # Default to NeuroHub root
            self.project_root = Path(__file__).parent.parent.parent
        else:
            self.project_root = Path(project_root)
        
        self.venv_name = venv_name
        self.venv_path = self.project_root / venv_name
        self.python_executable = self._get_python_executable()

    def _get_python_executable(self) -> Path:
        """Get Python executable path in venv.
        
        Returns:
            Path to Python executable
        """
        if sys.platform == 'win32':
            return self.venv_path / 'Scripts' / 'python.exe'
        else:
            return self.venv_path / 'bin' / 'python'

    def venv_exists(self) -> bool:
        """Check if virtual environment exists.
        
        Returns:
            True if venv exists
        """
        return self.venv_path.exists() and self.python_executable.exists()

    def create_venv(self) -> bool:
        """Create virtual environment.
        
        Returns:
            True if successful
        """
        try:
            print(f"🔧 Creating virtual environment at {self.venv_path}...")
            subprocess.run(
                [sys.executable, '-m', 'venv', str(self.venv_path)],
                check=True,
                capture_output=True,
                text=True
            )
            print("✅ Virtual environment created successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create venv: {e.stderr}")
            return False

    def install_package(self, package: str) -> bool:
        """Install package in virtual environment.
        
        Args:
            package: Package name (e.g., 'requests', 'numpy==1.21.0')
            
        Returns:
            True if successful
        """
        if not self.venv_exists():
            if not self.create_venv():
                return False
        
        try:
            print(f"📦 Installing {package} in virtual environment...")
            
            pip_executable = self.venv_path / ('Scripts' if sys.platform == 'win32' else 'bin') / 'pip'
            
            subprocess.run(
                [str(self.python_executable), '-m', 'pip', 'install', package],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"✅ {package} installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e.stderr}")
            return False

    def install_requirements(self, requirements_file: Optional[Path] = None) -> bool:
        """Install packages from requirements.txt.
        
        Args:
            requirements_file: Path to requirements.txt. Defaults to project root.
            
        Returns:
            True if successful
        """
        if requirements_file is None:
            requirements_file = self.project_root / 'requirements.txt'
        
        if not requirements_file.exists():
            print(f"⚠️ Requirements file not found: {requirements_file}")
            return False
        
        if not self.venv_exists():
            if not self.create_venv():
                return False
        
        try:
            print(f"📦 Installing packages from {requirements_file}...")
            subprocess.run(
                [str(self.python_executable), '-m', 'pip', 'install', '-r', str(requirements_file)],
                check=True,
                capture_output=True,
                text=True
            )
            print("✅ All packages installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install requirements: {e.stderr}")
            return False

    def detect_pip_install(self, code: str) -> List[str]:
        """Detect pip install commands in code.
        
        Args:
            code: Python code as string
            
        Returns:
            List of package names to install
        """
        packages = []
        
        # Pattern: subprocess.run(['pip', 'install', 'package'])
        pattern1 = r"subprocess\.run\(\s*\[.*?['\"]pip['\"].*?['\"]install['\"].*?['\"]([^'\"]+)['\"]"
        matches1 = re.findall(pattern1, code)
        packages.extend(matches1)
        
        # Pattern: os.system('pip install package')
        pattern2 = r"os\.system\(['\"]pip\s+install\s+([^'\"]+)['\"]"
        matches2 = re.findall(pattern2, code)
        packages.extend(matches2)
        
        # Pattern: !pip install (Jupyter style)
        pattern3 = r"!\s*pip\s+install\s+([^\n]+)"
        matches3 = re.findall(pattern3, code)
        for match in matches3:
            # Split by space and get package names
            pkgs = [p.strip() for p in match.split() if not p.startswith('-')]
            packages.extend(pkgs)
        
        return list(set(packages))  # Remove duplicates

    def detect_imports(self, code: str) -> List[str]:
        """Detect import statements in code.
        
        Args:
            code: Python code as string
            
        Returns:
            List of module names
        """
        imports = []
        
        # Pattern: import module
        pattern1 = r"^\s*import\s+([a-zA-Z0-9_]+)"
        matches1 = re.findall(pattern1, code, re.MULTILINE)
        imports.extend(matches1)
        
        # Pattern: from module import ...
        pattern2 = r"^\s*from\s+([a-zA-Z0-9_]+)\s+import"
        matches2 = re.findall(pattern2, code, re.MULTILINE)
        imports.extend(matches2)
        
        return list(set(imports))  # Remove duplicates

    def check_import_available(self, module_name: str) -> bool:
        """Check if module can be imported.
        
        Args:
            module_name: Module name to check
            
        Returns:
            True if module can be imported
        """
        try:
            result = subprocess.run(
                [str(self.python_executable), '-c', f'import {module_name}'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def run_with_venv(self, script_path: Path, args: Optional[List[str]] = None) -> Tuple[int, str, str]:
        """Run Python script in virtual environment.
        
        Args:
            script_path: Path to Python script
            args: Command-line arguments
            
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        if not self.venv_exists():
            if not self.create_venv():
                return (1, '', 'Failed to create virtual environment')
        
        cmd = [str(self.python_executable), str(script_path)]
        if args:
            cmd.extend(args)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_root)
            )
            return (result.returncode, result.stdout, result.stderr)
        except Exception as e:
            return (1, '', str(e))

    def auto_setup(self, code: Optional[str] = None, requirements_file: Optional[Path] = None) -> bool:
        """Automatically setup venv and install packages.
        
        Args:
            code: Python code to scan for dependencies
            requirements_file: Path to requirements.txt
            
        Returns:
            True if successful
        """
        # Create venv if not exists
        if not self.venv_exists():
            print("🔧 Virtual environment not found. Creating...")
            if not self.create_venv():
                return False
        
        # Install from requirements.txt if provided
        if requirements_file and requirements_file.exists():
            if not self.install_requirements(requirements_file):
                return False
        
        # Detect and install packages from code
        if code:
            packages = self.detect_pip_install(code)
            if packages:
                print(f"📦 Detected packages to install: {', '.join(packages)}")
                for package in packages:
                    if not self.install_package(package):
                        return False
            
            # Check imports
            imports = self.detect_imports(code)
            missing_imports = [imp for imp in imports if not self.check_import_available(imp)]
            if missing_imports:
                print(f"⚠️ Missing imports detected: {', '.join(missing_imports)}")
                # Try to install missing imports
                for imp in missing_imports:
                    # Skip standard library modules
                    if imp in ['os', 'sys', 'subprocess', 're', 'json', 'pathlib', 'datetime']:
                        continue
                    self.install_package(imp)
        
        return True


def main():
    """CLI entry point for venv management."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Manage virtual environments automatically')
    parser.add_argument('--create', action='store_true', help='Create virtual environment')
    parser.add_argument('--install', type=str, help='Install package')
    parser.add_argument('--requirements', type=str, help='Install from requirements.txt')
    parser.add_argument('--run', type=str, help='Run script in venv')
    parser.add_argument('--check-code', type=str, help='Check code file for dependencies')
    
    args = parser.parse_args()
    
    manager = VenvManager()
    
    if args.create:
        manager.create_venv()
    
    if args.install:
        manager.install_package(args.install)
    
    if args.requirements:
        manager.install_requirements(Path(args.requirements))
    
    if args.run:
        returncode, stdout, stderr = manager.run_with_venv(Path(args.run))
        print(stdout)
        if stderr:
            print(stderr, file=sys.stderr)
        sys.exit(returncode)
    
    if args.check_code:
        code_file = Path(args.check_code)
        if code_file.exists():
            with open(code_file, 'r', encoding='utf-8') as f:
                code = f.read()
            
            packages = manager.detect_pip_install(code)
            imports = manager.detect_imports(code)
            
            print(f"\n📦 Detected pip install: {packages}")
            print(f"📥 Detected imports: {imports}")
            
            missing = [imp for imp in imports if not manager.check_import_available(imp)]
            if missing:
                print(f"\n⚠️ Missing imports: {missing}")


if __name__ == '__main__':
    main()
