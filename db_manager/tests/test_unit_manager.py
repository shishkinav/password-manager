import unittest
from db_manager import managers as db_sql


class TestUnitManager(unittest.TestCase):
    _login_user = "temp"
    _password_user = "temp1234!@#$"
    _name_unit = "test-name"
    _login_unit = "test-login"
    _password_unit = "T_5678!@#$"
    user_proxy = db_sql.ProxyAction(db_sql.UserManager(prod_db=False))
    unit_proxy = db_sql.ProxyAction(db_sql.UnitManager(prod_db=False))
    category_proxy = db_sql.ProxyAction(db_sql.CategoryManager(prod_db=False))

    def setUp(self):
        """Подготовка перед каждым тестом"""
        # очищаем таблицы БД
        self.user_proxy.delete_obj(filters={})
        self.unit_proxy.delete_obj(filters={})
        self.category_proxy.delete_obj(filters={})

        # создаём тестового пользователя в БД
        self.user_proxy.add_obj({
            "username": self._login_user,
            "password": self._password_user
        })
        self._user = self.user_proxy.manager.get_obj(filters={"username": self._login_user})

        # создаём тестовый юнит пользователя в БД
        self.unit_proxy.add_obj({
            "username": self._login_user,
            "password": self._password_user,
            "name": self._name_unit,
            "login": self._login_unit,
            "secret": self._password_unit,
            "user_id": self._user.id
        })

    @classmethod
    def tearDownClass(cls):
        """Удаление тестовой БД по завершении тестов"""
        # cls.user_proxy.manager.session.close_all()
        # cls.user_proxy.manager.destroy_db()

        # очищаем таблицы БД - временное решение по причине
        # SADeprecationWarning: The Session.close_all() method is deprecated and will be removed in a future release.
        cls.user_proxy.delete_obj(filters={})
        cls.unit_proxy.delete_obj(filters={})
        cls.category_proxy.delete_obj(filters={})

    def test_add_unit(self):
        """Проверка создания юнита пользователя в БД через ProxyAction.add_obj"""
        # юнит уже создан вызовом self.unit_proxy.add_obj в setUp-методе

        # проверяем количество юнитов тестового пользователя в БД
        _units = self.unit_proxy.manager.get_objects(filters={"user_id": self._user.id})
        self.assertEqual(1, len(_units),
                         msg="Количество юнитов пользователя в БД не соответствует")

        # проверяем, что имя и логин юнита сохранены корректно
        _unit = self.unit_proxy.manager.get_obj(filters={"name": self._name_unit, "login": self._login_unit,
                                                         "user_id": self._user.id})
        self.assertEqual(self._name_unit, _unit.__dict__.get("name"),
                         msg="Имя юнита в БД не соответствует")
        self.assertEqual(self._login_unit, _unit.__dict__.get("login"),
                         msg="Логин юнита в БД не соответствует")

        # проверяем, что шифр пароля юнита сохранён корректно
        self.assertEqual(self._password_unit, self.unit_proxy.manager.decrypt_value(
                                                  username=self._login_user, password=self._password_user,
                                                  enc=_unit.__dict__.get("secret")
                                              ),
                         msg="Шифр пароля юнита в БД не соответствует")

        # проверяем, что добавление юнита с именем и логином, которые уже существуют у пользователя
        # вызывает исключение (связка имя + логин юнита + id пользователя должна быть уникальной)
        with self.assertRaisesRegex(Exception, ".*UNIQUE constraint failed: units.name, units.login, units.user_id.*"):
            self.unit_proxy.add_obj({
                "username": self._login_user,
                "password": self._password_user,
                "name": self._name_unit,
                "login": self._login_unit,
                "secret": self._password_unit,
                "user_id": self._user.id
            })

        # добавляем тестовому пользователю другой юнит с логином, отличным от ранее добавленного
        self.unit_proxy.add_obj({
            "username": self._login_user,
            "password": self._password_user,
            "name": self._name_unit,
            "login": "other login",
            "secret": self._password_unit,
            "user_id": self._user.id
        })

        # проверяем, что кол-во юнитов пользователя изменилось
        _units = self.unit_proxy.manager.get_objects(filters={"user_id": self._user.id})
        self.assertEqual(2, len(_units),
                         msg="Количество юнитов пользователя в БД не соответствует")

        # проверяем, что шифр одинаковых паролей у разных юнитов отличается
        _other_unit = self.unit_proxy.manager.get_obj(filters={"name": self._name_unit, "login": "other login",
                                                               "user_id": self._user.id})
        self.assertNotEqual(_unit.__dict__.get("secret"), _other_unit.__dict__.get("secret"),
                            msg="Шифры паролей разных юнитов совпали")
