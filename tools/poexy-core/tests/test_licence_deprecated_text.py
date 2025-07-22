import pytest

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project("license-deprecated-text")


def test_wheel(project, project_path, assert_wheel_build):
    with project(project_path):
        with pytest.raises(ValueError, match="Field License is deprecated since 2.4"):
            assert_wheel_build(project_path)


def test_sdist(project, project_path, assert_sdist_build):
    with project(project_path):
        with pytest.raises(ValueError, match="Field License is deprecated since 2.4"):
            assert_sdist_build(project_path)
