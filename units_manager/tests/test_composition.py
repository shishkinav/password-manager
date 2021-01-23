import unittest
from db_manager import managers as db_sql
from units_manager.models import PrintComposition


class TestComposition(unittest.TestCase):
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
    
    def test_print_users(self):
        """Проверка количества пользователей в БД"""
        self.user_proxy.add_obj({
            "username": "second",
            "password": "second"
        })
        _users = self.user_proxy.manager.get_objects(filters={})
        _composition = PrintComposition()
        _composition.prepare_data(data_objects=_users, box_attrs=["username"])
        
        
