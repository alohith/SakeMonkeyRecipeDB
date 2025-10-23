#!/usr/bin/env python3
"""
Setup script for SakeMonkey conda environment
"""

import subprocess
import sys
import os

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

def main():
    """Main setup function"""
    print("=== SakeMonkey Recipe Database - Conda Environment Setup ===")
    
    # Check if conda is available
    try:
        subprocess.run(["conda", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Conda not found. Please install Anaconda or Miniconda first.")
        return False
    
    # Create conda environment
    if not run_command("conda env create -f environment.yml", "Creating SakeMonkey conda environment"):
        print("❌ Failed to create conda environment")
        return False
    
    # Activate environment and install additional packages
    activate_cmd = "conda activate SakeMonkey"
    
    # Install additional packages if needed
    additional_packages = [
        "conda install -n SakeMonkey -c conda-forge tk -y",
        "conda install -n SakeMonkey -c conda-forge sqlite -y"
    ]
    
    for package_cmd in additional_packages:
        if not run_command(package_cmd, f"Installing {package_cmd.split()[-1]}"):
            print(f"⚠️  Warning: Failed to install {package_cmd.split()[-1]}")
    
    print("\n✅ Conda environment setup completed!")
    print("\nTo activate the environment, run:")
    print("  conda activate SakeMonkey")
    print("\nTo run the application:")
    print("  conda activate SakeMonkey")
    print("  python gui_app.py")
    
    return True

if __name__ == "__main__":
    main()
