from logging import INFO, ERROR

from sqlalchemy import (Column, ForeignKey, Integer, String, UniqueConstraint,
                        create_engine)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from encryption_manager.models import get_hash, get_secret_obj
from log_manager.models import log_and_print
from settings import FILE_DB

Base = declarative_base()


class User(Base):
    """Определение таблицы users"""
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    user = Column(String, nullable=False, unique=True,
                  sqlite_on_conflict_unique='FAIL')
    password = Column(String, nullable=False)
    units = relationship("Unit",
                         back_populates="user",
                         cascade="all, delete-orphan")

    def __init__(self, user, password):
        self.user = user
        self.password = password


class Unit(Base):
    """Определение таблицы units"""
    __tablename__ = 'units'
    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey('users.id', ondelete="CASCADE"))
    login = Column(String, nullable=False)
    url = Column(String)
    name = Column(String, nullable=False)
    category_id = Column(ForeignKey('categories.id', ondelete="CASCADE"))
    password = Column(String, nullable=False)
    login_name = UniqueConstraint(user_id, login, name)
    category = relationship("Category", back_populates="units")
    user = relationship("User", back_populates="units")

    def __init__(self, login, password, url=None, name='default'):
        self.login = login
        self.password = password
        self.url = url
        self.name = name


class Category(Base):
    """Определение таблицы units"""
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    category = Column(String, unique=True, nullable=False)
    units = relationship("Unit",
                         back_populates="category",
                         cascade="all, delete-orphan")

    def __init__(self, category):
        self.category = category


class UserManager:
    """Класс работы с user"""
    _session = None
    _user = None

    def __init__(self, session, user):
        self._session = session
        self._user = user

    def check_user(self, user=None):
        """
        check user existence in BD
        """
        user_tmp = self._user
        if user:
            user_tmp = user

        if self._session.query(User).filter(User.user == user_tmp).first():
            self._session.close()
            return True
        return False

    def check_user_password(self, password):
        """
        check user password in BD
        """
        pass_hash = get_hash((self._user + password).encode("utf-8"))
        if self._session.query(User).filter(User.user == self._user) \
                .filter(User.password == pass_hash).first():
            self._session.close()
            return True
        return False

    def add_user(self, password):
        """
        add user to BD
        """
        pass_hash = get_hash((self._user + password).encode("utf-8"))
        user_for_add = User(self._user, pass_hash)
        self._session.add(user_for_add)
        self._session.commit()
        self._session.close()

    def update_user(self, db, password, new_user, new_password=None):
        """
        update username (and password) in BD
        """
        if not new_password:
            new_password = password
        new_manager_obj = SQLAlchemyManager(db, self._user)
        logins = new_manager_obj.unit_obj.get_logins()
        logins_list = logins.get('logins')
        name_list = logins.get('name')
        for i in range(len(logins_list)):
            password_for_login = new_manager_obj.unit_obj.get_password(self._user, password, logins_list[i],
                                                                       name_list[i])
            new_manager_obj.unit_obj \
                .update_unit(new_user, new_password,
                             logins_list[i], password_for_login=password_for_login, name=name_list[i])

        if new_password:
            secret_password = new_user + new_password
        else:
            secret_password = new_user + password
        pass_hash = get_hash(secret_password.encode("utf-8"))
        self._session.query(User) \
            .filter(User.user == self._user).update({"user": new_user, "password": pass_hash})

        self._session.commit()
        log_and_print(f'User "{self._user}" updated. New username is "{new_user}"',
                      level=INFO)

    def del_user(self):
        """
        delete user from BD
        """
        self._session.query(Unit) \
            .filter(Unit.user.has(User.user == self._user))\
            .delete(synchronize_session='fetch')
        self._session.query(User) \
            .filter(User.user == self._user).delete()
        self._session.commit()

    def all_users(self):
        """
        list of users
        """
        users_list = []
        users = self._session.query(User).all()
        for user in users:
            users_list.append(user.user)
        users_list.sort()
        return users_list


