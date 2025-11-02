#!/usr/bin/env python3
"""Ollama automatic setup wizard.

This tool provides complete Ollama installation and configuration automation:
1. Check if Ollama is installed
2. Install Ollama if needed (WSL/Linux)
3. Detect PC specs and store in database
4. Query database for optimal model
5. Pull recommended model from Ollama registry
6. Generate Modelfile with MCP rules and project context
7. Build custom model
8. Validate installation

For first-time users of NeuroHub.
"""

import subprocess
import sys
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any
import json


class OllamaSetup:
    """Ollama installation and setup automation."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize Ollama setup.
        
        Args:
            db_path: Database path for system specs
        """
        self.project_root = Path(__file__).parent.parent
        
        if db_path is None:
            self.db_path = self.project_root / "neurohub_llm.db"
        else:
            self.db_path = Path(db_path)
        
        self.modelfiles_dir = self.project_root / "modelfiles"
        self.modelfiles_dir.mkdir(exist_ok=True)

    def check_ollama_installed(self) -> bool:
        """Check if Ollama is installed.
        
        Returns:
            True if Ollama is available
        """
        try:
            result = subprocess.run(
                ['ollama', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"✅ Ollama is installed: {result.stdout.strip()}")
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        print("⚠️ Ollama is not installed")
        return False

    def install_ollama_linux(self) -> bool:
        """Install Ollama on Linux/WSL.
        
        Returns:
            True if successful
        """
        print("🔧 Installing Ollama on Linux/WSL...")
        
        try:
            # Official installation script
            result = subprocess.run(
                ['curl', '-fsSL', 'https://ollama.com/install.sh'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                install_script = result.stdout
                
                # Run installation script
                result = subprocess.run(
                    ['sh'],
                    input=install_script,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode == 0:
                    print("✅ Ollama installed successfully")
                    return True
                else:
                    print(f"❌ Installation failed: {result.stderr}")
                    return False
            else:
                print(f"❌ Failed to download installation script: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Installation error: {e}")
            return False

    def start_ollama_server(self) -> bool:
        """Start Ollama server in background.
        
        Returns:
            True if server started
        """
        try:
            # Check if server is already running
            result = subprocess.run(
                ['curl', '-s', 'http://localhost:11434/api/tags'],
                capture_output=True,
                timeout=2
            )
            if result.returncode == 0:
                print("✅ Ollama server is already running")
                return True
        except:
            pass
        
        try:
            print("🔧 Starting Ollama server...")
            subprocess.Popen(
                ['ollama', 'serve'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Wait a bit for server to start
            import time
            time.sleep(3)
            
            # Check if server is running
            result = subprocess.run(
                ['curl', '-s', 'http://localhost:11434/api/tags'],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                print("✅ Ollama server started")
                return True
            else:
                print("⚠️ Server may not be ready yet")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False

    def detect_and_save_specs(self) -> Dict[str, Any]:
        """Detect system specs and save to database.
        
        Returns:
            System specifications dictionary
        """
        from services.common.system_info import SystemInfoCollector
        
        print("🔍 Detecting system specifications...")
        
        collector = SystemInfoCollector(db_path=str(self.db_path))
        specs = collector.collect_all()
        
        print(f"\n=== Detected Specifications ===")
        print(f"CPU: {specs['cpu_model']}")
        print(f"CPU Cores: {specs['cpu_cores']}")
        print(f"RAM: {specs['ram_total_gb']:.2f} GB")
        print(f"GPU: {specs['gpu_model']}")
        print(f"GPU VRAM: {specs['gpu_vram_gb']:.2f} GB")
        
        # Save to database
        spec_id = collector.save_to_db(specs)
        print(f"\n✅ Saved to database (ID: {spec_id})")
        
        return specs

    def get_recommended_model(self) -> str:
        """Get recommended model from database.
        
        Returns:
            Recommended model name
        """
        from services.common.system_info import SystemInfoCollector
        
        collector = SystemInfoCollector(db_path=str(self.db_path))
        specs = collector.get_latest_specs()
        
        if specs:
            recommended = specs.get('recommended_model', 'qwen2.5:3b')
            print(f"📊 Recommended model: {recommended}")
            return recommended
        else:
            # Fallback
            print("⚠️ No specs in database, using default model")
            return 'qwen2.5:3b'

    def pull_model(self, model_name: str) -> bool:
        """Pull model from Ollama registry.
        
        Args:
            model_name: Model name to pull
            
        Returns:
            True if successful
        """
        print(f"📥 Pulling model: {model_name}")
        print("⏳ This may take several minutes...")
        
        try:
            result = subprocess.run(
                ['ollama', 'pull', model_name],
                capture_output=False,  # Show progress
                text=True,
                timeout=1800  # 30 minutes max
            )
            
            if result.returncode == 0:
                print(f"✅ Model {model_name} pulled successfully")
                return True
            else:
                print(f"❌ Failed to pull model")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Pull timeout (30 minutes)")
            return False
        except Exception as e:
            print(f"❌ Pull error: {e}")
            return False

    def generate_mcp_modelfile(self, base_model: str, custom_name: str = "neurohub-mcp") -> Path:
        """Generate Modelfile with MCP coding rules.
        
        Args:
            base_model: Base model name
            custom_name: Custom model name
            
        Returns:
            Path to generated Modelfile
        """
        print(f"📝 Generating Modelfile for {custom_name}...")
        
        # Read MCP coding rules
        rules_file = self.project_root / "docs" / "MCP_CODING_RULES.md"
        if rules_file.exists():
            with open(rules_file, 'r', encoding='utf-8') as f:
                mcp_rules = f.read()
        else:
            mcp_rules = "# MCP Coding Rules (file not found)"
        
        # Create Modelfile content
        modelfile_content = f"""FROM {base_model}

# MCP Coding Assistant for NeuroHub
# Automatically generated by ollama_setup.py

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40

SYSTEM \"\"\"
You are a highly skilled coding assistant specialized in generating production-ready Python code for the NeuroHub MCP (Model Context Protocol) system.

# MCP Coding Rules

{mcp_rules}

# Output Format
Always generate complete, working code with:
- argparse for CLI arguments
- Proper error handling
- Logging instead of print statements
- No input() function usage
- Safe file operations with pathlib
- Database operations using NeuroHub's DatabaseManager

Generate code that follows these rules strictly.
\"\"\"
"""
        
        # Save Modelfile
        modelfile_path = self.modelfiles_dir / f"{custom_name}.Modelfile"
        with open(modelfile_path, 'w', encoding='utf-8') as f:
            f.write(modelfile_content)
        
        print(f"✅ Modelfile created: {modelfile_path}")
        return modelfile_path

    def build_model(self, modelfile_path: Path, model_name: str) -> bool:
        """Build custom Ollama model from Modelfile.
        
        Args:
            modelfile_path: Path to Modelfile
            model_name: Name for the custom model
            
        Returns:
            True if successful
        """
        print(f"🔨 Building model: {model_name}")
        
        try:
            result = subprocess.run(
                ['ollama', 'create', model_name, '-f', str(modelfile_path)],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                print(f"✅ Model {model_name} built successfully")
                return True
            else:
                print(f"❌ Build failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Build error: {e}")
            return False

    def validate_installation(self, model_name: str) -> bool:
        """Validate Ollama installation and model.
        
        Args:
            model_name: Model name to test
            
        Returns:
            True if validation passed
        """
        print(f"✅ Validating installation...")
        
        try:
            # Test basic generation
            result = subprocess.run(
                ['ollama', 'run', model_name, 'Say "OK" if you can hear me'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout.strip():
                print(f"✅ Model {model_name} is working!")
                print(f"Response: {result.stdout.strip()[:100]}...")
                return True
            else:
                print(f"⚠️ Model did not respond as expected")
                return False
                
        except Exception as e:
            print(f"❌ Validation error: {e}")
            return False

    def run_full_setup(self) -> bool:
        """Run complete Ollama setup process.
        
        Returns:
            True if successful
        """
        print("\n" + "="*60)
        print("  🦙 NeuroHub Ollama Setup Wizard")
        print("="*60 + "\n")
        
        # Step 1: Check/Install Ollama
        if not self.check_ollama_installed():
            print("\n📦 Installing Ollama...")
            if not self.install_ollama_linux():
                print("❌ Setup failed at installation step")
                return False
        
        # Step 2: Start server
        print("\n🚀 Starting Ollama server...")
        if not self.start_ollama_server():
            print("⚠️ Server start warning, but continuing...")
        
        # Step 3: Detect specs
        print("\n🔍 Detecting system specifications...")
        specs = self.detect_and_save_specs()
        
        # Step 4: Get recommendation
        print("\n📊 Getting model recommendation...")
        recommended_model = self.get_recommended_model()
        
        # Step 5: Pull model
        print(f"\n📥 Pulling base model: {recommended_model}")
        if not self.pull_model(recommended_model):
            print("⚠️ Pull failed, trying smaller model...")
            recommended_model = 'qwen2.5:3b'
            if not self.pull_model(recommended_model):
                print("❌ Setup failed at pull step")
                return False
        
        # Step 6: Generate Modelfile
        print("\n📝 Generating MCP Modelfile...")
        modelfile_path = self.generate_mcp_modelfile(recommended_model, "neurohub-mcp")
        
        # Step 7: Build model
        print("\n🔨 Building custom model...")
        if not self.build_model(modelfile_path, "neurohub-mcp"):
            print("❌ Setup failed at build step")
            return False
        
        # Step 8: Validate
        print("\n✅ Validating installation...")
        if not self.validate_installation("neurohub-mcp"):
            print("⚠️ Validation warning, but model was built")
        
        print("\n" + "="*60)
        print("  ✅ Setup Complete!")
        print("="*60)
        print(f"\nYour custom model 'neurohub-mcp' is ready to use!")
        print(f"Base model: {recommended_model}")
        print(f"System specs saved to database: {self.db_path}")
        print(f"\nTo use the model:")
        print(f"  ollama run neurohub-mcp")
        print(f"\nOr in NeuroHub:")
        print(f"  python services/llm/provider_ollama.py --model neurohub-mcp --prompt 'your prompt'")
        
        return True


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Ollama automatic setup wizard')
    parser.add_argument('--db', type=str, help='Database path')
    parser.add_argument('--check-only', action='store_true', help='Only check if Ollama is installed')
    parser.add_argument('--install-only', action='store_true', help='Only install Ollama')
    parser.add_argument('--specs-only', action='store_true', help='Only detect and save specs')
    parser.add_argument('--model', type=str, help='Specific model to pull and setup')
    
    args = parser.parse_args()
    
    setup = OllamaSetup(db_path=args.db)
    
    if args.check_only:
        setup.check_ollama_installed()
        sys.exit(0)
    
    if args.install_only:
        if setup.check_ollama_installed():
            print("✅ Ollama already installed")
        else:
            setup.install_ollama_linux()
        sys.exit(0)
    
    if args.specs_only:
        setup.detect_and_save_specs()
        sys.exit(0)
    
    if args.model:
        # Custom model setup
        setup.start_ollama_server()
        setup.detect_and_save_specs()
        if setup.pull_model(args.model):
            modelfile = setup.generate_mcp_modelfile(args.model, "neurohub-custom")
            setup.build_model(modelfile, "neurohub-custom")
            setup.validate_installation("neurohub-custom")
    else:
        # Full automatic setup
        success = setup.run_full_setup()
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
