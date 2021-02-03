from typing import List, Optional, ClassVar
from pydantic import BaseModel


class UserBase(BaseModel):
    # id: int
    username: str
    password: str


class CategoryBase(BaseModel):
    # id: int
    name: str
    user_id: int


class Unit(BaseModel):
    # id: int
    name: str
    login: str
    secret: str
    url: str = ''
    user_id: int
    category_id: int

    class Config:
        orm_mode = True


class User(UserBase):
    units: List[int] = []
    categories: List[int] = []

    class Config:
        orm_mode = True


class Category(CategoryBase):
    units: List[int] = []

    class Config:
        orm_mode = True
