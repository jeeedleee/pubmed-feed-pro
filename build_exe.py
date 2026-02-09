#!/usr/bin/env python3
"""
Build script for PubMed Papers Feed - Windows EXE
Usage: python build_exe.py
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def clean_build():
    """Clean previous build artifacts."""
    dirs_to_remove = ['build', 'dist', '__pycache__']
    files_to_remove = ['*.spec']
    
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            print(f"Removing {dir_name}/...")
            shutil.rmtree(dir_name, ignore_errors=True)
    
    for pattern in files_to_remove:
        for f in Path('.').glob(pattern):
            print(f"Removing {f}...")
            f.unlink(missing_ok=True)


def build_exe():
    """Build executable using PyInstaller."""
    
    # Ensure data directories exist
    os.makedirs('data/reports', exist_ok=True)
    
    # PyInstaller command
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--name=PubMedPapersFeed',
        '--onefile',
        '--windowed',
        '--add-data=web/templates;web/templates',
        '--add-data=web/static;web/static',
        '--add-data=data;data',
        '--add-data=config.yaml.example;.',
        '--icon=NONE',
        '--clean',
        '--noconfirm',
        'main.py'
    ]
    
    print("Building executable...")
    print(f"Command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=False, text=True)
    
    if result.returncode != 0:
        print("Build failed!")
        return False
    
    print("Build successful!")
    return True


def create_launcher():
    """Create a launcher script."""
    launcher_content = '''@echo off
echo Starting PubMed Papers Feed...
echo.
echo Please wait...
echo.

set APP_DIR=%~dp0
set DATA_DIR=%USERPROFILE%\\.pubmed_papers_feed

:: Create data directory in user profile
if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"
if not exist "%DATA_DIR%\data" mkdir "%DATA_DIR%\data"
if not exist "%DATA_DIR%\data\reports" mkdir "%DATA_DIR%\data\reports"

:: Copy config if not exists
if not exist "%DATA_DIR%\config.yaml" (
    copy "%APP_DIR%\config.yaml.example" "%DATA_DIR%\config.yaml"
    echo Created default config at %DATA_DIR%\config.yaml
    echo Please edit it with your API key before using.
    echo.
    pause
)

:: Run the app
cd /d "%DATA_DIR%"
start http://localhost:8000
"%APP_DIR%\PubMedPapersFeed.exe"
'''
    
    with open('dist/start.bat', 'w', encoding='utf-8') as f:
        f.write(launcher_content)
    
    print("Created launcher: dist/start.bat")


def main():
    """Main build process."""
    print("=" * 60)
    print("PubMed Papers Feed - EXE Builder")
    print("=" * 60)
    print()
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print("[OK] PyInstaller is installed")
    except ImportError:
        print("[ERROR] PyInstaller not found. Installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
    
    print()
    print("Step 1: Cleaning previous builds...")
    clean_build()
    
    print()
    print("Step 2: Building executable...")
    if not build_exe():
        print("Build failed!")
        sys.exit(1)
    
    print()
    print("Step 3: Creating launcher...")
    create_launcher()
    
    # Copy necessary files to dist
    print()
    print("Step 4: Copying additional files...")
    shutil.copy('config.yaml.example', 'dist/config.yaml.example')
    shutil.copy('README.md', 'dist/README.md')
    
    print()
    print("=" * 60)
    print("Build complete!")
    print("=" * 60)
    print()
    print("Output location: dist/")
    print("- PubMedPapersFeed.exe  (主程序)")
    print("- start.bat             (启动脚本)")
    print("- config.yaml.example   (配置模板)")
    print()
    print("Usage:")
    print("  1. 复制 dist/ 文件夹给对方")
    print("  2. 运行 start.bat 启动")
    print("  3. 首次运行需配置 API Key")
    print()


if __name__ == '__main__':
    main()
