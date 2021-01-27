import time
import unittest
from db_manager import managers as db_sql
import logging
import log_manager.config


logger = logging.getLogger(__name__)


class TestDatabase(unittest.TestCase):
    _login_user = 'temp'
    _password_user = 'temp1234!@#$'
    user_proxy = db_sql.ProxyAction(db_sql.UserManager(prod_db=False))
    category_proxy = db_sql.ProxyAction(db_sql.CategoryManager(prod_db=False))
    unit_proxy = db_sql.ProxyAction(db_sql.UnitManager(prod_db=False))

    @classmethod
    def setUpClass(cls):
        """Подготовка перед тестированием"""
        # создаём тестового пользователя в БД
        cls.user_proxy.add_obj({
            "username": cls._login_user,
            "password": cls._password_user
        })

    @classmethod
    def tearDownClass(cls):
        """Очистка тестовой базы"""
        cls.user_proxy.manager.destroy_db()
    
    def test_count_users(self):
        """Проверка количества пользователей в БД"""
        _users = self.user_proxy.manager.get_objects(filters={})
        self.assertEqual(len(_users), 1,
            msg="Количество пользователей в БД не соответствует")

    def test_add_category(self):
        """Проверка создания категории в БД"""
        _user = self.user_proxy.manager.get_obj(filters={"username": self._login_user})
        self.assertTrue(
            self.category_proxy.add_obj({"name": "Проверочная категория",
                "user_id": _user.id}),
            msg="Категория не создана по указанным параметрам через прокси"
        )
        _categories = self.category_proxy.manager.get_objects(filters={})
        self.assertEqual(len(_categories), 1,
            msg="После создания категории, она не числится в БД")
        # массовое создание
        for i in range(2, 11):
            self.category_proxy.add_obj({"name": f"Тестовая категория {i}",
                "user_id": _user.id})
        _categories = self.category_proxy.manager.get_objects(filters={})
        self.assertEqual(len(_categories), 10,
            msg="Кол-во категорий после массового создания не соответствует")
    
    def test_delete_category(self):
        """Проверяем удаление всех категорий по конкретному пользователю"""
        _user = self.user_proxy.manager.get_obj(filters={"username": self._login_user})
        _categories_count = len(self.category_proxy.manager.get_objects(
            filters={"user_id": _user.id}
        ))
        self.assertTrue(_categories_count > 0, 
            msg="Для проведения этого теста требуется больше категорий у пользователя")
        self.category_proxy.delete_obj(filters={"user_id": _user.id})
        _categories_count = len(self.category_proxy.manager.get_objects(
            filters={"user_id": _user.id}
        ))  
        self.assertTrue(_categories_count == 0, 
            msg="На момент проверки у пользователя не должно быть ни одной категории")

    def test_add_unit(self):
        """Проверка создания категории в БД"""
        _filters = {"name": "Проверочная категория"}
        if not self.category_proxy.check_obj(filters=_filters):
            self.category_proxy.add_obj(data=_filters)
        _category = self.category_proxy.manager.get_obj(filters=_filters)
        _user = self.user_proxy.manager.get_obj(filters={"username": self._login_user})
        _unit_data = {
                "username": _user.username,
                "password": self._password_user,
                "name": "Проверочный юнит",
                "login": "Ya_horse",
                "secret": "qwerty1234!@#$",
                "url": "https://pydantic-docs.helpmanual.io/usage/exporting_models/#advanced-include-and-exclude",
                "user_id": _user.id,
                "category_id": _category.id
            }
        self.assertTrue(
            self.unit_proxy.add_obj(data=_unit_data),
            msg="Unit не создан по указанным параметрам через прокси"
        )
        _units = self.unit_proxy.manager.get_objects(filters={})
        self.assertEqual(len(_units), 1,
            msg="После создания юнита, он не числится в БД")
        _unit = self.unit_proxy.manager.get_obj({"name": "Проверочный юнит"})
        self.assertEqual('temp', _unit.user.__dict__.get('username'))
        self.assertEqual('Проверочная категория', _unit.category.__dict__.get('name'))
        self.user_proxy.update_obj(filters={"username": self._login_user},
            data={"units": _unit})
        _units = self.unit_proxy.manager.get_objects(filters={"user": _user})
        self.assertEqual(len(_units), 1)

    def test_logger(self):
        """Проверяем работоспособность настроенного логгера"""
        from time import sleep

        for _ in range(10):
            logger.debug('Проверка')
            logger.error('Я ошибка')
            time.sleep(1)
