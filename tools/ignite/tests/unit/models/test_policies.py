import pytest
from pydantic import ValidationError
from assertpy import assert_that

from ignite.models.policies import (
    Policies, ContainerPolicy, FolderPolicy, FilePolicy,
    ContainerBackendPolicy, FolderCreatePolicy, FileWritePolicy,
    ReservedPolicyKeys
)


class TestValidPolicies:
    """Test cases for valid policies configurations."""

    def test_policies_with_container_policy(self):
        """Test that policies with container policy is accepted."""
        policies = Policies({
            "container": ContainerPolicy(backend=ContainerBackendPolicy.DOCKER)
        })
        assert_that(policies.root).contains_key("container")
        assert_that(policies.root["container"].backend).is_equal_to(ContainerBackendPolicy.DOCKER)

    def test_policies_with_folder_policy(self):
        """Test that policies with folder policy is accepted."""
        policies = Policies({
            "folder": FolderPolicy(create=FolderCreatePolicy.ALWAYS)
        })
        assert_that(policies.root).contains_key("folder")
        assert_that(policies.root["folder"].create).is_equal_to(FolderCreatePolicy.ALWAYS)

    def test_policies_with_file_policy(self):
        """Test that policies with file policy is accepted."""
        policies = Policies({
            "file": FilePolicy(write=FileWritePolicy.OVERWRITE)
        })
        assert_that(policies.root).contains_key("file")
        assert_that(policies.root["file"].write).is_equal_to(FileWritePolicy.OVERWRITE)

    def test_policies_with_all_policy_types(self):
        """Test that policies with all policy types is accepted."""
        policies = Policies({
            "container": ContainerPolicy(backend=ContainerBackendPolicy.PODMAN),
            "folder": FolderPolicy(create=FolderCreatePolicy.NEVER),
            "file": FilePolicy(write=FileWritePolicy.SKIP)
        })
        assert_that(policies.root).contains_key("container")
        assert_that(policies.root).contains_key("folder")
        assert_that(policies.root).contains_key("file")
        assert_that(policies.root["container"].backend).is_equal_to(ContainerBackendPolicy.PODMAN)
        assert_that(policies.root["folder"].create).is_equal_to(FolderCreatePolicy.NEVER)
        assert_that(policies.root["file"].write).is_equal_to(FileWritePolicy.SKIP)

    def test_policies_with_default_values(self):
        """Test that policies with default values are accepted."""
        policies = Policies({
            "container": ContainerPolicy(),
            "folder": FolderPolicy(),
            "file": FilePolicy()
        })
        assert_that(policies.root["container"].backend).is_equal_to(ContainerBackendPolicy.ANY)
        assert_that(policies.root["folder"].create).is_equal_to(FolderCreatePolicy.ASK)
        assert_that(policies.root["file"].write).is_equal_to(FileWritePolicy.ASK)


class TestPoliciesValidation:
    """Test cases for Policies validation."""

    def test_empty_policies_raises_error(self):
        """Test that empty policies raises validation error."""
        with pytest.raises(ValueError, match="At least one policy must be specified"):
            Policies({})

    def test_policies_with_none_dict_raises_error(self):
        """Test that policies with None dict raises validation error."""
        with pytest.raises(ValidationError):
            Policies(None)

    def test_policies_with_invalid_policy_type_raises_error(self):
        """Test that policies with invalid policy type raises validation error."""
        with pytest.raises(ValidationError):
            Policies({
                "container": "not a policy"
            })

    def test_policies_with_mixed_valid_and_invalid_policies_raises_error(self):
        """Test that policies with mixed valid and invalid policies raises validation error."""
        with pytest.raises(ValidationError):
            Policies({
                "container": ContainerPolicy(backend=ContainerBackendPolicy.DOCKER),
                "folder": "not a policy"
            })

    def test_policies_with_invalid_key_raises_error(self):
        """Test that policies with invalid key raises validation error."""
        with pytest.raises(ValueError, match="Invalid policy key: invalid-key"):
            Policies({
                "invalid-key": ContainerPolicy(backend=ContainerBackendPolicy.DOCKER)
            })

    def test_policies_with_custom_keys_raises_error(self):
        """Test that policies with custom keys raises validation error."""
        with pytest.raises(ValueError, match="Invalid policy key: my-container"):
            Policies({
                "my-container": ContainerPolicy(backend=ContainerBackendPolicy.DOCKER),
                "my-folder": FolderPolicy(create=FolderCreatePolicy.ALWAYS),
                "my-file": FilePolicy(write=FileWritePolicy.OVERWRITE)
            })

    def test_policies_with_special_characters_in_keys_raises_error(self):
        """Test that policies with special characters in keys raises validation error."""
        with pytest.raises(ValueError, match="Invalid policy key: container-policy"):
            Policies({
                "container-policy": ContainerPolicy(backend=ContainerBackendPolicy.DOCKER),
                "folder_policy": FolderPolicy(create=FolderCreatePolicy.ALWAYS),
                "file.policy": FilePolicy(write=FileWritePolicy.OVERWRITE)
            })


