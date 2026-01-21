import json
from pathlib import Path

from app.models.prompts import FewShotConfig, PromptConfig, SystemPromptConfig


class PromptService:
    def __init__(self, workspace_dir: Path):
        self.workspace_dir = Path(workspace_dir)
        self.categories_file = self.workspace_dir / "category_definitions.json"
        self.few_shots_file = self.workspace_dir / "few_shot_examples.json"
        self.system_prompt_file = self.workspace_dir / "system_prompt.json"

    def get_categories(self) -> PromptConfig:
        with open(self.categories_file) as f:
            return PromptConfig.model_validate(json.load(f))

    def save_categories(self, config: PromptConfig) -> None:
        with open(self.categories_file, "w") as f:
            json.dump(config.model_dump(), f, indent=2)

    def get_few_shots(self) -> FewShotConfig:
        with open(self.few_shots_file) as f:
            return FewShotConfig.model_validate(json.load(f))

    def save_few_shots(self, config: FewShotConfig) -> None:
        with open(self.few_shots_file, "w") as f:
            json.dump(config.model_dump(), f, indent=2)

    def get_system_prompt(self) -> SystemPromptConfig:
        if not self.system_prompt_file.exists():
            return SystemPromptConfig(content="")
        with open(self.system_prompt_file) as f:
            return SystemPromptConfig.model_validate(json.load(f))

    def save_system_prompt(self, config: SystemPromptConfig) -> None:
        with open(self.system_prompt_file, "w") as f:
            json.dump(config.model_dump(), f, indent=2)
