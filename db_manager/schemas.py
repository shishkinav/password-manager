from typing import List, Optional, ClassVar
from pydantic import BaseModel


class UserBase(BaseModel):
    id: int
    username: str
    password: str


class CategoryBase(BaseModel):
    # id: int
    name: str


class Unit(BaseModel):
    id: int
    name: str
    login: str
    password: str
    url: str
    user: Optional[UserBase]
    category: Optional[CategoryBase]

    class Config:
        orm_mode = True


class User(UserBase):
    units: List[Unit] = []
    # categories: List[CategoryBase] = []

    class Config:
        orm_mode = True


class Category(CategoryBase):
    units: List[Unit] = []
    # user: Optional[UserBase]

    class Config:
        orm_mode = True
