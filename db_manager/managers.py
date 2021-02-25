from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, close_all_sessions
from settings import FILE_DB, FILE_TEST_DB
from db_manager import models, schemas
from pydantic import ValidationError
from pathlib import Path
from typing import List, Any
from encryption_manager import models as enc_models


class DBManager:
    """Менеджер управления БД"""
    _model: models.Base = None
    _schema: schemas.BaseModel = None

    def __init__(self, model: models.Base, schema: schemas.BaseModel, prod_db=True):
        self._model = model
        self._schema = schema
        self.prod_db = prod_db
        self.file_db: Path = FILE_DB if self.prod_db else FILE_TEST_DB
        self.file_db.touch()
        self.bd_url = f'sqlite:///{self.file_db}'
        engine = create_engine(self.bd_url, connect_args={"check_same_thread": False})
        models.Base.metadata.create_all(bind=engine)
        self.session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    @property
    def session(self):
        return self.session_local()

    def destroy_db(self):
        """Закрытие сессии и удаление БД"""
        close_all_sessions()
        self.file_db.unlink()

    def get_objects(self, filters: dict) -> List[Any]:
        """Получить список объектов модели с учётом переданных фильтров"""
        return self.session.query(self._model).filter_by(**filters).all()

    def get_obj(self, filters: dict) -> Any:
        """Получить объект модели с учетом указанных фильтров"""
        if len(self.get_objects(filters)) > 1:
            raise ValueError("При получении объекта выявлено более одного "
                             "экземпляра по указанным фильтрам")
        return self.session.query(self._model).filter_by(**filters).first()

    def create_obj(self, data: dict) -> bool:
        """Универсальный метод создания объекта в БД с 
        обязательной валидацией атрибутов до создания"""
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
        """Обновить данные моделей подпадающих под условия фильтрации
        на данные переданные в data"""
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
        """Удалить объекты из базы, которые подпадают под условия фильтрации"""
        db = self.session
        try:
            _objects = db.query(self._model).filter_by(**filters).all()
            for _ in _objects:
                db.delete(_)
            db.commit()
        except:
            return False
        return True

    def generate_hash(self, value: str) -> str:
        """Генерация хэш по переданному значению"""
        return enc_models.get_hash(value.encode("utf-8"))

    def __get_secret_obj(self, username: str, password: str):
        """Внутренний метод получения объекта шифровальщика"""
        _key = self.generate_hash(username + password)
        return enc_models.AESCipher(_key)

    def encrypt_value(self, username: str, password: str, raw: str) -> str:
        """Зашифровать по пользовательским данным текст raw"""
        _cipher = self.__get_secret_obj(username, password)
        return _cipher.encrypt(raw)

    def decrypt_value(self, username: str, password: str, enc: str) -> str:
        """Расшифровать по пользовательским данным ранее зашифрованный текст enc"""
        _cipher = self.__get_secret_obj(username, password)
        return _cipher.decrypt(enc)


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


