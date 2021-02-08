import unittest
from db_manager import managers as db_sql


class TestManager(unittest.TestCase):
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
        self.unit_proxy.delete_obj(filters={})
        self.category_proxy.delete_obj(filters={})
        self.user_proxy.delete_obj(filters={})

        # создаём тестового пользователя в БД
        self.user_proxy.add_obj({
            "username": self._login_user,
            "password": self._password_user
        })

        # получаем объект тестового пользователя к которому можем обращаться в последующих тестах
        self._user = self.user_proxy.manager.get_obj(filters={"username": self._login_user})

    @classmethod
    def tearDownClass(cls):
        """Удаление тестовой БД по завершении тестов"""
        # cls.user_proxy.manager.session.close_all()
        # cls.user_proxy.manager.destroy_db()

        # очищаем таблицы БД - временное решение по причине
        # SADeprecationWarning: The Session.close_all() method is deprecated and will be removed in a future release.
        cls.unit_proxy.delete_obj(filters={})
        cls.category_proxy.delete_obj(filters={})
        cls.user_proxy.delete_obj(filters={})

    def _add_test_unit(self, login=_login_unit):
        """Добавление тестового юнита тестовому пользователю в БД"""
        self.unit_proxy.add_obj({
            "username": self._login_user,
            "password": self._password_user,
            "name": self._name_unit,
            "login": login,
            "secret": self._password_unit,
            "user_id": self._user.id,  # объект тестового пользователя формируется в setUp-методе
            "category_id": self.category_proxy.get_prepared_category({"user_id": self._user.id}).id
        })


