import subprocess
import sys
import os
import pkg_resources

def check_missing_packages():
    if not os.path.exists("requirements.txt"):
        return []
    
    with open("requirements.txt", "r") as f:
        requirements = f.read().splitlines()
    
    missing = []
    installed_packages = {pkg.key for pkg in pkg_resources.working_set}
    
    for requirement in requirements:
        requirement = requirement.strip()
        if not requirement or requirement.startswith("#"):
            continue
        
        # Extract package name (handle == and >= operators)
        package_name = requirement.split("==")[0].split(">=")[0].split("<=")[0].strip().lower()
        
        if package_name not in installed_packages:
            missing.append(requirement)
    
    return missing

def install_requirements():
    missing_packages = check_missing_packages()
    
    if not missing_packages:
        print("✓ All required packages are already installed!")
        return True
    
    print(f"Installing {len(missing_packages)} missing package(s)...")
    try:
        # Install only missing packages
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            *missing_packages,
            "--prefer-binary",
            "--no-warn-script-location"
        ])
        print("\n✓ All packages installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Error installing packages: {e}")
        return False

if __name__ == "__main__":
    # Install requirements first
    install_requirements()
    
    print("\nStarting application...")
    # Import and launch LoginMain
    from PyQt5.QtWidgets import QApplication
    from LoginMain import LogIn
    
    app = QApplication(sys.argv)
    login_window = LogIn()
    login_window.show()
    sys.exit(app.exec_())
