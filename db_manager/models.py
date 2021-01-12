from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, MetaData
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
    # categories = relationship("Category",
    #                      back_populates="user",
    #                      cascade="all, delete-orphan")


class Unit(Base):
    """Определение таблицы units"""
    __tablename__ = 'units'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    login = Column(String)
    password = Column(String)
    url = Column(String)

    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"))    
    category_id = Column(Integer, ForeignKey('categories.id', ondelete="CASCADE"))
    
    category = relationship("Category", back_populates="units")
    user = relationship("User", back_populates="units")


class Category(Base):
    """Определение таблицы units"""
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)

    units = relationship("Unit",
                         back_populates="category",
                         cascade="all, delete-orphan")
    