# @unittest.skip("Temporary skip")
class TestUserManager(TestManager):
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

    def test_check_user(self):
        """Проверка наличия/отсутствия экземпляра пользователя в БД через ProxyAction.check_obj"""
        # пользователь создан вызовом self.user_proxy.add_obj в setUp-методе
        # проверяем наличие экземпляра пользователя в БД
        self.assertTrue(self.user_proxy.check_obj(filters={"username": self._login_user}),
                        msg="Наличие экземпляра пользователя в БД не подтверждено")

        # проверяем, что метод check_obj подтверждает отсутствие экземпляра несуществующего пользователя
        self.assertFalse(self.user_proxy.check_obj(filters={"username": "nonexistent username"}),
                         msg="Несоответствие проверки отсутствия экземпляра пользователя в БД")

    def test_check_user_password(self):
        """Проверка наличия в БД пользователя с указанными именем и паролем через ProxyAction.check_user_password"""
        # пользователь создан вызовом self.user_proxy.add_obj в setUp-методе
        # проверяем наличие в БД пользователя с указанными именем и паролем
        self.assertTrue(self.user_proxy.check_user_password(
                        self._login_user, self._password_user),
                        msg="Наличие пользователя в БД с указанными именем и паролем не подтверждено")

        # проверяем, что метод check_user_password подтверждает отсутствие пользователя
        # при несоответствии имени или пароля
        self.assertFalse(self.user_proxy.check_user_password(
                         "nonexistent username", self._password_user),
                         msg="Несоответствие проверки отсутствия пользователя в БД")
        self.assertFalse(self.user_proxy.check_user_password(
                         self._login_user, "nonexistent password"),
                         msg="Несоответствие проверки отсутствия пользователя в БД")

    def test_add_next_users(self):
        """Проверка создания нескольких пользователей в БД через ProxyAction.add_obj"""
        # первый пользователь создан вызовом self.user_proxy.add_obj в setUp-методе

        # проверяем, что добавление пользователя с логином уже существующего пользователя
        # вызывает исключение (имя пользователя должно быть уникальным)
        with self.assertRaisesRegex(Exception, ".*UNIQUE constraint failed: users.username.*",
                                    msg="Несоответствие ограничения таблицы пользователей в БД"):
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

        # проверяем, что для пользователей с одинаковыми паролями, но разными именами
        # хэши в поле "password", сохранённые в БД, отличаются
        _other_user = self.user_proxy.manager.get_obj(filters={"username": "other username"})
        self.assertNotEqual(self._user.__dict__.get("password"), _other_user.__dict__.get("password"),
                            msg="Различие хэшей паролей пользователей в БД не подтверждено")

    def __user_checks_after_update_user(self, old_username, old_password=None, new_username=None, new_password=None):
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

    def __unit_checks_after_update_user(self, new_username=TestManager._login_user,
                                        new_password=TestManager._password_user):
        """Проверка наличия экземпляров и атрибутов юнитов после изменения
        атрибутов пользователя с применением ProxyAction.update_obj"""
        # проверяем, что количество юнитов у пользователя не изменилось
        _units = self.unit_proxy.manager.get_objects(filters={"user_id": self._user.id})
        self.assertEqual(2, len(_units),
                         msg="Количество юнитов пользователя в БД не соответствует")

        # проверяем, что юниты пользователя идентифицируются по ключу name + login + user_id
        self.assertTrue(self.unit_proxy.check_obj(filters={"name": self._name_unit, "login": self._login_unit,
                                                           "user_id": self._user.id}),
                        msg="После изменения атрибутов пользователя его юнит не идентифицируется")
        self.assertTrue(self.unit_proxy.check_obj(filters={"name": self._name_unit, "login": "other login",
                                                           "user_id": self._user.id}),
                        msg="После изменения атрибутов пользователя его юнит не идентифицируется")

        # проверяем, что пароли юнитов перешифрованы корректно и соответствуют заданным при создании юнитов
        self.assertEqual(self._password_unit, self.unit_proxy.get_secret(filters={
                                                  "username": new_username,
                                                  "password": new_password,
                                                  "name": self._name_unit,
                                                  "login": self._login_unit
                                              }),
                         msg="После изменения атрибутов пользователя его пароль перешифрован некорректно")
        self.assertEqual(self._password_unit, self.unit_proxy.get_secret(filters={
                                                  "username": new_username,
                                                  "password": new_password,
                                                  "name": self._name_unit,
                                                  "login": "other login"
                                              }),
                         msg="После изменения атрибутов пользователя его пароль перешифрован некорректно")

    def __add_units_before_test_update_user(self):
        """Для проверки результатов обновления атрибутов тестового пользователя добавляем
        ему юниты, поскольку изменение этих атрибутов влияет на ключ шифра пароля юнита"""
        self._add_test_unit()
        self._add_test_unit(login="other login")

    def test_update_username(self):
        """Проверка изменения имени пользователя в БД через ProxyAction.update_obj"""
        self.__add_units_before_test_update_user()

        # Изменяем имя пользователя
        self.user_proxy.update_obj(filters={"username": self._login_user},
                                   data={
            "username": "new_username",
            "current_password": self._password_user  # пароль мы не
            # меняем, но передаём текущее значение, чтобы изменить
            # хэш пароля пользователя и перешифровать пароли юнитов
        })

        # проверяем результат изменения для экземпляра пользователя
        self.__user_checks_after_update_user(old_username=self._login_user, old_password=self._password_user,
                                             new_username="new_username")

        # проверяем результат изменения для юнитов пользователя
        self.__unit_checks_after_update_user(new_username="new_username")

    def test_update_user_password(self):
        """Проверка изменения пароля пользователя в БД через ProxyAction.update_obj"""
        self.__add_units_before_test_update_user()

        # Изменяем пароль пользователя
        self.user_proxy.update_obj(filters={"username": self._login_user},
                                   data={
            "current_password": self._password_user,  # передаём текущее значение пароля пользователя,
                                                      # чтобы перешифровать пароли юнитов
            "password": "new_password"
        })

        # проверяем результат изменения для экземпляра пользователя
        self.__user_checks_after_update_user(old_username=self._login_user,
                                             new_password="new_password")

        # проверяем результат изменения для юнитов пользователя
        self.__unit_checks_after_update_user(new_password="new_password")

    def test_update_username_and_password(self):
        """Проверка одновременного изменения имени и пароля пользователя в БД через ProxyAction.update_obj"""
        self.__add_units_before_test_update_user()

        # Изменяем имя пользователя и пароль одновременно
        self.user_proxy.update_obj(filters={"username": self._login_user},
                                   data={
            "username": "new_username",
            "current_password": self._password_user,  # передаём текущее значение пароля пользователя,
                                                      # чтобы перешифровать пароли юнитов
            "password": "new_password"
        })

        # проверяем результат изменения для экземпляра пользователя
        self.__user_checks_after_update_user(old_username="other_username",
                                             new_username="new_username", new_password="new_password")

        # проверяем результат изменения для юнитов пользователя
        self.__unit_checks_after_update_user(new_username="new_username", new_password="new_password")

    @unittest.skip("Temporary skip")
    def test_delete_user(self):
        """Проверка удаления пользователя в БД через ProxyAction.delete_obj"""
        # проверяем наличие экземпляра пользователя в БД до удаления
        self.assertTrue(self.user_proxy.check_obj(filters={"id": self._user.id}),
                        msg="Наличие экземпляра пользователя в БД не подтверждено")

        # добавляем пользователю юнит для проверки каскадного удаления связанных объектов
        self._add_test_unit()

        # проверяем количество юнитов тестового пользователя в БД
        _units = self.unit_proxy.manager.get_objects(filters={"user_id": self._user.id})
        self.assertEqual(1, len(_units),
                         msg="Количество юнитов пользователя в БД не соответствует")

        # проверяем что с добавлением юнита у тестового пользователя
        # появилась связанная категория юнита в БД
        _categories = self.category_proxy.manager.get_objects(filters={"user_id": self._user.id})
        self.assertEqual(1, len(_categories),
                         msg="Количество категорий юнитов пользователя в БД не соответствует")

        # удаляем пользователя
        self.user_proxy.delete_obj(filters={"id": self._user.id})

        # проверяем отсутсвие экземпляра пользователя в БД после удаления
        self.assertFalse(self.user_proxy.check_obj(filters={"id": self._user.id}),
                         msg="Выявлено наличие экземпляра пользователя в БД после его удаления")

        # проверяем, что после удаления пользователя удалён и его юнит
        _units = self.unit_proxy.manager.get_objects(filters={"user_id": self._user.id})
        self.assertEqual(0, len(_units),
                         msg="После удаления пользователя связанный с ним юнит не удалён")

        # проверяем, что после удаления пользователя удалена и связанная с ним категория юнитов
        _categories = self.category_proxy.manager.get_objects(filters={"user_id": self._user.id})
        self.assertEqual(0, len(_categories),
                         msg="После удаления пользователя связанная с ним"
                             " категория юнитов не удалена")


