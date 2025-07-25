from typing import Any, Dict

from poetry.core.masonry.utils.helpers import distribution_name

from poexy_core.pyproject.exceptions import PyProjectError


class ModulePackage:
    @staticmethod
    def __transform_config(config: Dict[str, Any]) -> Dict[str, Any]:
        package_config = config.pop("package", None)
        if package_config is None:
            raise PyProjectError("[tool.poexy.package] section not found")
        assert isinstance(package_config, dict)
        if len(package_config.keys()) == 0:
            raise PyProjectError("[tool.poexy.package] section not found")
        if len(package_config.keys()) > 1:
            raise PyProjectError(
                "[tool.poexy.package] section must contain only one package definition"
            )
        package_name, package_config = package_config.popitem()
        package_config = {"name": package_name, **package_config}
        config["package"] = package_config
        return config

    @staticmethod
    def from_project_config(config: Dict[str, Any]) -> Dict[str, Any]:
        project = config.get("project", None)
        assert isinstance(project, dict)
        project_name = project.get("name", None)
        if project_name is None:
            raise PyProjectError("[project] section must contain a name")
        project_name = distribution_name(project_name)
        config["package"] = {
            project_name: {
                "source": project_name,
            }
        }
        return ModulePackage.__transform_config(config)

    @staticmethod
    def from_poexy_config(config: Dict[str, Any]) -> Dict[str, Any]:
        return ModulePackage.__transform_config(config)


class BinaryPackage:
    @staticmethod
    def __transform_config(config: Dict[str, Any]) -> Dict[str, Any]:
        binary_config = config.get("binary", None)
        if binary_config is None:
            raise PyProjectError("[tool.poexy.binary] section not found")
        assert isinstance(binary_config, dict)
        executable_name = binary_config.get("name", None)
        if executable_name is None:
            package_name = config.get("name", None)
            if package_name is None:
                raise PyProjectError("[tool.poexy.binary] section must contain a name")
            executable_name = package_name.replace("_", "-")
            binary_config["name"] = executable_name
        else:
            binary_config["name"] = executable_name.replace("_", "-")
        return config

    @staticmethod
    def from_project_config(config: Dict[str, Any]) -> Dict[str, Any]:
        project = config.get("project", None)
        assert isinstance(project, dict)
        project_name = project.get("name", None)
        if project_name is None:
            raise PyProjectError("[project] section must contain a name")
        config["binary"] = {"name": project_name}
        return BinaryPackage.__transform_config(config)

    @staticmethod
    def from_poexy_config(config: Dict[str, Any]) -> Dict[str, Any]:
        binary_config = config.get("binary", None)
        if binary_config is None:
            binary_config = {"name": None}
            config["binary"] = binary_config
        elif binary_config.get("name", None) is None:
            package_config = config.get("package", None)
            if package_config is None:
                raise PyProjectError("[tool.poexy.package] section not found")
            assert isinstance(package_config, dict)
            package_name = package_config.get("name", None)
            if package_name is None:
                raise PyProjectError("[tool.poexy.package] section must contain a name")
            binary_config["name"] = package_name.replace("_", "-")
        assert isinstance(binary_config, dict)
        if len(binary_config.keys()) == 0:
            raise PyProjectError("[tool.poexy.binary] section not found")
        return BinaryPackage.__transform_config(config)
