from typing import Literal

from pydantic import BaseModel, validator


class Module(BaseModel):
    """
    Module
    """

    name: str = "Unknown"
    pack: str
    version: str = "Unknown"
    author: list[str] = ["Unknown"]
    pypi: bool = False
    category: Literal[
        "utility", "entertainment", "dependency", "miscellaneous"
    ] = "miscellaneous"
    description: str = ""
    dependency: list[str] = None
    loaded: bool = True
    hidden: bool = False
    override_default: None | bool = None
    override_switch: None | bool = None

    @validator("category", pre=True)
    def category_validator(cls, category: str):
        if category.startswith("uti"):
            category = "utility"
        elif category.startswith("ent"):
            category = "entertainment"
        elif category.startswith("dep"):
            category = "dependency"
        elif category.startswith("mis"):
            category = "miscellaneous"
        return category

    def __str__(self):
        return self.name

    def __repr__(self):
        return (
            f"Module({self.name})\n"
            f"\tpack: {self.pack}\n"
            f"\tversion: {self.version}\n"
            f"\tauthor: {self.author}\n"
            f"\tpypi: {self.pypi}\n"
            f"\tcategory: {self.category}\n"
            f"\tdescription: {self.description}\n"
            f"\tdependency: {self.dependency}\n"
            f"\tloaded: {self.loaded}\n"
            f"\thidden: {self.hidden}\n"
            f"\toverride_default: {self.override_default}\n"
            f"\toverride_switch: {self.override_switch}\n"
        )

    def __hash__(self):
        return hash(self.name)
