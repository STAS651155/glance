"""
Platform detection and Java installation utilities.
Handles cross-platform support for Windows, macOS, and Linux.
"""

import os
import re
import subprocess
import platform
from pathlib import Path


def get_platform():
    """Detect the current operating system."""
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    elif system == "darwin":
        return "macos"
    elif system == "linux":
        return "linux"
    return "unknown"


def find_java_installations():
    """Find all Java installations on the system."""
    java_paths = []
    current_os = get_platform()

    try:
        if current_os == "windows":
            result = subprocess.run(
                ["where", "java"], capture_output=True, text=True, timeout=10
            )
        else:
            result = subprocess.run(
                ["which", "-a", "java"], capture_output=True, text=True, timeout=10
            )

        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                line = line.strip()
                if line and os.path.exists(line):
                    java_home = get_java_home_from_executable(line)
                    if java_home and java_home not in java_paths:
                        java_paths.append(java_home)
    except Exception:
        pass

    standard_paths = _get_standard_java_paths(current_os)

    for base_path in standard_paths:
        if os.path.exists(base_path):
            try:
                for item in os.listdir(base_path):
                    full_path = os.path.join(base_path, item)
                    if os.path.isdir(full_path):
                        if is_valid_java_home(full_path):
                            if full_path not in java_paths:
                                java_paths.append(full_path)
                        contents_home = os.path.join(full_path, "Contents", "Home")
                        if os.path.exists(contents_home) and is_valid_java_home(
                            contents_home
                        ):
                            if contents_home not in java_paths:
                                java_paths.append(contents_home)
            except PermissionError:
                pass

    java_home_env = os.environ.get("JAVA_HOME")
    if (
        java_home_env
        and os.path.exists(java_home_env)
        and is_valid_java_home(java_home_env)
    ):
        if java_home_env not in java_paths:
            java_paths.insert(0, java_home_env)

    return java_paths


def _get_standard_java_paths(current_os):
    """Get standard Java installation paths for the current OS."""
    standard_paths = []

    if current_os == "windows":
        program_files = [
            os.environ.get("ProgramFiles", "C:\\Program Files"),
            os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
            os.environ.get("LOCALAPPDATA", ""),
        ]
        for pf in program_files:
            if pf:
                standard_paths.extend(
                    [
                        os.path.join(pf, "Java"),
                        os.path.join(pf, "Eclipse Adoptium"),
                        os.path.join(pf, "AdoptOpenJDK"),
                        os.path.join(pf, "Zulu"),
                        os.path.join(pf, "Amazon Corretto"),
                        os.path.join(pf, "Microsoft"),
                        os.path.join(pf, "BellSoft"),
                        os.path.join(pf, "Semeru"),
                    ]
                )

    elif current_os == "macos":
        standard_paths.extend(
            [
                "/Library/Java/JavaVirtualMachines",
                "/System/Library/Java/JavaVirtualMachines",
                os.path.expanduser("~/Library/Java/JavaVirtualMachines"),
                "/opt/homebrew/opt/openjdk",
                "/opt/homebrew/Cellar/openjdk",
                "/usr/local/opt/openjdk",
                "/usr/local/Cellar/openjdk",
            ]
        )

    elif current_os == "linux":
        standard_paths.extend(
            [
                "/usr/lib/jvm",
                "/usr/java",
                "/opt/java",
                "/opt/jdk",
                os.path.expanduser("~/.sdkman/candidates/java"),
                os.path.expanduser("~/.jdks"),
                "/usr/local/java",
            ]
        )

    return standard_paths


def get_java_home_from_executable(java_exe_path):
    """Extract JAVA_HOME from a java executable path."""
    try:
        java_path = Path(java_exe_path).resolve()
        if java_path.parent.name == "bin":
            java_home = java_path.parent.parent
            if is_valid_java_home(str(java_home)):
                return str(java_home)
    except Exception:
        pass
    return None


def is_valid_java_home(path):
    """Check if a path is a valid JAVA_HOME directory."""
    current_os = get_platform()
    if current_os == "windows":
        java_exe = os.path.join(path, "bin", "java.exe")
        keytool_exe = os.path.join(path, "bin", "keytool.exe")
    else:
        java_exe = os.path.join(path, "bin", "java")
        keytool_exe = os.path.join(path, "bin", "keytool")

    return os.path.exists(java_exe) and os.path.exists(keytool_exe)


def get_java_version(java_home):
    """Get the version string of a Java installation."""
    current_os = get_platform()
    java_exe = os.path.join(
        java_home, "bin", "java.exe" if current_os == "windows" else "java"
    )

    try:
        result = subprocess.run(
            [java_exe, "-version"], capture_output=True, text=True, timeout=10
        )
        output = result.stderr + result.stdout
        for line in output.split("\n"):
            if "version" in line.lower():
                match = re.search(r'"([^"]+)"', line)
                if match:
                    return match.group(1)
                return line.strip()
    except Exception:
        pass
    return "unknown"


def get_java_executable(java_home):
    """Get the path to the java executable."""
    current_os = get_platform()
    return os.path.join(
        java_home, "bin", "java.exe" if current_os == "windows" else "java"
    )


def get_keytool_executable(java_home):
    """Get the path to the keytool executable."""
    current_os = get_platform()
    return os.path.join(
        java_home, "bin", "keytool.exe" if current_os == "windows" else "keytool"
    )
