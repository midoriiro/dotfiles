import pytest

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project("readme-wrong-content-type")


def test_wheel(project, project_path, assert_wheel_build):
    with project(project_path):
        with pytest.raises(
            ValueError,
            match="is not a valid ReadmeContentType",
        ):
            assert_wheel_build(project_path)


def test_sdist(project, project_path, assert_sdist_build):
    with project(project_path):
        with pytest.raises(
            ValueError,
            match="is not a valid ReadmeContentType",
        ):
            assert_sdist_build(project_path)
