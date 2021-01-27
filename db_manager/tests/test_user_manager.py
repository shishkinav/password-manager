import unittest
from db_manager import managers as db_sql


class TestUserManager(unittest.TestCase):
    _login_user = "temp"
    _password_user = "temp1234!@#$"
    user_proxy = db_sql.ProxyAction(db_sql.UserManager(prod_db=False))

    def setUp(self):
        """Подготовка перед каждым тестом"""
        # очищаем таблицу пользователей в БД
        self.user_proxy.delete_obj(filters={})

        # создаём тестового пользователя в БД
        self.user_proxy.add_obj({
            "username": self._login_user,
            "password": self._password_user
        })

    @classmethod
    def tearDownClass(cls):
        """Удаление тестовой БД по завершении тестов"""
        # cls.user_proxy.manager.session.close_all()
        # cls.user_proxy.manager.destroy_db()

        # очищаем использованную при тестировании таблицу БД - временное решение по причине
        # SADeprecationWarning: The Session.close_all() method is deprecated and will be removed in a future release.
        cls.user_proxy.delete_obj(filters={})

    def test_add_user(self):
        """Проверка создания пользователя в БД через ProxyAction.add_obj"""
        # пользователь создан вызовом self.user_proxy.add_obj в setUp-методе

        # проверяем количество пользователей в БД
        _users = self.user_proxy.manager.get_objects(filters={})
        self.assertEqual(1, len(_users),
                         msg="Количество пользователей в БД не соответствует")

        # проверяем, что имя пользователя сохранено корректно
        _user = self.user_proxy.manager.get_obj(filters={"username": self._login_user})
        self.assertEqual(self._login_user, _user.__dict__.get("username"),
                         msg="Имя пользователя в БД не соответствует")

        # проверяем, что пароль пользователя сохранён корректно, а именно:
        # в поле password сохранён хэш(username + password)
        pass_hash = self.user_proxy.manager.generate_hash(self._login_user + self._password_user)
        self.assertEqual(pass_hash, _user.__dict__.get("password"),
                         msg="Хэш пароля пользователя в БД не соответствует")

        # проверяем, что добавление пользователя с логином уже существующего пользователя
        # вызывает исключение (имя пользователя должно быть уникальным)
        with self.assertRaisesRegex(Exception, ".*UNIQUE constraint failed: users.username.*"):
            self.user_proxy.add_obj({
                "username": self._login_user,
                "password": "other password"
            })

        # проверяем, что для пароля пользователя нет ограничения уникальности:
        # добавляем другого пользователя с логином, отличным от ранее добавленного
        self.user_proxy.add_obj({
            "username": "other username",
            "password": self._password_user
        })

        # проверяем, что кол-во пользователей изменилось
        _users = self.user_proxy.manager.get_objects(filters={})
        self.assertEqual(2, len(_users),
                         msg="Количество пользователей в БД не соответствует")

        # проверяем, что имя нового пользователя сохранено корректно
        _other_user = self.user_proxy.manager.get_obj(filters={"username": "other username"})
        self.assertEqual("other username", _other_user.__dict__.get("username"),
                         msg="Имя пользователя в БД не соответствует")

        # проверяем, что пароль нового пользователя сохранён корректно:
        pass_hash = self.user_proxy.manager.generate_hash("other username" + self._password_user)
        self.assertEqual(pass_hash, _other_user.__dict__.get("password"),
                         msg="Хэш пароля пользователя в БД не соответствует")

        # проверяем, что для пользователей с одинаковыми паролями, но разными именами
        # хэши в поле "password", сохранённые в БД, отличаются
        self.assertNotEqual(_user.__dict__.get("password"), _other_user.__dict__.get("password"))

    def __checks_after_update_user(self, old_username, old_password=None, new_username=None, new_password=None):
        """Проверка наличия экземпляров и атрибутов пользователей после применения ProxyAction.update_obj"""
        if new_username:
            # проверяем, что пользователь со старым имененем отсутствует в БД
            self.assertFalse(self.user_proxy.check_obj(filters={"username": old_username}),
                             msg="Имя пользователя при изменении не поменялось")

            # проверяем, что пользователь с новым имененем присутствует в БД
            self.assertTrue(self.user_proxy.check_obj(filters={"username": new_username}),
                            msg="После изменения пользователь не числится в БД")

            # валидация атрибутов изменённого пользователя
            if new_password:
                self.assertTrue(self.user_proxy.check_user_password(new_username, new_password),
                                msg="После изменения имя и пароль пользователя в БД не соответствуют")
            else:
                self.assertIsNotNone(old_password,
                                     msg='Для проверки атрибутов пользователя после изменения не передан пароль')
                self.assertTrue(self.user_proxy.check_user_password(new_username, old_password),
                                msg="После изменения имя и пароль пользователя в БД не соответствуют")
        else:
            # проверяем, что пользователь со старым имененем присутствует в БД
            self.assertTrue(self.user_proxy.check_obj(filters={"username": old_username}),
                            msg="После изменения пользователь не числится в БД")

            # валидация атрибутов пользователя после изменения
            self.assertIsNotNone(new_password,
                                 msg='Для проверки атрибутов пользователя после изменения не передан пароль')
            self.assertTrue(self.user_proxy.check_user_password(old_username, new_password),
                            msg="После изменения пароля имя и пароль пользователя в БД не соответствуют")

    def test_update_user(self):
        """Проверка изменения атрибутов пользователя без юнитов в БД через ProxyAction.update_obj"""
        # 1. Изменяем имя пользователя
        update_result = self.user_proxy.update_obj(filters={"username": self._login_user}, data={
                            "username": "other_username",
                            "password": self._password_user  # пароль мы не меняем, но передаём его, чтобы изменить хэш
                        })
        self.assertTrue(update_result,
                        msg="Изменение имени пользователя с помощью ProxyAction.update_obj не выполнено")
        # проверяем результат изменения
        self.__checks_after_update_user(old_username=self._login_user, old_password=self._password_user,
                                        new_username="other_username")

        # 2. Изменяем пароль пользователя
        update_result = self.user_proxy.update_obj(filters={"username": "other_username"}, data={
                            "password": "other_password"
                        })
        self.assertTrue(update_result,
                        msg="Изменение пароля пользователя с помощью ProxyAction.update_obj не выполнено")
        # проверяем результат изменения
        self.__checks_after_update_user(old_username="other_username",
                                        new_password="other_password")

        # 3. Изменяем имя пользователя и пароль одновременно
        update_result = self.user_proxy.update_obj(filters={"username": "other_username"}, data={
                            "username": "new_username",
                            "password": "new_password"
                        })
        self.assertTrue(update_result,
                        msg="Изменение имени и пароля пользователя с помощью ProxyAction.update_obj не выполнено")
        # проверяем результат изменения
        self.__checks_after_update_user(old_username="other_username",
                                        new_username="new_username", new_password="new_password")
