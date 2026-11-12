from pydantic import BaseModel, ConfigDict, Field, field_validator


def _clean(v: str) -> str:
    return " ".join(v.split())


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str


class CategoryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=2, max_length=50)

    @field_validator("name")
    @classmethod
    def _name(cls, v: str) -> str:
        return _clean(v)


class CategoryUpdate(CategoryCreate):
    pass
