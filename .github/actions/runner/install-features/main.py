import os
import subprocess
from typing import List, Union

runner_commands = {
    "linux": {
        "update": "sudo apt update",
        "install": "sudo apt install -y",
    },
    "macos": {"update": "brew update", "install": "brew install"},
    "windows": {"update": None, "install": "choco install"},
}

features_info = {
    "git-daemon": {
        "cmd": "git daemon -h",
        "linux": "git-daemon-run",
        "macos": "git",
        "windows": "git",
    }
}


def run_command(cmd: Union[str, List[str]]) -> subprocess.CompletedProcess:
    if isinstance(cmd, str):
        run_cmd = [part.strip() for part in cmd.split(" ")]
    else:
        run_cmd = cmd

    return subprocess.run(run_cmd, shell=True, text=True, capture_output=True)


def is_feature_installed(feature_cmd: str):
    process = run_command(feature_cmd)
    return process.returncode == 0


def install_feature(feature: str, runner_os: str):
    if feature not in features_info:
        print(f"Feature {feature} not found")
        exit(1)

    feature_info = features_info[feature]

    if is_feature_installed(feature_info["cmd"]):
        print(f"Feature {feature} is already installed")
        return

    if runner_os == "Linux":
        runner_command = runner_commands["linux"]
        package_name = feature_info["linux"]
    elif runner_os == "macOS":
        runner_command = runner_commands["macos"]
        package_name = feature_info["macos"]
    elif runner_os == "Windows":
        runner_command = runner_commands["windows"]
        package_name = feature_info["windows"]
    else:
        print(f"Unsupported OS: {runner_os}")
        exit(1)

    if runner_command["update"] is not None:
        run_command(runner_command["update"])

    install_command = f"{runner_command['install']} {package_name}"

    run_command(install_command)


features_to_install = os.getenv("FEATURES_TO_INSTALL", None)

if features_to_install is None:
    print("No features to install")
    exit(0)

features_to_install = [feature.strip() for feature in features_to_install.split(",")]

if len(features_to_install) == 0:
    print("No features to install")
    exit(0)

runner_os = os.getenv("RUNNER_OS", None)

if runner_os is None:
    print("RUNNER_OS is not set")
    exit(1)

for feature in features_to_install:
    print(f"Installing {feature}")
    install_feature(feature, runner_os)
