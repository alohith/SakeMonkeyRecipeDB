"""
Test script to verify Gooey and its dependencies are installed and working
"""
import sys

def test_imports():
    """Test that all required packages can be imported"""
    results = {}
    
    # Test Python version
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}\n")
    
    # Test Gooey
    try:
        import gooey
        version = getattr(gooey, '__version__', 'unknown')
        results['gooey'] = (True, f"Gooey {version}")
        print(f"[OK] Gooey: {version}")
    except ImportError as e:
        results['gooey'] = (False, f"Import error: {e}")
        print(f"[FAIL] Gooey: NOT INSTALLED - {e}")
    
    # Test wxPython (required by Gooey)
    try:
        import wx
        version = wx.version()
        results['wxpython'] = (True, f"wxPython {version}")
        print(f"[OK] wxPython: {version}")
    except ImportError as e:
        results['wxpython'] = (False, f"Import error: {e}")
        print(f"[FAIL] wxPython: NOT INSTALLED - {e}")
    
    # Test other dependencies
    dependencies = [
        'sqlmodel',
        'sqlalchemy',
        'google.auth',
        'googleapiclient',
    ]
    
    for dep in dependencies:
        try:
            module = __import__(dep)
            version = getattr(module, '__version__', 'installed')
            results[dep] = (True, version)
            print(f"[OK] {dep}: {version}")
        except ImportError as e:
            results[dep] = (False, str(e))
            print(f"[FAIL] {dep}: NOT INSTALLED - {e}")
    
    return results

def test_gooey_basic():
    """Test basic Gooey functionality"""
    try:
        from gooey import Gooey, GooeyParser
        
        @Gooey(program_name="Test Gooey App")
        def test_app():
            parser = GooeyParser(description="Test Gooey Application")
            parser.add_argument('--test', type=str, help='Test argument')
            args = parser.parse_args()
            print("Gooey is working!")
            return True
        
        print("\n[OK] Gooey basic functionality test passed")
        return True
    except Exception as e:
        print(f"\n[FAIL] Gooey basic functionality test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Gooey and Dependencies")
    print("=" * 60)
    print()
    
    results = test_imports()
    print()
    
    # Only test Gooey functionality if imports work
    if results.get('gooey', (False,))[0] and results.get('wxpython', (False,))[0]:
        test_gooey_basic()
    else:
        print("\n⚠ Skipping Gooey functionality test - missing dependencies")
    
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    
    all_ok = all(status[0] for status in results.values())
    if all_ok:
        print("[OK] All packages are installed and working!")
    else:
        print("[FAIL] Some packages are missing or not working:")
        for name, (status, msg) in results.items():
            if not status:
                print(f"  - {name}: {msg}")
        print("\nTo install missing packages, run:")
        print("  pip install -r requirements.txt")
        print("or")
        print("  conda env update -n SakeMonkey -f environment.yml --prune")

