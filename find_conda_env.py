"""
Helper script to find the SakeMonkey conda environment path
Run this to get the correct Python interpreter path for VS Code/Cursor settings
"""
import subprocess
import sys
import os

def find_conda_env_path(env_name="SakeMonkey"):
    """Find the path to a conda environment"""
    try:
        # Try to get conda info
        result = subprocess.run(
            ["conda", "info", "--envs"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse output to find environment path
        for line in result.stdout.split('\n'):
            if env_name in line:
                # Extract path (format: "SakeMonkey  *  /path/to/env")
                parts = line.split()
                for i, part in enumerate(parts):
                    if env_name in part and i + 2 < len(parts):
                        # Path is usually after the asterisk
                        if '*' in parts:
                            path_idx = parts.index('*') + 1
                            if path_idx < len(parts):
                                env_path = parts[path_idx]
                                python_exe = os.path.join(env_path, "python.exe")
                                if os.path.exists(python_exe):
                                    return python_exe
                                # Try without .exe for Unix
                                python_exe = os.path.join(env_path, "bin", "python")
                                if os.path.exists(python_exe):
                                    return python_exe
        
        # Alternative: try conda env list
        result = subprocess.run(
            ["conda", "env", "list"],
            capture_output=True,
            text=True,
            check=True
        )
        
        for line in result.stdout.split('\n'):
            if env_name in line and not line.strip().startswith('#'):
                parts = line.split()
                if len(parts) >= 2:
                    env_path = parts[-1]
                    python_exe = os.path.join(env_path, "python.exe")
                    if os.path.exists(python_exe):
                        return python_exe
                    python_exe = os.path.join(env_path, "bin", "python")
                    if os.path.exists(python_exe):
                        return python_exe
        
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # Fallback: try common conda locations
    common_paths = [
        os.path.expanduser("~/miniconda3/envs/SakeMonkey"),
        os.path.expanduser("~/anaconda3/envs/SakeMonkey"),
        "C:/Users/%USERNAME%/miniconda3/envs/SakeMonkey",
        "C:/Users/%USERNAME%/anaconda3/envs/SakeMonkey",
    ]
    
    for base_path in common_paths:
        python_exe = os.path.join(base_path, "python.exe")
        if os.path.exists(python_exe):
            return python_exe
        python_exe = os.path.join(base_path, "bin", "python")
        if os.path.exists(python_exe):
            return python_exe
    
    return None

if __name__ == "__main__":
    path = find_conda_env_path()
    if path:
        print(f"Found SakeMonkey conda environment at:")
        print(path)
        print(f"\nAdd this to your .vscode/settings.json:")
        print(f'  "python.defaultInterpreterPath": "{path}",')
    else:
        print("Could not find SakeMonkey conda environment.")
        print("Make sure:")
        print("1. The environment exists: conda env list")
        print("2. Conda is in your PATH")
        print("3. The environment name is exactly 'SakeMonkey'")
        sys.exit(1)