class ProxyAction:
    """Класс основных действий через проксирование объектных менеджеров.
    Все методы класса Прокси будут работать с БД относительно предустановленных
    моделей и схем в соответствующих проксируемых менеджерах"""

    def __init__(self, manager: DBManager):
        """В качестве менеджера передаётся один из объектных менеджеров базы"""
        self._manager = manager

    @property
    def manager(self):
        """Обращение к проксируемому менеджеру"""
        return self._manager

    @manager.setter
    def manager(self, new_manager: DBManager) -> None:
        """Замена проксируемого менеджера через присваивание другого"""
        self._manager = new_manager

    def __check_manager(self, need_use_class: DBManager) -> bool:
        """Проверка текущего проксируемого менеджера на соответствие указанному"""
        if isinstance(self.manager, need_use_class):
            return True
        return False

    def check_obj(self, filters: dict) -> bool:
        """Проверяем наличие экземпляра модели по менеджеру в БД"""
        _obj = self.manager.get_obj(filters=filters)
        if isinstance(_obj, models.Base):
            return True
        return False

    def add_obj(self, data: dict) -> bool:
        """Создание новых объектов в БД через проксируемого менеджера.
        Не забывайте передавать для Units в data значения username и password,
        т.к. они используются для encrypt"""
        if self.__check_manager(UserManager):
            _new_user = self.manager._schema(**data)
            _data = _new_user.dict(include={"username", "password"})
            _value = ''.join([x for x in _data.values()])
            _new_user.password = self.manager.generate_hash(_value)
            data = _new_user.dict()
        if self.__check_manager(UnitManager):
            _username = data.pop("username")
            _password = data.pop("password")
            _new_unit = self.manager._schema(**data)
            _new_unit.secret = self.manager.encrypt_value(
                username=_username, password=_password, raw=_new_unit.secret
            )
            data = _new_unit.dict()
        if self.__check_manager(CategoryManager):
            self.manager._schema(**data)
        return self.manager.create_obj(data=data)

    def update_obj(self, filters: dict, data: dict):
        """Обновление объектов по проксируемому менеджеру,
        удовлетворяющих условиям в filters, замена данных указанных в data.
        Не забывайте при обновлении пароля юнита (или пользователя с юнитами)
        передавать в data текущий пароль пользователя с ключом "current_password",
        т.к. он используется для encrypt (decrypt)"""
        if not self.check_obj(filters=filters):
            raise ValueError("Объект изменения не определён")

        if self.__check_manager(UserManager):
            _user = self.manager.get_obj(filters=filters)
            _new_username = data.get("username")
            _new_password = data.get("password")
            if not _new_username and not _new_password:
                raise KeyError("Нечего апдейтить")

            _current_password = data.get("current_password")
            if not _new_password and not _current_password:
                raise KeyError("Не передан пароль пользователя для обновления хэша")

            if not _new_password:
                _new_password = _current_password
            if not _new_username:
                _new_username = _user.username
            data["password"] = self.manager.generate_hash(_new_username + _new_password)
            if _current_password:
                data.pop("current_password")

            # если у пользователя есть юниты, их надо перешифровать
            unit_proxy = ProxyAction(UnitManager(prod_db=self.manager.prod_db))
            _units = unit_proxy.manager.get_objects(filters={"user_id": _user.id})
            if _units and not _current_password:
                raise KeyError("Не хватает данных для расшифровки юнитов: "
                               "не передан текущий пароль пользователя")
            for _unit in _units:
                password_for_login = unit_proxy.get_secret(filters={
                    "username": _user.username,
                    "password": _current_password,
                    "name": _unit.name,
                    "login": _unit.login
                })
                unit_data = {"secret": self.manager.encrypt_value(
                    username=_new_username, password=_new_password, raw=password_for_login
                )}
                unit_proxy.manager.update_objects(filters={"name": _unit.name, "login": _unit.login,
                                                           "user_id": _user.id},
                                                  data=unit_data)
        if self.__check_manager(UnitManager):
            _user_id = filters.get("user_id")
            if not _user_id:
                raise KeyError("В условиях filters не передан id пользователя")
            if data.get("user_id"):
                raise ValueError("В рамках изменения юнита корректировка "
                                 "принадлежности пользователю не производится")
            _current_password = data.pop("current_password", None)
            coming_filters = filters.copy()
            coming_filters.update(data)
            if self.check_obj(filters=coming_filters):
                raise ValueError("По заданным атрибутам для изменения юнит уже существует")
            _secret = data.pop("secret", None)
            if _secret:

                if not _current_password:
                    raise KeyError("Не передан пароль пользователя для шифрования юнита")
                user_proxy = ProxyAction(UserManager(prod_db=self.manager.prod_db))
                _user = user_proxy.manager.get_obj(filters={"id": _user_id})
                data["secret"] = self.manager.encrypt_value(
                    username=_user.username, password=_current_password, raw=_secret
                )
        return self.manager.update_objects(filters=filters, data=data)

    def delete_obj(self, filters: dict) -> bool:
        """Удаление объектов по проксируемому менеджеру,
        удовлетворяющих условиям в filters"""
        return self.manager.delete_objects(filters=filters)

    def check_user_password(self, username: str, password: str):
        """Проверка наличия пользователя с таким именем и паролем"""
        if self.__check_manager(UserManager):
            pass_hash = self.manager.generate_hash(username + password)
            _obj = self.manager.get_obj(filters={"username": username, "password": pass_hash})
            return True if _obj else False
        raise TypeError

    def get_secret(self, filters: dict) -> str:
        """Получить пароль юнита.
        Не забывайте передавать в filters значения username и password,
        т.к. они используются для decrypt"""
        if not self.__check_manager(UnitManager):
            raise TypeError
        if "username" not in filters or "password" not in filters:
            raise KeyError("Не все обязательные атрибуты метода переданы")
        _username = filters.pop("username")
        _password = filters.pop("password")

        _obj = self.manager.get_obj(filters)
        if _obj:
            return self.manager.decrypt_value(
                username=_username, password=_password, enc=_obj.secret
            )
        raise IndexError("По указанным фильтрам не определён экземпляр юнита "
                             "для извлечения пароля")

    def get_prepared_category(self, filters: dict):
        """Получить объект модели категории с учетом указанных фильтров.
        Если в фильтрах не указано название категории,
        добавляем фильтр для "name" со значением по-умолчанию: "default".
        Если объект не найден, пробуем добавить его с атрибутами на основе фильтров"""
        if not self.__check_manager(CategoryManager):
            raise TypeError
        if not filters.get("name"):
            filters["name"] = "default"  # значение по-умолчанию
        if not self.check_obj(filters=filters):
            self.add_obj(data=filters)
            if not self.check_obj(filters=filters):
                raise IndexError
        return self.manager.get_obj(filters=filters)
