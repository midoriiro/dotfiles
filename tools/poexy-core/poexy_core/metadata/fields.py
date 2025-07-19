import textwrap
from enum import Enum
from typing import Optional

from poetry.core._vendor.packaging.version import Version


class MetadataVersions(Enum):
    V1_0 = Version("1.0")
    V1_1 = Version("1.1")
    V1_2 = Version("1.2")
    V2_1 = Version("2.1")
    V2_2 = Version("2.2")
    V2_3 = Version("2.3")
    V2_4 = Version("2.4")

    def __lt__(self, other: "MetadataVersions") -> bool:
        return self.value < other.value

    def __le__(self, other: "MetadataVersions") -> bool:
        return self.value <= other.value

    def __gt__(self, other: "MetadataVersions") -> bool:
        return self.value > other.value

    def __ge__(self, other: "MetadataVersions") -> bool:
        return self.value >= other.value

    def __eq__(self, other: "MetadataVersions") -> bool:
        return self.value == other.value

    def __ne__(self, other: "MetadataVersions") -> bool:
        return self.value != other.value

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"MetadataVersions.{self.value}"


class _MetadataField:
    def __init__(
        self,
        name: str,
        version: MetadataVersions,
        required: bool = False,
        multiuse: bool = False,
        multiline: bool = False,
        deprecated_since: Optional[MetadataVersions] = None,
    ):
        self.name = name
        self.version = version
        self.required = required
        self.multiuse = multiuse
        self.multiline = multiline
        self.deprecated_since = deprecated_since

    def format_value(self, value) -> str:
        if self.multiline and isinstance(value, str):
            # Indentation is not only for readability, but required
            # so that the line break is not treated as end of field.
            # The exact indentation does not matter,
            # but it is essential to also indent empty lines.
            from poexy_core.manifest.parser import MULTILINE_PREFIX

            prefix = MULTILINE_PREFIX
            lines = value.splitlines()
            if len(lines) == 1:
                return value
            lines_to_indent = lines[1:]
            value = "\n".join(lines_to_indent)
            value = textwrap.indent(value, prefix, lambda _: True)
            value = f"{lines[0].strip()}\n{value}"
        return value


class MetadataField(Enum):
    # Version 1.0
    MetadataVersion = _MetadataField(
        "Metadata-Version", MetadataVersions.V1_0, required=True
    )
    Name = _MetadataField("Name", MetadataVersions.V1_0, required=True)
    Version = _MetadataField("Version", MetadataVersions.V1_0, required=True)
    Platform = _MetadataField("Platform", MetadataVersions.V1_0, multiuse=True)
    Summary = _MetadataField("Summary", MetadataVersions.V1_0, required=True)
    Description = _MetadataField("Description", MetadataVersions.V1_0, multiline=True)
    Keywords = _MetadataField("Keywords", MetadataVersions.V1_0)
    Author = _MetadataField("Author", MetadataVersions.V1_0, multiline=True)
    AuthorEmail = _MetadataField("Author-email", MetadataVersions.V1_0)
    License = _MetadataField(
        "License",
        MetadataVersions.V1_0,
        multiline=True,
        deprecated_since=MetadataVersions.V2_4,
    )
    HomePage = _MetadataField(
        "Home-Page", MetadataVersions.V1_0, deprecated_since=MetadataVersions.V1_2
    )

    # Version 1.1
    SupportedPlatforms = _MetadataField(
        "Supported-Platforms", MetadataVersions.V1_1, multiuse=True
    )
    Classifier = _MetadataField("Classifier", MetadataVersions.V1_1, multiuse=True)
    DownloadURL = _MetadataField(
        "Download-URL", MetadataVersions.V1_1, deprecated_since=MetadataVersions.V1_2
    )
    Requires = _MetadataField(
        "Requires", MetadataVersions.V1_1, deprecated_since=MetadataVersions.V1_2
    )
    Provides = _MetadataField(
        "Provides", MetadataVersions.V1_1, deprecated_since=MetadataVersions.V1_2
    )
    Obsoletes = _MetadataField(
        "Obsoletes", MetadataVersions.V1_1, deprecated_since=MetadataVersions.V1_2
    )

    # Version 1.2
    Maintainer = _MetadataField("Maintainer", MetadataVersions.V1_2, multiline=True)
    MaintainerEmail = _MetadataField("Maintainer-email", MetadataVersions.V1_2)
    RequiresDist = _MetadataField("Requires-Dist", MetadataVersions.V1_2, multiuse=True)
    RequiresPython = _MetadataField("Requires-Python", MetadataVersions.V1_2)
    RequiresExternal = _MetadataField(
        "Requires-External", MetadataVersions.V1_2, multiuse=True
    )
    ProjectURL = _MetadataField("Project-URL", MetadataVersions.V1_2, multiuse=True)
    ObsoletesDist = _MetadataField(
        "Obsoletes-Dist", MetadataVersions.V1_2, multiuse=True
    )

    # Version 2.1
    DescriptionContentType = _MetadataField(
        "Description-Content-Type", MetadataVersions.V2_1
    )
    ProvidesExtra = _MetadataField(
        "Provides-Extra", MetadataVersions.V2_1, multiuse=True
    )
    ProvidesDist = _MetadataField("Provides-Dist", MetadataVersions.V2_1, multiuse=True)

    # Version 2.2
    Dynamic = _MetadataField("Dynamic", MetadataVersions.V2_2, multiuse=True)

    # Version 2.4
    LicenseExpression = _MetadataField(
        "License-Expression", MetadataVersions.V2_4, multiuse=True
    )
    LicenseFile = _MetadataField("License-File", MetadataVersions.V2_4, multiuse=True)

    @property
    def name(self) -> str:
        return self.value.name

    @property
    def version(self) -> MetadataVersions:
        return self.value.version

    @property
    def required(self) -> bool:
        return self.value.required

    @property
    def multiuse(self) -> bool:
        return self.value.multiuse

    @property
    def multiline(self) -> bool:
        return self.value.multiline

    @property
    def deprecated_since(self) -> Optional[MetadataVersions]:
        return self.value.deprecated_since

    def format_value(self, value) -> str:
        return self.value.format_value(value)