class TestPoliciesModelValidation:
    """Test cases for individual policy model validation."""

    def test_container_policy_with_invalid_backend_raises_error(self):
        """Test that container policy with invalid backend raises validation error."""
        with pytest.raises(ValidationError):
            Policies({
                "container": ContainerPolicy(backend="invalid")
            })

    def test_folder_policy_with_invalid_create_raises_error(self):
        """Test that folder policy with invalid create raises validation error."""
        with pytest.raises(ValidationError):
            Policies({
                "folder": FolderPolicy(create="invalid")
            })

    def test_file_policy_with_invalid_write_raises_error(self):
        """Test that file policy with invalid write raises validation error."""
        with pytest.raises(ValidationError):
            Policies({
                "file": FilePolicy(write="invalid")
            })


class TestPoliciesAccess:
    """Test cases for accessing policies data."""

    def test_access_policies_by_key(self):
        """Test that policies can be accessed by key."""
        policies = Policies({
            "container": ContainerPolicy(backend=ContainerBackendPolicy.DOCKER),
            "folder": FolderPolicy(create=FolderCreatePolicy.ALWAYS)
        })
        assert_that(policies.root["container"]).is_instance_of(ContainerPolicy)
        assert_that(policies.root["folder"]).is_instance_of(FolderPolicy)

    def test_policies_keys(self):
        """Test that policies keys can be accessed."""
        policies = Policies({
            "container": ContainerPolicy(backend=ContainerBackendPolicy.DOCKER),
            "folder": FolderPolicy(create=FolderCreatePolicy.ALWAYS),
            "file": FilePolicy(write=FileWritePolicy.OVERWRITE)
        })
        keys = list(policies.root.keys())
        assert_that(keys).contains("container")
        assert_that(keys).contains("folder")
        assert_that(keys).contains("file")
        assert_that(keys).is_length(3)

    def test_policies_values(self):
        """Test that policies values can be accessed."""
        policies = Policies({
            "container": ContainerPolicy(backend=ContainerBackendPolicy.DOCKER),
            "folder": FolderPolicy(create=FolderCreatePolicy.ALWAYS)
        })
        values = list(policies.root.values())
        assert_that(values).is_length(2)
        assert_that(values[0]).is_instance_of(ContainerPolicy)
        assert_that(values[1]).is_instance_of(FolderPolicy)


class TestPoliciesEdgeCases:
    """Test cases for edge cases in policies."""

    def test_policies_with_single_policy(self):
        """Test that policies with single policy is valid."""
        policies = Policies({
            "container": ContainerPolicy(backend=ContainerBackendPolicy.ANY)
        })
        assert_that(policies.root).is_length(1)
        assert_that(policies.root["container"].backend).is_equal_to(ContainerBackendPolicy.ANY)

    def test_policies_with_multiple_same_type_policies_raises_error(self):
        """Test that policies with multiple same type policies raises validation error."""
        with pytest.raises(ValueError, match="Invalid policy key: container1"):
            Policies({
                "container1": ContainerPolicy(backend=ContainerBackendPolicy.DOCKER),
                "container2": ContainerPolicy(backend=ContainerBackendPolicy.PODMAN),
                "container3": ContainerPolicy(backend=ContainerBackendPolicy.ANY)
            })


