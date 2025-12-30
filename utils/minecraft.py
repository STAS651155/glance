"""
Minecraft directory detection and launcher utilities.
"""

import os
import glob
import subprocess
import uuid
import hashlib
import re

import minecraft_launcher_lib

from utils.platform_utils import get_platform, get_java_executable


def is_fabric_version(version: str) -> tuple[bool, str | None]:
    """Check if version is Fabric and extract vanilla version.

    Returns:
        (is_fabric, vanilla_version)
    """
    if "fabric" not in version.lower():
        return False, None

    patterns = [
        r"fabric-loader-[\d.]+-([\d.]+)",  # fabric-loader-0.16.14-1.21
        r"([\d.]+)-fabric",  # 1.21-fabric
        r"fabric-([\d.]+)",  # fabric-1.21
    ]

    for pattern in patterns:
        match = re.search(pattern, version)
        if match:
            return True, match.group(1)

    return True, None


def find_minecraft_directory():
    """Find the Minecraft installation directory."""
    current_os = get_platform()
    possible_paths = []

    if current_os == "windows":
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            possible_paths.append(os.path.join(appdata, ".minecraft"))
        userprofile = os.environ.get("USERPROFILE", "")
        if userprofile:
            possible_paths.append(os.path.join(userprofile, ".minecraft"))
            possible_paths.append(
                os.path.join(userprofile, "AppData", "Roaming", ".minecraft")
            )

    elif current_os == "macos":
        home = os.path.expanduser("~")
        possible_paths.extend(
            [
                os.path.join(home, "Library", "Application Support", "minecraft"),
                os.path.join(home, ".minecraft"),
            ]
        )

    elif current_os == "linux":
        home = os.path.expanduser("~")
        possible_paths.extend(
            [
                os.path.join(home, ".minecraft"),
                os.path.join(home, ".local", "share", "minecraft"),
                os.path.join(home, ".var", "app", "com.mojang.Minecraft", ".minecraft"),
            ]
        )

    for path in possible_paths:
        if os.path.exists(path) and os.path.isdir(path):
            return path

    return None


def get_minecraft_versions(minecraft_dir):
    """Get a list of installed Minecraft versions."""
    versions_dir = os.path.join(minecraft_dir, "versions")
    if not os.path.exists(versions_dir):
        return []

    valid_versions = []

    try:
        for item in os.listdir(versions_dir):
            version_path = os.path.join(versions_dir, item)
            if os.path.isdir(version_path):
                json_files = glob.glob(os.path.join(version_path, "*.json"))
                if json_files:
                    valid_versions.append(item)
    except Exception:
        pass

    return sorted(valid_versions, reverse=True)


def launch_minecraft(java_home, minecraft_dir, version, username="Player"):
    """Launch Minecraft with proxy configuration."""
    java_exe = get_java_executable(java_home)

    try:
        is_fabric, vanilla_version = is_fabric_version(version)
        if is_fabric:
            print(f"\n[>] Launching Fabric version: {version}")

            version_json_path = os.path.join(
                minecraft_dir, "versions", version, f"{version}.json"
            )
            if os.path.exists(version_json_path):
                import json

                with open(version_json_path, "r", encoding="utf-8") as f:
                    fabric_data = json.load(f)

                vanilla_jar_version = fabric_data.get("jar")
                if vanilla_jar_version:
                    vanilla_jar_path = os.path.join(
                        minecraft_dir,
                        "versions",
                        vanilla_jar_version,
                        f"{vanilla_jar_version}.jar",
                    )

                    if not os.path.exists(vanilla_jar_path):
                        print(f"    [!] Missing vanilla jar: {vanilla_jar_version}")
                        print(
                            f"    [>] Installing vanilla Minecraft {vanilla_jar_version}..."
                        )

                        try:
                            minecraft_launcher_lib.install.install_minecraft_version(
                                vanilla_jar_version, minecraft_dir
                            )
                            print(f"    [✓] Vanilla {vanilla_jar_version} installed")
                        except Exception as e:
                            print(f"    [!] Failed to install vanilla version: {e}")
                            print(
                                f"    [!] Please install vanilla {vanilla_jar_version} manually first!"
                            )
                            return None

        player_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, f"OfflinePlayer:{username}"))
        access_token = hashlib.md5(f"{username}{player_uuid}".encode()).hexdigest()

        jvm_args = [
            "-Dhttp.proxyHost=127.0.0.1",
            "-Dhttp.proxyPort=8080",
            "-Dhttps.proxyHost=127.0.0.1",
            "-Dhttps.proxyPort=8080",
            "-XX:+UnlockExperimentalVMOptions",
            "-XX:+UseG1GC",
            "-XX:G1NewSizePercent=20",
            "-XX:G1ReservePercent=20",
            "-XX:MaxGCPauseMillis=50",
            "-XX:G1HeapRegionSize=32M",
            "-Dfile.encoding=UTF-8",
        ]

        options = {
            "username": username,
            "uuid": player_uuid,
            "token": access_token,
            "executablePath": java_exe,
            "jvmArguments": jvm_args,
        }

        command = minecraft_launcher_lib.command.get_minecraft_command(
            version=version, minecraft_directory=minecraft_dir, options=options
        )

        print(f"\n[>] Launching Minecraft {version}...")
        print(f"    Java: {java_exe}")
        print("    Proxy: 127.0.0.1:8080")
        print()

        return subprocess.Popen(
            command,
            cwd=minecraft_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    except ImportError:
        print("[!] minecraft_launcher_lib not installed")
        print("    Install: pip install minecraft-launcher-lib")
        print("    Or launch Minecraft manually through launcher with proxy")
        return None
