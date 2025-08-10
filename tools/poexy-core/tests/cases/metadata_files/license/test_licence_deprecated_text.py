"""
Test case: Deprecated license text field usage

This test verifies that poexy-core correctly handles and rejects the deprecated
"license" text field in project metadata. The old license field has been
deprecated in favor of license-expression and license-files fields.

Test scenario:
- A project uses the deprecated "license" field in metadata
- The deprecated field contains license text directly in metadata
- The build system attempts to process the deprecated license specification
- Appropriate deprecation errors should be raised for the obsolete field

Expected behavior:
- Deprecated license field usage is detected and rejected
- Error messages clearly identify the deprecated field and suggest alternatives
- Build fails early with guidance toward modern license specification methods
- Deprecation handling is consistent across wheel and sdist formats

Edge case significance:
This tests backward compatibility and deprecation handling which is important
for guiding users toward modern packaging standards. Proper deprecation
warnings help maintain ecosystem evolution while providing clear migration paths.
"""

import pytest

from tests.conftests.paths import SamplePaths

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(SamplePaths.MetadataFilesLicence / "license-deprecated-text")


def test_wheel(project, project_path, assert_wheel_build):
    with project(project_path):
        with pytest.raises(ValueError, match="Field License is deprecated since 2.4"):
            assert_wheel_build(project_path)


def test_sdist(project, project_path, assert_sdist_build):
    with project(project_path):
        with pytest.raises(ValueError, match="Field License is deprecated since 2.4"):
            assert_sdist_build(project_path)
