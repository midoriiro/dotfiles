import logging
from pathlib import Path
from typing import Any, Optional, override

from pydantic import BaseModel, Field


class BaseMessage(BaseModel):
    type: str

    @override
    def model_post_init(self, __context: Any) -> None:
        self.type = self.__class__.__name__

    @staticmethod
    def from_record(record: logging.LogRecord) -> "BaseMessage":
        if record.type == JsonSchemaValidationErrorMessage.__name__:
            return JsonSchemaValidationErrorMessage.model_construct(
                json_path=record.json_path,
                error_message=record.error_message,
            )
        elif record.type == PydanticValidationErrorMessageList.__name__:
            return PydanticValidationErrorMessageList.model_construct(
                errors=[
                    PydanticValidationErrorMessage.model_construct(
                        location=error["location"],
                        error_type=error["error_type"],
                        error_message=error["error_message"],
                        input=error["input"],
                    )
                    for error in record.errors
                ]
            )
        elif record.type == FilesystemMessage.__name__:
            return FilesystemMessage.model_construct(
                level=record.levelno,
                operation=record.operation,
                message=record.message,
                path=record.path,
            )
        elif record.type == ConfigurationFileErrorMessage.__name__:
            return ConfigurationFileErrorMessage.model_construct(
                line=record.line,
                column=record.column,
                problem=record.problem,
            )
        elif record.type == ComposerMessage.__name__:
            return ComposerMessage.model_construct(
                composer_type=record.composer_type,
                error_type=record.error_type,
                error_message=record.error_message,
            )
        else:
            raise ValueError(f"Unknown message type: {record.type}")


class JsonSchemaValidationErrorMessage(BaseMessage):
    json_path: str
    error_message: str


class PydanticValidationErrorMessage(BaseMessage):
    location: str
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    input: Optional[Any] = None


class PydanticValidationErrorMessageList(BaseMessage):
    errors: list[PydanticValidationErrorMessage]


class ConfigurationFileErrorMessage(BaseMessage):
    line: int
    column: int
    problem: str


class ComposerMessage(BaseMessage):
    composer_type: str
    error_type: str
    error_message: str


class FilesystemMessage(BaseMessage):
    level: int
    operation: str
    message: str
    path: Path

    @staticmethod
    def create_folder(path: Path) -> "FilesystemMessage":
        return FilesystemMessage.model_construct(
            level=logging.INFO,
            operation="create folder",
            message=f"Folder '{path}' created.",
            path=path,
        )

    @staticmethod
    def skip_folder(path: Path) -> "FilesystemMessage":
        return FilesystemMessage.model_construct(
            level=logging.WARNING,
            operation="skip folder",
            message=f"Folder '{path}' creation skipped.",
            path=path,
        )

    @staticmethod
    def save_file(path: Path) -> "FilesystemMessage":
        return FilesystemMessage.model_construct(
            level=logging.INFO,
            operation="save file",
            message=f"File '{path}' saved.",
            path=path,
        )

    @staticmethod
    def skip_file(path: Path) -> "FilesystemMessage":
        return FilesystemMessage.model_construct(
            level=logging.WARNING,
            operation="skip file",
            message=f"File '{path}' skipped.",
            path=path,
        )

    @staticmethod
    def overwrite_file(path: Path) -> "FilesystemMessage":
        return FilesystemMessage.model_construct(
            level=logging.WARNING,
            operation="overwrite file",
            message=f"File '{path}' will be overwritten.",
            path=path,
        )

    def log(self, logger: logging.Logger) -> None:
        logger.log(
            self.level,
            self.message,
            extra={
                "type": self.type,
                "operation": self.operation,
                "path": self.path,
            },
        )