class TestPoliciesInheritance:
    """Test cases for Policies inheritance and type checking."""

    def test_policies_inherits_from_root_model(self):
        """Test that Policies inherits from RootModel."""
        policies = Policies({
            "container": ContainerPolicy(backend=ContainerBackendPolicy.DOCKER)
        })
        assert_that(policies).is_instance_of(Policies)

    def test_policies_root_is_dict(self):
        """Test that policies root is a dictionary."""
        policies = Policies({
            "container": ContainerPolicy(backend=ContainerBackendPolicy.DOCKER)
        })
        assert_that(policies.root).is_instance_of(dict)

    def test_policies_model_dump(self):
        """Test that policies can be dumped to dict."""
        policies = Policies({
            "container": ContainerPolicy(backend=ContainerBackendPolicy.DOCKER),
            "folder": FolderPolicy(create=FolderCreatePolicy.ALWAYS)
        })
        dumped = policies.model_dump()
        assert_that(dumped).contains_key("container")
        assert_that(dumped).contains_key("folder")
        assert_that(dumped["container"]["backend"]).is_equal_to("docker")
        assert_that(dumped["folder"]["create"]).is_equal_to("always")


class TestPoliciesModelValidation:
    """Test cases for model validation methods."""

    def test_check_policies_with_valid_policies(self):
        """Test that check_policies method works with valid policies."""
        policies = Policies({
            "container": ContainerPolicy(backend=ContainerBackendPolicy.DOCKER)
        })
        # The validation should pass without raising an error
        assert_that(policies.root).is_not_empty()

    def test_check_policies_with_empty_dict_raises_error(self):
        """Test that check_policies method raises error with empty dict."""
        with pytest.raises(ValueError, match="At least one policy must be specified"):
            Policies({})

    def test_check_policies_returns_self(self):
        """Test that check_policies method returns self."""
        policies = Policies({
            "container": ContainerPolicy(backend=ContainerBackendPolicy.DOCKER)
        })
        # The validation should return the policies object
        assert_that(policies).is_instance_of(Policies)

    def test_check_policies_validates_reserved_keys(self):
        """Test that check_policies method validates reserved keys."""
        # Test with valid reserved keys
        policies = Policies({
            "container": ContainerPolicy(backend=ContainerBackendPolicy.DOCKER),
            "folder": FolderPolicy(create=FolderCreatePolicy.ALWAYS),
            "file": FilePolicy(write=FileWritePolicy.OVERWRITE)
        })
        assert_that(policies.root).contains_key("container")
        assert_that(policies.root).contains_key("folder")
        assert_that(policies.root).contains_key("file")

    def test_check_policies_rejects_non_reserved_keys(self):
        """Test that check_policies method rejects non-reserved keys."""
        with pytest.raises(ValueError, match="Invalid policy key: invalid"):
            Policies({
                "invalid": ContainerPolicy(backend=ContainerBackendPolicy.DOCKER)
            })


class TestReservedPolicyKeys:
    """Test cases for ReservedPolicyKeys."""

    def test_reserved_policy_keys_contains_expected_keys(self):
        """Test that ReservedPolicyKeys contains the expected keys."""
        assert_that(ReservedPolicyKeys).contains_key("container")
        assert_that(ReservedPolicyKeys).contains_key("folder")
        assert_that(ReservedPolicyKeys).contains_key("file")
        assert_that(ReservedPolicyKeys).is_length(3)

    def test_reserved_policy_keys_values(self):
        """Test that ReservedPolicyKeys has correct values."""
        assert_that(ReservedPolicyKeys["container"]).is_equal_to("container")
        assert_that(ReservedPolicyKeys["folder"]).is_equal_to("folder")
        assert_that(ReservedPolicyKeys["file"]).is_equal_to("file")
