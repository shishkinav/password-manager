import unittest
from db_manager import managers as db_sql
from pathlib import Path
from settings import FILE_TEST_DB


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


class TestDBManager(TestManager):
    def test_get_obj(self):
        """Проверка получения объекта модели"""
        # проверяем, что, если объект модели не определяется однозначно в соответствии
        # с указанными фильтрами, вызывается соответствующее исключение;
        # для этого добавляем тестовому пользователю два юнита, отличающийся только
        # логином, но при получении объекта в фильтрах логин не указываем
        self._add_test_unit()
        self._add_test_unit(login="other login")
        with self.assertRaisesRegex(Exception, ".*более одного экземпляра по указанным фильтрам",
                                    msg="Несоответствие проверки однозначности "
                                        "определения объекта модели"):
            self.unit_proxy.manager.get_obj(filters={
                "user_id": self._user.id,
            })


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

    def test_get_secret(self):
        """Проверка получения пароля юнита из БД через ProxyAction.get_secret"""
        # добавляем тестовому пользователю тестовый юнит
        self._add_test_unit()

        # проверяем, что метод get_secret возвращает расшифрованный пароль
        # юнита пользователя, указанного в фильтрах
        self.assertEqual(self._password_unit, self.unit_proxy.get_secret(filters={
                                                                         "username": self._login_user,
                                                                         "password": self._password_user,
                                                                         "name": self._name_unit,
                                                                         "login": self._login_unit
                                                                         }),
                         msg="Несоответствие проверки получения пароля юнита")

        # проверяем, что отсутствие в фильтре для метода get_secret
        # значения имени пользователя вызывает исключение
        with self.assertRaisesRegex(Exception, "Не все обязательные атрибуты метода переданы",
                                    msg="Несоответствие проверки атрибутов "
                                        "необходимых для расшифровки пароля юнита"):
            self.unit_proxy.get_secret(filters={
                "password": self._password_user,
                "name": self._name_unit,
                "login": self._login_unit
            })

        # проверяем, что отсутствие в фильтре для метода get_secret
        # значения пароля пользователя вызывает исключение
        with self.assertRaisesRegex(Exception, "Не все обязательные атрибуты метода переданы",
                                    msg="Несоответствие проверки атрибутов "
                                        "необходимых для расшифровки пароля юнита"):
            self.unit_proxy.get_secret(filters={
                "username": self._login_user,
                "name": self._name_unit,
                "login": self._login_unit
            })

        # проверяем, что, если экземпляр юнита для извлечения пароля
        # не определён, вызывается соответствующее исключение
        with self.assertRaisesRegex(Exception, "По указанным фильтрам не определён экземпляр юнита.*",
                                    msg="Несоответствие проверки фильтров при определении "
                                        "экземпляра юнита для извлечения пароля"):
            self.unit_proxy.get_secret(filters={
                "username": self._login_user,
                "password": self._password_user,
                "name": self._name_unit,
                "login": "nonexistent login"
            })

    def __get_control_user_with_unit(self):
        """Добавляем контрольного пользователя, добавляем ему тестовый юнит.
        Метод возвращает объект этого пользователя"""
        self.user_proxy.add_obj({
            "username": "control user",
            "password": self._password_user
        })
        _control_user = self.user_proxy.manager.get_obj(filters={"username": "control user"})
        self.unit_proxy.add_obj({
            "username": "control user",
            "password": self._password_user,
            "name": self._name_unit,
            "login": self._login_unit,
            "secret": self._password_unit,
            "user_id": _control_user.id,
            "category_id": self.category_proxy.get_prepared_category({"user_id": _control_user.id}).id
        })
        return _control_user

    def __checks_for_control_units(self, control_user_id):
        """Проверка атрибутов контрольных юнитов
        у тестового и контрольного пользователей"""
        # проверяем, что атрибуты контрольного юнита тестового пользователя не затронуты
        _default_category = self.category_proxy.get_prepared_category({"user_id": self._user.id})
        self.assertTrue(self.unit_proxy.check_obj(filters={
                                                  "name": self._name_unit,
                                                  "login": "control login",
                                                  "user_id": self._user.id,
                                                  "category_id": _default_category.id}),
                        msg="Наличие экземпляра контрольного юнита в БД не подтверждено")
        self.assertEqual(self._password_unit, self.unit_proxy.get_secret(filters={
                                                  "name": self._name_unit,
                                                  "login": "control login",
                                                  "username": self._login_user,
                                                  "password": self._password_user}),
                         msg="Пароль контрольного юнита в БД не соответствует")

        # проверяем, что кол-во юнитов контрольного пользователя не изменилось
        _control_user_units = self.unit_proxy.manager.get_objects(filters={"user_id": control_user_id})
        self.assertEqual(1, len(_control_user_units),
                         msg="Количество юнитов контрольного пользователя в БД не соответствует")

        # проверяем, что атрибуты юнита контрольного пользователя не затронуты
        _default_category = self.category_proxy.get_prepared_category({"user_id": control_user_id})
        self.assertTrue(self.unit_proxy.check_obj(filters={
                                                  "name": self._name_unit,
                                                  "login": self._login_unit,
                                                  "user_id": control_user_id,
                                                  "category_id": _default_category.id}),
                        msg="Наличие экземпляра юнита контрольного пользователя в БД не подтверждено")
        self.assertEqual(self._password_unit, self.unit_proxy.get_secret(filters={
                                                  "name": self._name_unit,
                                                  "login": self._login_unit,
                                                  "username": "control user",
                                                  "password": self._password_user}),
                         msg="Пароль юнита контрольного пользователя в БД не соответствует")

    def test_update_unit(self):
        """Проверка изменения атрибутов юнита пользователя в БД через ProxyAction.update_obj"""
        # добавляем тестовому пользователю тестовый юнит
        self._add_test_unit()

        # добавляем контрольного пользователя с аналогичным юнитом
        _control_user = self.__get_control_user_with_unit()

        # добавляем тестовому пользователю ещё один юнит для контроля
        self._add_test_unit(login="control login")

        # проверяем, что попытка изменить принадлежность
        # тестового юнита пользователю вызывает исключение
        with self.assertRaisesRegex(Exception, ".*корректировка принадлежности пользователю не производится",
                                    msg="Несоответствие при проверке ограничения на "
                                        "корректировку принадлежности юнита пользователю"):
            self.unit_proxy.update_obj(filters={"name": self._name_unit, "login": self._login_unit,
                                                "user_id": self._user.id},
                                       data={"user_id": _control_user.id})

        # изменяем ключевые атрибуты тестового юнита
        self.unit_proxy.update_obj(filters={"name": self._name_unit, "login": self._login_unit,
                                            "user_id": self._user.id},
                                   data={"name": "new name", "login": "new login"})

        # проверяем наличие экземпляра юнита тестового пользователя с новыми ключевыми атрибутами
        self.assertTrue(self.unit_proxy.check_obj(filters={
                                                  "name": "new name",
                                                  "login": "new login",
                                                  "user_id": self._user.id}),
                        msg="Наличие экземпляра юнита в БД не подтверждено")

        # изменяем пароль юнита, при этом в data передаём текущий пароль
        # пользователя, чтобы новый пароль юнита был зашифрован корректно
        self.unit_proxy.update_obj(filters={"name": "new name", "login": "new login",
                                            "user_id": self._user.id},
                                   data={"secret": "new secret",
                                         "current_password": self._password_user}
                                   )

        # проверяем, что изменение пароля юнита произошло корректно
        _unit = self.unit_proxy.manager.get_obj(filters={"name": "new name", "login": "new login",
                                                         "user_id": self._user.id})
        self.assertEqual("new secret", self.unit_proxy.get_secret(filters={"id": _unit.id,
                                                                           "username": self._login_user,
                                                                           "password": self._password_user}),
                         msg="Пароль юнита в БД не соответствует")

        # проверяем, что вызывается исключение, если при изменении
        # пароля юнита в data не передан текущий пароль пользователя
        with self.assertRaisesRegex(Exception, "Не передан пароль пользователя.*",
                                    msg="Несоответствие проверки атрибутов "
                                        "необходимых для шифрования пароля юнита"):
            self.unit_proxy.update_obj(filters={"name": "new name", "login": "new login",
                                                "user_id": self._user.id},
                                       data={"secret": "newer secret"})

        # изменяем другие неключевые атрибуты тестового юнита
        _new_category = self.category_proxy.get_prepared_category(
            {"user_id": self._user.id, "name": "new category"}
        )
        self.unit_proxy.update_obj(filters={"name": "new name", "login": "new login",
                                            "user_id": self._user.id},
                                   data={"url": "new url",
                                         "category_id": _new_category.id})

        # проверяем, что изменение атрибутов юнита произошло корректно
        _unit = self.unit_proxy.manager.get_obj(filters={"name": "new name", "login": "new login",
                                                         "user_id": self._user.id})
        self.assertEqual("new url", _unit.url,
                         msg="url юнита в БД не соответствует")
        self.assertEqual("new category", self.category_proxy.manager.get_obj(
                                             filters={"id": _unit.category_id}
                                         ).name,
                         msg="Категория юнита в БД не соответствует")

        # проверяем, что после всех изменений количество
        # юнитов у тестового пользователя не изменилось
        _units = self.unit_proxy.manager.get_objects(filters={"user_id": self._user.id})
        self.assertEqual(2, len(_units),
                         msg="Количество юнитов пользователя в БД не соответствует")

        # проверяем, что контрольные юниты не затронуты
        # изменениями тестового юнита
        self.__checks_for_control_units(_control_user.id)

    def test_delete_unit(self):
        """Проверка удаления юнита пользователя в БД через ProxyAction.delete_obj"""
        # добавляем тестовому пользователю тестовый юнит
        self._add_test_unit()

        # добавляем контрольного пользователя с аналогичным юнитом
        _control_user = self.__get_control_user_with_unit()

        # добавляем тестовому пользователю ещё один юнит для контроля
        self._add_test_unit(login="control login")

        # проверяем, что у тестового пользователя теперь 2 юнита
        _units = self.unit_proxy.manager.get_objects(filters={"user_id": self._user.id})
        self.assertEqual(2, len(_units),
                         msg="Количество юнитов пользователя в БД не соответствует")

        # удаляем тестовый юнит
        self.unit_proxy.delete_obj(filters={"name": self._name_unit, "login": self._login_unit,
                                            "user_id": self._user.id})

        # проверяем, что количество юнитов у тестового пользователя уменьшилось на 1
        _units = self.unit_proxy.manager.get_objects(filters={"user_id": self._user.id})
        self.assertEqual(1, len(_units),
                         msg="Количество юнитов пользователя в БД не соответствует")

        # проверяем, что удалённый юнит не определяется в БД
        self.assertFalse(self.unit_proxy.check_obj(
            filters={"name": self._name_unit, "login": self._login_unit,
                     "user_id": self._user.id})
        )

        # проверяем, что контрольные юниты не затронуты
        # удалением тестового юнита
        self.__checks_for_control_units(_control_user.id)


# чтобы увидеть содержимое тестовой БД по завершении тестов
# нужно раскомментировать строку ниже
# @unittest.skip("Temporary skip")
class TestZapDB(TestManager):
    def test_destroy_db(self):
        """Проверка удаления тестовой БД"""
        _err_msg = ""
        try:
            self.user_proxy.manager.destroy_db()
        except Exception as exc:
            _err_msg = "".join([exc.__class__.__name__, ": ", exc.__str__()])
        self.assertFalse(Path(FILE_TEST_DB).is_file(),
                         msg=f"Сбой удаления тестовой БД. {_err_msg}")
