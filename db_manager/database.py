from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
from settings import FILE_DB, FILE_TEST_DB
from db_manager import models, schemas
from pydantic import ValidationError
from pathlib import Path
from typing import List, Any


class DBManager:
    """Менеджер управления БД"""
    _model: models.Base = None
    _schema: schemas.BaseModel = None
    
    def __init__(self, model: models.Base, schema: schemas.BaseModel, prod_db=True):
        self._model = model
        self._schema = schema
        self.file_db: Path = FILE_DB if prod_db else FILE_TEST_DB
        self.file_db.touch()
        self.bd_url = f'sqlite:///{self.file_db}'
        engine = create_engine(self.bd_url, connect_args={"check_same_thread": False})
        models.Base.metadata.create_all(bind=engine)
        self.session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    @property
    def session(self):
        return self.session_local()
        
    def clear_db(self):
        self.session.close()
        self.file_db.unlink()

    def get_objects(self, filters: dict) -> List[Any]:
        """Получить список объектов модели с учётом переданных фильтров"""
        return self.session.query(self._model).filter_by(**filters).all()

    def get_obj(self, filters: dict) -> Any:
        """Получить объект модели с учетом указанных фильтров"""
        return self.session.query(self._model).filter_by(**filters).first() 

    def create_obj(self, data: dict) -> bool:
        db = self.session
        try:
            schema_obj = self._schema(**data)
            new_obj = self._model(**schema_obj.dict())
            db.add(new_obj)
            db.commit()
            db.refresh(new_obj)
        except ValidationError:
            return False
        return True

    def update_objects(self, filters: dict, data: dict) -> bool:
        db = self.session
        try:
            db.query(self._model).filter_by(**filters).update(
                data,
                synchronize_session='evaluate'
            )
            db.commit()
        except:
            return False
        return True

    def delete_objects(self, filters: dict) -> bool:
        db = self.session
        try:
            db.query(self._model).filter_by(**filters).delete(synchronize_session='evaluate')
            db.commit()
        except:
            return False
        return True


class CategoryManager(DBManager):

    def __init__(self, prod_db=True) -> None:
        super().__init__(
            model=models.Category,
            schema=schemas.Category,
            prod_db=prod_db
        )


class UserManager(DBManager):

    def __init__(self, prod_db=True) -> None:
        super().__init__(
            model=models.User,
            schema=schemas.User,
            prod_db=prod_db
        )


class UnitManager(DBManager):

    def __init__(self, prod_db=True) -> None:
        super().__init__(
            model=models.Unit,
            schema=schemas.Unit,
            prod_db=prod_db
        )
