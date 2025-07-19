from poetry.core.masonry.metadata import Metadata as PoetryMetadata

from poexy_core.manifest.manifest import Manifest, ManifestValue
from poexy_core.metadata.fields import MetadataField, MetadataVersions


class MetadataManifestBuilder:
    def __init__(self, manifest: Manifest, version: MetadataVersions):
        self.__manifest = manifest
        self.__version = version
        self.__manifest.set(MetadataField.MetadataVersion.name, str(version))

    def get(self, field: MetadataField) -> ManifestValue:
        return self.__manifest.get(field)

    def set(self, field: MetadataField, value: ManifestValue):
        if field.version > self.__version:
            raise ValueError(
                f"Field {field.name} is not supported in version {self.__version}"
            )
        if field.deprecated_since and field.deprecated_since <= self.__version:
            raise ValueError(
                f"Field {field.name} is deprecated since {field.deprecated_since}"
            )
        self.__manifest.set(field.name, field.format_value(value))

    def delete(self, field: MetadataField):
        self.__manifest.delete(field)

    def validate(self):
        required_fields = [field for field in MetadataField if field.required]
        for field in required_fields:
            if not self.__manifest.get(field.name):
                raise ValueError(f"Field {field.name} is required")

    @staticmethod
    def from_poetry(builder: "MetadataManifestBuilder", metadata: PoetryMetadata):
        if metadata.name is None:
            raise ValueError("Metadata.name is required")
        builder.set(MetadataField.Name, metadata.name)
        builder.set(MetadataField.Version, metadata.version)

        # 1.0
        if metadata.platforms:
            builder.set(MetadataField.Platform, metadata.platforms)

        if metadata.supported_platforms:
            builder.set(MetadataField.SupportedPlatforms, metadata.supported_platforms)

        if metadata.summary:
            builder.set(MetadataField.Summary, metadata.summary)

        if metadata.description:
            builder.set(MetadataField.Description, metadata.description)

        if metadata.keywords:
            builder.set(MetadataField.Keywords, metadata.keywords)

        if metadata.home_page:
            builder.set(MetadataField.HomePage, metadata.home_page)

        if metadata.download_url:
            builder.set(MetadataField.DownloadURL, metadata.download_url)

        if metadata.author:
            builder.set(MetadataField.Author, metadata.author)

        if metadata.author_email:
            builder.set(MetadataField.AuthorEmail, metadata.author_email)

        if metadata.license:
            builder.set(MetadataField.License, metadata.license)
        elif hasattr(metadata, "license_expression"):
            builder.set(
                MetadataField.LicenseExpression, getattr(metadata, "license_expression")
            )
        elif hasattr(metadata, "license_files"):
            builder.set(MetadataField.LicenseFile, getattr(metadata, "license_files"))

        # 1.1
        if metadata.classifiers:
            builder.set(MetadataField.Classifier, metadata.classifiers)

        if metadata.requires:
            builder.set(MetadataField.Requires, metadata.requires)

        if metadata.provides:
            builder.set(MetadataField.Provides, metadata.provides)

        if metadata.obsoletes:
            builder.set(MetadataField.Obsoletes, metadata.obsoletes)

        # 1.2
        if metadata.maintainer:
            builder.set(MetadataField.Maintainer, metadata.maintainer)

        if metadata.maintainer_email:
            builder.set(MetadataField.MaintainerEmail, metadata.maintainer_email)

        if metadata.requires_python:
            builder.set(MetadataField.RequiresPython, metadata.requires_python)

        if metadata.requires_external:
            builder.set(MetadataField.RequiresExternal, metadata.requires_external)

        if metadata.requires_dist:
            builder.set(MetadataField.RequiresDist, sorted(metadata.requires_dist))

        if metadata.provides_dist:
            builder.set(MetadataField.ProvidesDist, metadata.provides_dist)

        if metadata.obsoletes_dist:
            builder.set(MetadataField.ObsoletesDist, metadata.obsoletes_dist)

        if metadata.project_urls:
            builder.set(
                MetadataField.ProjectURL,
                sorted(metadata.project_urls, key=lambda u: u[0]),
            )

        # 2.1
        if metadata.description_content_type:
            builder.set(
                MetadataField.DescriptionContentType, metadata.description_content_type
            )

        if metadata.provides_extra:
            builder.set(MetadataField.ProvidesExtra, sorted(metadata.provides_extra))
