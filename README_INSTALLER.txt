Ghost installer
===============
Fast way (no build needed):
  1. Install Python 3.10+ from python.org.
  2. Double-click ghost_installer.py (or run: python ghost_installer.py).

Make a real .exe (Windows):
  Double-click build_exe.bat. It installs PyInstaller and creates dist\GhostInstaller.exe,
  which has the mod built in. Send that single .exe to anyone.

What the installer does:
  - finds your .minecraft folder
  - "Install Fabric" downloads and runs the Fabric installer for Minecraft 26.2 (needs Java 25)
  - "Install" copies ghost-26.2.jar into mods and downloads Fabric API
  - "Uninstall" removes the Ghost jar
Online updates: put the URL of the newest jar in update_url.txt next to the exe (see ghost_installer.py).
