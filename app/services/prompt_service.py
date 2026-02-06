import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel

from app.models.prompts import (
    FewShotConfig,
    PromptConfig,
    PromptHistoryRecord,
    SystemPromptConfig,
    VersionedFewShotConfig,
    VersionedPromptConfig,
    VersionedSystemPromptConfig,
)


PromptUpdateSource = Literal["direct_save", "approved_change_request"]


class PromptStorageFileMissingError(Exception):
    """Raised when a required prompt storage file is missing."""

    def __init__(self, filepath: Path):
        self.filepath = filepath
        super().__init__(f"Missing required prompt storage file: {filepath}")


class PromptStorageValidationError(Exception):
    """Raised when prompt storage data has invalid schema."""

    def __init__(self, filepath: Path, details: str):
        self.filepath = filepath
        super().__init__(f"Invalid prompt data in {filepath}: {details}")


class PromptHistoryVersionNotFoundError(Exception):
    """Raised when a requested prompt history version cannot be found."""

    def __init__(self, history_file: Path, version: int):
        self.history_file = history_file
        self.version = version
        super().__init__(
            f"Version {version} not found in prompt history file: {history_file}"
        )


class PromptService:
    def __init__(self, workspace_dir: Path):
        self.workspace_dir = Path(workspace_dir)
        self.categories_file = self.workspace_dir / "category_definitions.json"
        self.categories_history_file = self.workspace_dir / "category_definitions.history.jsonl"
        self.few_shots_file = self.workspace_dir / "few_shot_examples.json"
        self.few_shots_history_file = self.workspace_dir / "few_shot_examples.history.jsonl"
        self.system_prompt_file = self.workspace_dir / "system_prompt.json"
        self.system_prompt_history_file = self.workspace_dir / "system_prompt.history.jsonl"

    def get_categories(self) -> VersionedPromptConfig:
        data = self._read_json_file(self.categories_file)
        return self._validate_model(self.categories_file, VersionedPromptConfig, data)

    def save_categories(
        self,
        config: PromptConfig,
        updated_by: str,
        source: PromptUpdateSource,
        change_request_id: str | None,
    ) -> VersionedPromptConfig:
        self._validate_write_metadata(updated_by, source, change_request_id)
        self._require_file(self.categories_history_file)
        current = self.get_categories()
        if current.categories == config.categories:
            return current
        next_state = VersionedPromptConfig(
            version=current.version + 1,
            categories=config.categories,
        )
        self._write_json_file(self.categories_file, next_state.model_dump())
        self._append_history_entry(
            history_file=self.categories_history_file,
            version=next_state.version,
            updated_by=updated_by,
            source=source,
            change_request_id=change_request_id,
            content=config.model_dump(),
        )
        return next_state

    def get_categories_history(self) -> list[PromptHistoryRecord]:
        return self._read_history_file(self.categories_history_file)

    def restore_categories(
        self,
        version: int,
        updated_by: str,
        source: PromptUpdateSource,
        change_request_id: str | None,
    ) -> VersionedPromptConfig:
        content = self._get_content_by_version(self.categories_history_file, version)
        config = PromptConfig.model_validate(content)
        return self.save_categories(config, updated_by, source, change_request_id)

    def get_categories_content_for_version(self, version: int) -> PromptConfig:
        content = self._get_content_by_version(self.categories_history_file, version)
        return PromptConfig.model_validate(content)

    def get_few_shots(self) -> VersionedFewShotConfig:
        data = self._read_json_file(self.few_shots_file)
        return self._validate_model(self.few_shots_file, VersionedFewShotConfig, data)

    def save_few_shots(
        self,
        config: FewShotConfig,
        updated_by: str,
        source: PromptUpdateSource,
        change_request_id: str | None,
    ) -> VersionedFewShotConfig:
        self._validate_write_metadata(updated_by, source, change_request_id)
        self._require_file(self.few_shots_history_file)
        current = self.get_few_shots()
        if current.examples == config.examples:
            return current
        next_state = VersionedFewShotConfig(
            version=current.version + 1,
            examples=config.examples,
        )
        self._write_json_file(self.few_shots_file, next_state.model_dump())
        self._append_history_entry(
            history_file=self.few_shots_history_file,
            version=next_state.version,
            updated_by=updated_by,
            source=source,
            change_request_id=change_request_id,
            content=config.model_dump(),
        )
        return next_state

    def get_few_shots_history(self) -> list[PromptHistoryRecord]:
        return self._read_history_file(self.few_shots_history_file)

    def restore_few_shots(
        self,
        version: int,
        updated_by: str,
        source: PromptUpdateSource,
        change_request_id: str | None,
    ) -> VersionedFewShotConfig:
        content = self._get_content_by_version(self.few_shots_history_file, version)
        config = FewShotConfig.model_validate(content)
        return self.save_few_shots(config, updated_by, source, change_request_id)

    def get_few_shots_content_for_version(self, version: int) -> FewShotConfig:
        content = self._get_content_by_version(self.few_shots_history_file, version)
        return FewShotConfig.model_validate(content)

    def get_system_prompt(self) -> VersionedSystemPromptConfig:
        data = self._read_json_file(self.system_prompt_file)
        return self._validate_model(
            self.system_prompt_file,
            VersionedSystemPromptConfig,
            data,
        )

    def save_system_prompt(
        self,
        config: SystemPromptConfig,
        updated_by: str,
        source: PromptUpdateSource,
        change_request_id: str | None,
    ) -> VersionedSystemPromptConfig:
        self._validate_write_metadata(updated_by, source, change_request_id)
        self._require_file(self.system_prompt_history_file)
        current = self.get_system_prompt()
        if current.content == config.content:
            return current
        next_state = VersionedSystemPromptConfig(
            version=current.version + 1,
            content=config.content,
        )
        self._write_json_file(self.system_prompt_file, next_state.model_dump())
        self._append_history_entry(
            history_file=self.system_prompt_history_file,
            version=next_state.version,
            updated_by=updated_by,
            source=source,
            change_request_id=change_request_id,
            content=config.model_dump(),
        )
        return next_state

    def get_system_prompt_history(self) -> list[PromptHistoryRecord]:
        return self._read_history_file(self.system_prompt_history_file)

    def restore_system_prompt(
        self,
        version: int,
        updated_by: str,
        source: PromptUpdateSource,
        change_request_id: str | None,
    ) -> VersionedSystemPromptConfig:
        content = self._get_content_by_version(self.system_prompt_history_file, version)
        config = SystemPromptConfig.model_validate(content)
        return self.save_system_prompt(config, updated_by, source, change_request_id)

    def get_system_prompt_content_for_version(self, version: int) -> SystemPromptConfig:
        content = self._get_content_by_version(self.system_prompt_history_file, version)
        return SystemPromptConfig.model_validate(content)

    @classmethod
    def initialize_prompt_storage(cls, workspace_dir: Path, updated_by: str) -> None:
        service = cls(workspace_dir)
        service._require_directory(service.workspace_dir)
        for filepath in service._all_prompt_files():
            if filepath.exists():
                raise FileExistsError(f"Prompt storage file already exists: {filepath}")
        service._write_json_file(
            service.categories_file,
            VersionedPromptConfig(version=1, categories=[]).model_dump(),
        )
        service._write_json_file(
            service.few_shots_file,
            VersionedFewShotConfig(version=1, examples=[]).model_dump(),
        )
        service._write_json_file(
            service.system_prompt_file,
            VersionedSystemPromptConfig(version=1, content="").model_dump(),
        )
        service._append_history_entry(
            history_file=service.categories_history_file,
            version=1,
            updated_by=updated_by,
            source="initialization",
            change_request_id=None,
            content={"categories": []},
        )
        service._append_history_entry(
            history_file=service.few_shots_history_file,
            version=1,
            updated_by=updated_by,
            source="initialization",
            change_request_id=None,
            content={"examples": []},
        )
        service._append_history_entry(
            history_file=service.system_prompt_history_file,
            version=1,
            updated_by=updated_by,
            source="initialization",
            change_request_id=None,
            content={"content": ""},
        )

    @classmethod
    def reset_prompt_storage(cls, workspace_dir: Path, updated_by: str) -> None:
        service = cls(workspace_dir)
        service._require_directory(service.workspace_dir)
        for filepath in service._all_prompt_files():
            if filepath.exists():
                filepath.unlink()
        cls.initialize_prompt_storage(workspace_dir, updated_by)

    def _all_prompt_files(self) -> list[Path]:
        return [
            self.categories_file,
            self.categories_history_file,
            self.few_shots_file,
            self.few_shots_history_file,
            self.system_prompt_file,
            self.system_prompt_history_file,
        ]

    def _require_directory(self, directory: Path) -> None:
        if not directory.exists() or not directory.is_dir():
            raise NotADirectoryError(f"Workspace directory does not exist: {directory}")

    def _require_file(self, filepath: Path) -> None:
        if not filepath.exists() or not filepath.is_file():
            raise PromptStorageFileMissingError(filepath)

    def _read_json_file(self, filepath: Path) -> dict[str, Any]:
        self._require_file(filepath)
        with open(filepath) as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise PromptStorageValidationError(filepath, "Expected JSON object")
        return data

    def _write_json_file(self, filepath: Path, data: dict[str, Any]) -> None:
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    def _validate_model(
        self,
        filepath: Path,
        model_class: type[BaseModel],
        data: dict[str, Any],
    ) -> BaseModel:
        try:
            return model_class.model_validate(data)
        except Exception as exc:
            raise PromptStorageValidationError(filepath, str(exc)) from exc

    def _append_history_entry(
        self,
        history_file: Path,
        version: int,
        updated_by: str,
        source: str,
        change_request_id: str | None,
        content: dict[str, Any],
    ) -> None:
        entry = PromptHistoryRecord(
            version=version,
            updated_at=datetime.now(timezone.utc),
            updated_by=updated_by,
            source=source,
            change_request_id=change_request_id,
            content=content,
        )
        with open(history_file, "a") as f:
            f.write(json.dumps(entry.model_dump(mode="json")) + "\n")

    def _validate_write_metadata(
        self,
        updated_by: str,
        source: PromptUpdateSource,
        change_request_id: str | None,
    ) -> None:
        if not updated_by:
            raise ValueError("updated_by is required")
        if source == "approved_change_request" and not change_request_id:
            raise ValueError("change_request_id is required for approved_change_request")
        if source == "direct_save" and change_request_id is not None:
            raise ValueError("change_request_id must be None for direct_save")

    def _read_history_file(self, history_file: Path) -> list[PromptHistoryRecord]:
        self._require_file(history_file)
        entries = []
        with open(history_file) as f:
            for line_number, line in enumerate(f, start=1):
                entries.append(self._parse_history_line(history_file, line, line_number))
        entries.sort(key=lambda entry: entry.version, reverse=True)
        return entries

    def _parse_history_line(
        self,
        history_file: Path,
        line: str,
        line_number: int,
    ) -> PromptHistoryRecord:
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise PromptStorageValidationError(
                history_file,
                f"Invalid JSON at line {line_number}: {exc}",
            ) from exc
        try:
            return PromptHistoryRecord.model_validate(raw)
        except Exception as exc:
            raise PromptStorageValidationError(
                history_file,
                f"Invalid history schema at line {line_number}: {exc}",
            ) from exc

    def _get_content_by_version(
        self,
        history_file: Path,
        version: int,
    ) -> dict[str, Any]:
        entries = self._read_history_file(history_file)
        for entry in entries:
            if entry.version == version:
                return entry.content
        raise PromptHistoryVersionNotFoundError(history_file, version)