class UnitManager:
    """Класс работы с unit"""
    _session = None
    _user = None

    def __init__(self, session, user):
        self._session = session
        self._user = user

    def get_logins(self, category=None):
        """Выдача units"""

        def make_logins_obj(units_list):
            """Выдача логинов, из списка"""
            units_obj = {
                "logins": [],
                "category": [],
                "url": [],
                "name": []
            }

            if units_list:
                for unit_ in units_list:
                    units_obj['logins'].append(unit_.login)
                    units_obj['category']\
                        .append(unit_.category.category if unit_.category.category else 'default')
                    units_obj['url']\
                        .append(unit_.url if unit_.url else '')
                    units_obj['name']\
                        .append(unit_.name if unit_.name else '')
            return units_obj

        if category:
            units = self._session.query(Unit)\
                .filter(Unit.user.has(User.user == self._user)
                        & Unit.category.has(Category.category == category)).all()
            return make_logins_obj(units)
        else:
            units = self._session.query(Unit)\
                .filter(Unit.user.has(User.user == self._user)).all()
            return make_logins_obj(units)

    def check_login(self, login, name, msg_need='not exist'):
        """Проверка существования логина"""
        if self._session.query(Unit)\
            .filter(Unit.user.has(User.user == self._user) & (Unit.login == login)
                    & (Unit.name == name)).all():
            if msg_need == 'exist':
                log_and_print(f'login "{login}" with "{name}" name already exists', level=ERROR)
            return True
        else:
            if msg_need == 'not exist':
                log_and_print(f'login "{login}" with "{name}" name not exists', level=ERROR)
            return False

    def get_category(self, category):
        """Выдаем категорию, если есть, иначе создаем"""
        category_obj = self._session.query(Category)\
            .filter(Category.category == category).first()
        if category_obj:
            return category_obj
        else:
            return Category(category=category)

    def get_user(self):
        """Выдаем пользователя"""
        return self._session.query(User).filter(User.user == self._user).first()

    def add_unit(self, user, password, login, password_for_login, name='default',
                 category='default', url=None):
        """Добавление unit"""
        secret_obj = get_secret_obj(user, password)
        unit_for_add = Unit(login, secret_obj.encrypt(password_for_login), url, name)
        self._session.add(unit_for_add)
        unit_for_add.category = self.get_category(category)
        unit_for_add.user = self.get_user()
        self._session.commit()

    def get_password(self, user, password, login, name):
        """Получение пароля"""
        secret_obj = get_secret_obj(user, password)
        unit_obj = self._session.query(Unit)\
            .filter(Unit.user.has(User.user == self._user) &
                    (Unit.login == login) & (Unit.name == name)).first()
        return secret_obj.decrypt(unit_obj.password)

    def update_unit(self, user, password, login, name, new_login=None, password_for_login=None,
                    new_category=None, url=None, new_name=None):
        """Обновление unit"""
        update_dict = {'login': login}
        if new_login:
            update_dict['login'] = new_login
        if password_for_login:
            secret_obj = get_secret_obj(user, password)
            update_dict['password'] = secret_obj.encrypt(password_for_login)
        if url:
            update_dict['url'] = url
        if new_name:
            update_dict['name'] = new_name

        if new_category:
            self._session.query(Unit)\
                .filter(Unit.user.has(User.user == self._user)
                        & (Unit.login == login) & (Unit.name == name))\
                .first().category = self.get_category(new_category)
        self._session.query(Unit)\
            .filter(Unit.user.has(User.user == self._user)
                    & (Unit.login == login) & (Unit.name == name))\
            .update(update_dict, synchronize_session='fetch')
        self._session.commit()

    def delete_unit(self, login, name):
        """Удаление unit"""
        self._session.query(Unit) \
            .filter(Unit.user.has(User.user == self._user)
                    & (Unit.login == login) & (Unit.name == name))\
            .delete(synchronize_session='fetch')
        self._session.commit()


class SQLAlchemyManager:
    """Менеджер управления БД, предположительно будет отвечать за установление
    коннектов с базой, CRUD(Create, Read, Update, Delete) по хранящимся юнитам"""
    _file_user_db = ''
    _session_for_user = None
    _session_for_unit = None

    _user = None

    user_obj = None
    unit_obj = None

    @property
    def file_user_db(self):
        return self._file_user_db

    @property
    def session_for_user(self):
        return self._session_for_user

    @property
    def session_for_unit(self):
        return self._session_for_unit

    @property
    def user(self):
        return self._user

    def __init__(self, file_db=FILE_DB, user=None):
        """Инициализация класса при вызове с поднятием текущей сессии"""
        self._user = user
        self._file_user_db = file_db

        # Инициализация User
        engine = create_engine(f'sqlite:///{self.file_user_db}', echo=False)

        # Создание файла БД, если его нет
        Base.metadata.create_all(engine)

        self._session_for_user = sessionmaker(bind=engine)()

        self.user_obj = UserManager(self.session_for_user, self.user)
        self.unit_obj = UnitManager(self.session_for_user, self.user)
