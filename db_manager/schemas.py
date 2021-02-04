from typing import List
from pydantic import BaseModel


class UserBase(BaseModel):
    username: str
    password: str


class CategoryBase(BaseModel):
    name: str
    user_id: int


class Unit(BaseModel):
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
