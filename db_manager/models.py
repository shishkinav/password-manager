from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class User(Base):
    """Определение таблицы users"""
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False, unique=True,
                  sqlite_on_conflict_unique='FAIL')
    password = Column(String, nullable=False)
    units = relationship("Unit",
                         back_populates="user",
                         cascade="all, delete-orphan")
    categories = relationship("Category",
                         back_populates="user",
                         cascade="all, delete-orphan")


class Unit(Base):
    """Определение таблицы units"""
    __tablename__ = 'units'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    login = Column(String)
    secret = Column(String)
    url = Column(String)

    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"))    
    category_id = Column(Integer, ForeignKey('categories.id', ondelete="CASCADE"))
    UniqueConstraint(name, login, user_id, name='unc_name')
    
    category = relationship("Category", back_populates="units")
    user = relationship("User", back_populates="units")


class Category(Base):
    """Определение таблицы categories"""
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)

    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"))
    UniqueConstraint(name, user_id, name='unc_name')

    user = relationship("User", back_populates="categories")
    units = relationship("Unit",
                         back_populates="category",
                         cascade="all, delete-orphan")
    

