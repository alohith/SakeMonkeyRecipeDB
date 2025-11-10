#!/usr/bin/env python3
"""
Setup script for Docker containerization of SakeMonkey Recipe Database
"""

import subprocess
import sys
import os
import shutil

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

def create_directories():
    """Create necessary directories"""
    directories = ['data', 'credentials', 'logs', 'backups']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def main():
    """Main Docker setup function"""
    print("=== SakeMonkey Recipe Database - Docker Setup ===")
    
    # Check if Docker is available
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker not found. Please install Docker first.")
        return False
    
    # Check if Docker Compose is available
    try:
        subprocess.run(["docker-compose", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker Compose not found. Please install Docker Compose first.")
        return False
    
    # Create necessary directories
    print("\n📁 Creating directories...")
    create_directories()
    
    # Build Docker image
    if not run_command("docker-compose build", "Building Docker image"):
        print("❌ Failed to build Docker image")
        return False
    
    # Initialize database if it doesn't exist
    if not os.path.exists("data/sake_recipe_db.sqlite"):
        print("\n🗄️  Initializing database...")
        if not run_command("docker-compose run --rm sakemonkey-db python setup_database.py", "Setting up database"):
            print("❌ Failed to initialize database")
            return False
        
        # Import Excel data if available
        if os.path.exists("../../SakeRecipeDataBase.xlsx"):
            print("📊 Importing Excel data...")
            if not run_command("docker-compose run --rm sakemonkey-db python import_excel_data.py", "Importing Excel data"):
                print("⚠️  Warning: Failed to import Excel data")
    
    print("\n✅ Docker setup completed!")
    print("\n🐳 Available commands:")
    print("  docker-compose up                    - Start the application")
    print("  docker-compose up -d                 - Start in background")
    print("  docker-compose down                  - Stop the application")
    print("  docker-compose run --rm sakemonkey-db python gui_app.py  - Run GUI")
    print("  docker-compose run --rm sakemonkey-db python database_interface.py  - Run CLI")
    print("  docker-compose run --rm backup      - Create backup")
    
    print("\n📁 Data persistence:")
    print("  - Database: ./data/")
    print("  - Credentials: ./credentials/")
    print("  - Logs: ./logs/")
    print("  - Backups: ./backups/")
    
    return True

if __name__ == "__main__":
    main()



