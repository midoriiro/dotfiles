from pydantic import BaseModel, Field

from ignite.models.container import Container
from ignite.models.workspace import Workspace


class Configuration(BaseModel):
    """
    Represents a configuration.
    """

    container: Container = Field(..., description="Container configuration")
    workspace: Workspace = Field(..., description="Workspace configuration")


Configuration.model_rebuild()
