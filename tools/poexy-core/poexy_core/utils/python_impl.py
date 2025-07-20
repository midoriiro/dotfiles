#!/usr/bin/env python3
"""
Python Implementation Detection Script

This script detects the current Python implementation and generates
the appropriate wheel tag according to PEP 425 standards.
"""

import platform
import sys
from typing import Optional


def get_python_implementation_tag() -> str:
    """
    Detect the Python implementation and return the appropriate tag.

    Returns:
        str: The implementation tag (py, cp, ip, pp, jy, etc.)
    """
    impl = sys.implementation

    # Standard implementation tags according to PEP 425
    impl_tags = {
        "cpython": "cp",
        "pypy": "pp",
        "ironpython": "ip",
        "jython": "jy",
        "micropython": "mp",
        "graalpython": "gp",
        "stackless": "sl",
    }

    # Get the implementation name
    impl_name = impl.name.lower()

    # Return the corresponding tag, default to 'py' for unknown implementations
    return impl_tags.get(impl_name, "py")


def get_python_version_info() -> tuple[int, int]:
    """
    Get the current Python version information.

    Returns:
        tuple[int, int]: (major, minor) version numbers
    """
    return sys.version_info.major, sys.version_info.minor


def get_abi_tag() -> str:
    """
    Get the ABI tag for the current Python implementation.

    Returns:
        str: The ABI tag
    """
    impl = sys.implementation

    # For CPython, use the version-specific ABI
    if impl.name.lower() == "cpython":
        major, minor = get_python_version_info()
        return f"cp{major}{minor}"

    # For other implementations, use 'none' as they typically don't have
    # version-specific ABIs in the same way
    return "none"


def get_platform_tag() -> str:
    """
    Get the platform tag for the current system.

    Returns:
        str: The platform tag
    """
    # Get the platform and normalize it
    platform_name = platform.system().lower()
    machine = platform.machine().lower()

    # Common platform mappings
    platform_mappings = {
        "linux": "linux",
        "darwin": "macosx",
        "windows": "win",
        "freebsd": "freebsd",
        "openbsd": "openbsd",
        "netbsd": "netbsd",
        "sunos": "sunos",
        "aix": "aix",
        "hp-ux": "hp-ux",
    }

    base_platform = platform_mappings.get(platform_name, platform_name)

    if base_platform == "linux":
        libc_version = platform.libc_ver()
        if libc_version is not None and libc_version[0] == "glibc":
            libc_version = libc_version[1]
            x, y = libc_version.split(".")
            base_platform = f"manylinux_{x}_{y}"
        else:
            raise ValueError(f"Unsupported libc version: {libc_version}")

    # Add architecture information
    arch_mappings = {
        "x86_64": "x86_64",
        "amd64": "x86_64",
        "i386": "i386",
        "i686": "i686",
        "aarch64": "aarch64",
        "arm64": "aarch64",
        "armv7l": "armv7l",
        "armv6l": "armv6l",
        "ppc64le": "ppc64le",
        "ppc64": "ppc64",
        "s390x": "s390x",
        "riscv64": "riscv64",
    }

    arch = arch_mappings.get(machine, machine)

    return f"{base_platform}_{arch}"


def generate_wheel_tag(
    impl: Optional[str] = None,
    major: Optional[int] = None,
    minor: Optional[int] = None,
    abi: Optional[str] = None,
    _platform: Optional[str] = None,
) -> str:
    """
    Generate a complete wheel tag.

    Args:
        impl: Implementation tag (py, cp, ip, pp, jy, etc.)
        major: Python major version
        minor: Python minor version
        abi: ABI tag
        platform: Platform tag

    Returns:
        str: Complete wheel tag in format: {python_tag}-{abi_tag}-{platform_tag}
    """
    # Use detected values if not provided
    if impl is None:
        impl = get_python_implementation_tag()

    if major is None:
        major = get_python_version_info()[0]

    if minor is None:
        minor = get_python_version_info()[1]

    if abi is None:
        abi = get_abi_tag()

    if _platform is None:
        _platform = get_platform_tag()

    # Generate the Python tag
    python_tag = f"{impl}{major}{minor}"

    # Format the complete tag
    return f"{python_tag}-{abi}-{_platform}"