# @unittest.skip("Temporary skip")
class TestUnitManager(TestManager):
    def test_add_unit(self):
        """Проверка создания юнита пользователя в БД через ProxyAction.add_obj"""
        # добавление тестового юнита с предустановленными атрибутами
        # вызовом self.unit_proxy.add_obj вынесено в отдельный метод:
        self._add_test_unit()

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

    def test_check_unit(self):
        """Проверка наличия/отсутствия экземпляра юнита в БД через ProxyAction.check_obj"""
        # добавляем тестовому пользователю тестовый юнит
        self._add_test_unit()

        # проверяем наличие экземпляра юнита в БД
        self.assertTrue(self.unit_proxy.check_obj(filters={
                                                  "name": self._name_unit,
                                                  "login": self._login_unit,
                                                  "user_id": self._user.id}),
                        msg="Наличие экземпляра юнита в БД не подтверждено")

        # проверяем, что метод check_obj подтверждает отсутствие экземпляра несуществующего юнита
        self.assertFalse(self.unit_proxy.check_obj(filters={
                                                  "name": self._name_unit,
                                                  "login": "nonexistent login",
                                                  "user_id": self._user.id}),
                         msg="Несоответствие проверки отсутствия экземпляра юнита в БД")

    def test_add_next_units(self):
        """Проверка создания нескольких юнитов пользователей в БД через ProxyAction.add_obj"""
        # добавляем тестовому пользователю первый юнит
        self._add_test_unit()

        # проверяем, что добавление юнита с именем и логином, которые уже существуют у пользователя
        # вызывает исключение (связка имя + логин юнита + id пользователя должна быть уникальной)
        with self.assertRaisesRegex(Exception,
                                    ".*UNIQUE constraint failed: units.name, units.login, units.user_id.*",
                                    msg="Несоответствие ограничения таблицы юнитов в БД"):
            self._add_test_unit()

        # добавляем тестовому пользователю другой юнит с логином, отличным от ранее добавленного
        self._add_test_unit(login="other login")

        # проверяем, что кол-во юнитов пользователя изменилось
        _units = self.unit_proxy.manager.get_objects(filters={"user_id": self._user.id})
        self.assertEqual(2, len(_units),
                         msg="Количество юнитов пользователя в БД не соответствует")

        # проверяем, что шифр одинаковых паролей у разных юнитов отличается
        _unit = self.unit_proxy.manager.get_obj(filters={"name": self._name_unit, "login": self._login_unit,
                                                         "user_id": self._user.id})
        _other_unit = self.unit_proxy.manager.get_obj(filters={"name": self._name_unit, "login": "other login",
                                                               "user_id": self._user.id})
        self.assertNotEqual(_unit.__dict__.get("secret"), _other_unit.__dict__.get("secret"),
                            msg="Шифры паролей разных юнитов совпали")
