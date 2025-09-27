"""
Setup script for the Semantic Database Schema Mapping System
"""

import os
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version.split()[0]} detected")
    return True


def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    try:
        # Install main dependencies
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Main dependencies installed")
        
        # Try to download spaCy model
        try:
            subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
            print("✅ spaCy English model downloaded")
        except subprocess.CalledProcessError:
            print("⚠️  Could not download spaCy model. You may need to install it manually:")
            print("   python -m spacy download en_core_web_sm")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False


def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    
    directories = [
        "logs",
        "cache",
        "cache/transformers",
        "examples",
        "outputs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    print("✅ Directories created")


def create_env_file():
    """Create .env file with default settings"""
    env_file = Path(".env")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return
    
    print("📝 Creating .env file...")
    
    env_content = """# Semantic Mapping System Configuration

# Application
DEBUG=true
LOG_LEVEL=INFO

# Server
HOST=127.0.0.1
PORT=8000

# AI/ML Models
TRANSFORMERS_CACHE=./cache/transformers
SPACY_MODEL=en_core_web_sm
SENTENCE_TRANSFORMER_MODEL=all-MiniLM-L6-v2

# Processing
MAX_WORKERS=4
CONFIDENCE_THRESHOLD=0.7

# File handling
MAX_FILE_SIZE=52428800
"""
    
    with open(env_file, "w") as f:
        f.write(env_content)
    
    print("✅ .env file created")


def run_basic_test():
    """Run a basic test to verify installation"""
    print("🧪 Running basic test...")
    
    try:
        # Test imports
        sys.path.append(str(Path.cwd() / "src"))
        
        from src.core.schema_parser import SchemaParser
        from src.core.config import settings
        
        # Test basic functionality
        parser = SchemaParser()
        print(f"✅ Schema parser initialized")
        print(f"✅ Settings loaded: {settings.VERSION}")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic test failed: {e}")
        return False


def main():
    """Main setup function"""
    print("🚀 Semantic Database Schema Mapping System - Setup")
    print("=" * 55)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Create directories
    create_directories()
    
    # Create environment file
    create_env_file()
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Run basic test
    if not run_basic_test():
        print("⚠️  Setup completed but basic test failed")
        print("   You may need to check your installation manually")
        return False
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("  1. Run examples: python run.py --examples")
    print("  2. Start API server: python run.py --server")
    print("  3. Process a file: python run.py --file data/sample_customers.csv")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
