#!/usr/bin/env python3
"""
Development setup script for SakeMonkey Recipe Database
Handles both conda environment and Docker setup
"""

import subprocess
import sys
import os
import argparse

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def setup_conda():
    """Setup conda environment"""
    print("=== Setting up Conda Environment ===")
    
    # Check if conda is available
    try:
        subprocess.run(["conda", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Conda not found. Please install Anaconda or Miniconda first.")
        return False
    
    # Create environment
    if not run_command("conda env create -f environment.yml", "Creating SakeMonkey conda environment"):
        print("❌ Failed to create conda environment")
        return False
    
    # Install additional GUI packages
    gui_packages = [
        "conda install -n SakeMonkey -c conda-forge tk -y",
        "conda install -n SakeMonkey -c conda-forge sqlite -y"
    ]
    
    for package_cmd in gui_packages:
        run_command(package_cmd, f"Installing GUI packages")
    
    print("✅ Conda environment setup completed!")
    return True

def setup_docker():
    """Setup Docker containerization"""
    print("=== Setting up Docker ===")
    
    # Check if Docker is available
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker not found. Please install Docker first.")
        return False
    
    # Create directories
    directories = ['data', 'credentials', 'logs', 'backups']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Build Docker image
    if not run_command("docker-compose build", "Building Docker image"):
        print("❌ Failed to build Docker image")
        return False
    
    print("✅ Docker setup completed!")
    return True

def main():
    """Main setup function"""
    parser = argparse.ArgumentParser(description='Setup SakeMonkey Recipe Database')
    parser.add_argument('--conda', action='store_true', help='Setup conda environment')
    parser.add_argument('--docker', action='store_true', help='Setup Docker containerization')
    parser.add_argument('--all', action='store_true', help='Setup both conda and Docker')
    
    args = parser.parse_args()
    
    if not any([args.conda, args.docker, args.all]):
        print("=== SakeMonkey Recipe Database - Development Setup ===")
        print("Choose setup option:")
        print("  python setup_dev.py --conda    - Setup conda environment")
        print("  python setup_dev.py --docker   - Setup Docker containerization")
        print("  python setup_dev.py --all      - Setup both")
        return
    
    success = True
    
    if args.conda or args.all:
        success &= setup_conda()
    
    if args.docker or args.all:
        success &= setup_docker()
    
    if success:
        print("\n🎉 Setup completed successfully!")
        print("\n📋 Next steps:")
        if args.conda or args.all:
            print("  conda activate SakeMonkey")
            print("  python gui_app.py")
        if args.docker or args.all:
            print("  docker-compose up")
    else:
        print("\n❌ Setup failed. Please check the error messages above.")

if __name__ == "__main__":
    main()
