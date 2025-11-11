"""
Setup script to initialize the SakeMonkey environment and database
"""
import subprocess
import sys
import os


def create_conda_environment():
    """Create conda environment from environment.yml"""
    env_file = os.path.join(os.path.dirname(__file__), "environment.yml")
    print("Creating conda environment from environment.yml...")
    try:
        subprocess.run(
            ["conda", "env", "create", "-f", env_file],
            check=True
        )
        print("Conda environment created successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error creating conda environment: {e}")
        return False
    except FileNotFoundError:
        print("Conda not found. Please install Miniconda or Anaconda first.")
        return False


def init_database():
    """Initialize the database"""
    from database import init_database
    print("Initializing database...")
    init_database()
    print("Database initialized!")


if __name__ == "__main__":
    print("SakeMonkey Setup")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--skip-env":
        print("Skipping conda environment creation...")
    else:
        if not create_conda_environment():
            print("\nTo create the environment manually, run:")
            print("  conda env create -f environment.yml")
            print("  conda activate SakeMonkey")
    
    init_database()
    
    print("\nSetup complete!")
    print("\nTo activate the environment, run:")
    print("  conda activate SakeMonkey")
    print("\nTo run the GUI application:")
    print("  python gui_app.py")




