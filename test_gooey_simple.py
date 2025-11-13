"""
Simple test to verify Gooey can create a GUI
"""
from gooey import Gooey, GooeyParser

@Gooey(program_name="SakeMonkey Test", program_description="Test Gooey GUI")
def main():
    parser = GooeyParser(description="Test Gooey Application")
    parser.add_argument('--test', type=str, help='Test argument', default='Hello Gooey!')
    args = parser.parse_args()
    print(f"Gooey is working! Test value: {args.test}")
    return args.test

if __name__ == "__main__":
    main()

