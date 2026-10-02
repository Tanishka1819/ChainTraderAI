import os
import subprocess
import sys

def install_requirements():
    """Install required packages"""
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("✓ Packages installed successfully!")

def create_directories():
    """Create necessary directories"""
    directories = [
        'models',
        'data', 
        'static/css',
        'static/js',
        'templates'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Created directory: {directory}")

def create_init_files():
    """Create __init__.py files for Python packages"""
    init_files = [
        'models/__init__.py',
        'data/__init__.py'
    ]
    
    for init_file in init_files:
        with open(init_file, 'w') as f:
            f.write('# Package initialization\n')
        print(f"✓ Created: {init_file}")

def main():
    print("🚀 Setting up ChainTraderAI...")
    print("=" * 50)
    
    try:
        create_directories()
        create_init_files()
        install_requirements()
        
        print("\n" + "=" * 50)
        print("✅ Setup completed successfully!")
        print("\nTo run the application:")
        print("1. python app.py")
        print("2. Open http://127.0.0.1:5000 in your browser")
        print("\nDemo Flow:")
        print("1. Click 'Train AI Model' (wait for completion)")
        print("2. Click 'Predict & Trade' to make predictions")
        print("3. View transactions in the blockchain ledger")
        print("4. Start auto trading for continuous operation")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()