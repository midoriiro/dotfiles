from enum import Enum


class PackageFormat(str, Enum):
    Source = "source"
    Wheel = "wheel"
    Binary = "binary"


DEFAULT_FORMATS = [PackageFormat.Source, PackageFormat.Wheel, PackageFormat.Binary]


class WheelFormat(str, Enum):
    Source = "source"
    Binary = "binary"


DEFAULT_WHEEL_FORMATS = [WheelFormat.Source]
