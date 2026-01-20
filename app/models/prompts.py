from pydantic import BaseModel


class CategoryDefinition(BaseModel):
    name: str
    definition: str


class FewShotExample(BaseModel):
    id: str
    news_content: str
    category: str
    reasoning: str


class PromptConfig(BaseModel):
    categories: list[CategoryDefinition]


class FewShotConfig(BaseModel):
    examples: list[FewShotExample]
