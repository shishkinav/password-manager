import unittest
from db_manager import database as db_sql


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
        cls.user_proxy.manager.clear_db()
    
    def test_count_users(self):
        """Проверка количества пользователей в БД"""
        _users = self.user_proxy.manager.get_objects(filters={})
        self.assertEqual(len(_users), 1,
            msg="Количество пользователей в БД не соответствует")

        