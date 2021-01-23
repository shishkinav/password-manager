import unittest
from db_manager import managers as db_sql
from units_manager.models import PrintComposition


class TestComposition(unittest.TestCase):
    """Тестирование методов класса PrintComposition"""
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
        cls.user_proxy.manager.session.close_all()
        cls.user_proxy.manager.destroy_db()

    def test_print_users(self):
        """Проверка корректности возвращаемых списков на вывод"""
        self.user_proxy.add_obj({
            "username": "second",
            "password": "second"
        })
        _users = self.user_proxy.manager.get_objects(filters={})
        _composition = PrintComposition()
        data = _composition.prepare_data(data_objects=_users, box_attrs=["id", "username"])
        self.assertTrue(len(data) == 3,
            msg="Количество строк в подготовленных данных не соответствует")

        with self.assertRaises(Exception):
            data = _composition.prepare_data(data_objects=_users, box_attrs=["id", "username", "login"])
