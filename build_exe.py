import os
import sys
import subprocess
import shutil
import time

def print_section(title):
    print(f"\n{'=' * 50}")
    print(f" {title}")
    print(f"{'=' * 50}")

def check_requirements():
    print_section("Checking Requirements")
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print(f"✓ PyInstaller {PyInstaller.__version__} is installed")
    except ImportError:
        print("✗ PyInstaller is not installed")
        print("Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("PyInstaller installed successfully")
    
    # Check if main script exists
    main_script = 'shamsi_calendar_widget.pyw'
    if os.path.exists(main_script):
        print(f"✓ Main script '{main_script}' found")
    else:
        print(f"✗ Main script '{main_script}' not found!")
        print(f"Please make sure '{main_script}' exists in the current directory.")
        return False
    
    return True

def build_executable():
    print_section("Building Executable")
    
    # Define the PyInstaller arguments
    args = [
        sys.executable,
        "-m", "PyInstaller",
        'shamsi_calendar_widget.pyw',  # Your main script
        '--name=ShamsiCalendar',       # Name of the output executable
        '--onefile',                   # Create a single file executable
        '--windowed',                  # Don't show the console window
        '--clean',                     # Clean PyInstaller cache
        '--noconfirm',                 # Replace output directory without asking
    ]
    
    # Check for additional data files and add them
    if os.path.exists('quotes.json'):
        print("✓ Found quotes.json, adding to executable")
        args.append('--add-data=quotes.json;.')
    
    if os.path.exists('icons'):
        print("✓ Found icons directory, adding to executable")
        args.append('--add-data=icons/*;icons/')
    
    # Run PyInstaller as a subprocess to capture output
    print("\nRunning PyInstaller (this may take a few minutes)...")
    process = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    
    # Print output in real-time with a simple progress indicator
    progress_chars = "|/-\\"
    progress_idx = 0
    
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            # Print progress indicator
            progress_char = progress_chars[progress_idx % len(progress_chars)]
            sys.stdout.write(f"\r[{progress_char}] Building...")
            sys.stdout.flush()
            progress_idx += 1
            
            # Print important messages
            if "ERROR" in output or "WARNING" in output:
                print(f"\n{output.strip()}")
    
    return_code = process.poll()
    
    if return_code == 0:
        print("\n\n✓ Build completed successfully!")
        return True
    else:
        print(f"\n\n✗ Build failed with return code {return_code}")
        return False

def create_zip():
    print_section("Creating ZIP File")
    
    exe_path = os.path.join('dist', 'ShamsiCalendar.exe')
    if not os.path.exists(exe_path):
        print(f"✗ Executable not found at {exe_path}")
        return False
    
    zip_path = os.path.join('dist', 'ShamsiCalendar.zip')
    
    print(f"Creating ZIP file: {zip_path}")
    try:
        import zipfile
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.write(exe_path, os.path.basename(exe_path))
            print(f"✓ Added {os.path.basename(exe_path)} to ZIP")
            
            # Add README if it exists
            if os.path.exists('README.md'):
                zipf.write('README.md', 'README.md')
                print("✓ Added README.md to ZIP")
        
        print(f"\n✓ ZIP file created successfully: {zip_path}")
        return True
    except Exception as e:
        print(f"✗ Failed to create ZIP file: {str(e)}")
        return False

def main():
    print_section("ShamsiCalendar Executable Builder")
    print("This script will build a standalone executable for ShamsiCalendar.")
    
    if not check_requirements():
        print("\n✗ Requirements check failed. Please fix the issues and try again.")
        return
    
    if build_executable():
        create_zip()
        
        print_section("Next Steps")
        print("1. The executable is in the 'dist' folder: dist/ShamsiCalendar.exe")
        print("2. A ZIP file has been created: dist/ShamsiCalendar.zip")
        print("3. To create a GitHub release:")
        print("   - Go to your GitHub repository")
        print("   - Click on 'Releases' > 'Create a new release'")
        print("   - Upload the ZIP file as a release asset")
        print("   - Add release notes explaining this is a standalone executable")

if __name__ == "__main__":
    main()
