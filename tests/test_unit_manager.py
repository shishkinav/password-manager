import os
import sqlite3
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_manager.models import Base, UnitManager, UserManager
from encryption_manager.models import get_secret_obj


class TestUnitManager(unittest.TestCase):
    _session_for_user = None
    _conn_sqlite = None
    _cursor_sqlite = None
    dir_path = 'tests' + os.sep + 'test_databases'
    file_path = dir_path + os.sep + 'users.sqlite'
    _test_user = 'test-user'
    _test_pwd_user = 'T_u!123'
    _test_login = 'test-login'
    _test_pwd_login = 'T_l!456'
    _test_name = 'test-name'

    def setUp(self) -> None:
        """Настройка окружения"""

        # Инициализация User
        # БД в памяти, без файла
        engine = create_engine(f'sqlite:///{self.file_path}', echo=False)

        # Создание файла БД, если его нет
        if not os.path.isdir(self.dir_path):
            os.makedirs(self.dir_path)
        Base.metadata.create_all(engine,
                                 tables=[
                                     Base.metadata.tables["users"],
                                     Base.metadata.tables["units"],
                                     Base.metadata.tables["categories"]
                                 ])

        self._session_for_user = sessionmaker(bind=engine)()
        
        # Добавление тестового пользователя
        user_obj = UserManager(self._session_for_user, self._test_user)
        user_obj.add_user(self._test_pwd_user)
        
        # Инициализация sqlite3
        self._conn_sqlite = sqlite3.connect(self.file_path)
        self._cursor_sqlite = self._conn_sqlite.cursor()

    def tearDown(self) -> None:
        """Чистка, после завершения тестов"""
        self._session_for_user.close()
        self._conn_sqlite.close()
        # Если для того, чтобы посмотреть, что в БД,
        # комментируем строку ниже. Не забываем удалить
        # файл БД вручную, перед следующим прогоном
        os.remove(self.file_path)

    @classmethod
    def tearDownClass(cls):
        """cleaning after finishing all tests"""
        os.rmdir(cls.dir_path)

    def test_add_unit(self):
        """
        check for add_unit
        """
        # add unit to DB
        unit_obj = UnitManager(self._session_for_user, self._test_user)
        unit_obj.add_unit(self._test_user, self._test_pwd_user, self._test_login, self._test_pwd_login)

        # checking query
        sql = "SELECT login, password FROM units WHERE login = ? and name = ?"
        self._cursor_sqlite.execute(sql, ([self._test_login, 'default']))
        result = self._cursor_sqlite.fetchall()
        
        # check that the result is only one line
        self.assertEqual(1, len(result))
        
        # check that 'login' field is correct
        self.assertEqual(self._test_login, result[0][0])
        
        # check that encrypted password for login is written correctly
        secret_obj = get_secret_obj(self._test_user, self._test_pwd_user)
        encrypted_pass = secret_obj.encrypt(self._test_pwd_login)
        self.assertEqual(secret_obj.decrypt(encrypted_pass), secret_obj.decrypt(result[0][1]))
        
        # сheck that exeption is occur when adding a unit that already exists
        exception_occur = False
        try:
            unit_obj.add_unit(self._test_user, self._test_pwd_user, self._test_login, self._test_pwd_login)
        except Exception:
            exception_occur = True
        self.assertEqual(True, exception_occur)

    def test_check_login(self):
        """
        check for check_login
        """
        # add unit to DB
        unit_obj = UnitManager(self._session_for_user, self._test_user)
        unit_obj.add_unit(self._test_user, self._test_pwd_user, self._test_login, self._test_pwd_login)

        # check that the check_login method confirms unit existence in DB by key login + default name
        unit_exist = False
        if unit_obj.check_login(self._test_login, name='default'):
            unit_exist = True
        self.assertEqual(True, unit_exist)

        # check that unit with 'non-existent-login' and default name doesn't exist in DB
        sql = "SELECT * FROM units WHERE login = ? and name = ?"
        self._cursor_sqlite.execute(sql, (['non-existent-login', 'default']))
        result = self._cursor_sqlite.fetchall()
        self.assertEqual([], result)

        # check that the check_login method confirms the absence of a unit that hasn't been added to DB
        unit_exist = False
        if unit_obj.check_login('non-existent-login', name='default', msg_need=None):
            unit_exist = True
        self.assertEqual(False, unit_exist)

    def test_get_password(self):
        """
        check for get_password
        """
        # add unit to DB
        unit_obj = UnitManager(self._session_for_user, self._test_user)
        unit_obj.add_unit(
            self._test_user, self._test_pwd_user,
            self._test_login, self._test_pwd_login, self._test_name
        )

        # check that get_password method returns correct password
        self.assertEqual(self._test_pwd_login, unit_obj.get_password(self._test_user, self._test_pwd_user,
                                                                     self._test_login, self._test_name))

    def test_delete_unit(self):
        """
        check for delete_unit
        """
        # add unit to DB
        unit_obj = UnitManager(self._session_for_user, self._test_user)
        unit_obj.add_unit(
            self._test_user, self._test_pwd_user,
            self._test_login, self._test_pwd_login, self._test_name
        )

        # delete unit from DB, than check that it isn't exists in DB
        unit_obj.delete_unit(self._test_login, self._test_name)
        self.assertEqual(False, True if unit_obj.check_login(self._test_login, self._test_name, msg_need=None) else False)

    def test_get_logins(self):
        """
        check for get_logins
        """
        class UnitsObj(dict):
            """
            extending functionality of dict class for dictionary of units
            """
            def __init__(self):
                self['logins'] = []
                self['name'] = []
                self['category'] = []
                self['url'] = []

            def append(self, logins, name='default', category='default', url=''):
                self['logins'].append(logins)
                self['name'].append(name)
                self['category'].append(category)
                self['url'].append(url)

        # create three dictionaries for collections of units with different categories
        units_default_category = UnitsObj()
        units_category1 = UnitsObj()
        units_category2 = UnitsObj()

        # union of created dictionaries
        units_all = UnitsObj()

        # create three collections of units with different categories with adding them to DB and dictionaries
        unit_obj = UnitManager(self._session_for_user, self._test_user)
        for i in '123':
            test_login = 'test-login-' + i
            test_pwd_login = 'T_l!-' + i * 3
            unit_obj.add_unit(
                self._test_user, self._test_pwd_user,
                test_login, test_pwd_login
            )
            units_default_category.append(test_login)
            units_all.append(test_login)

        for i in '456':
            test_login = 'test-login-' + i
            test_pwd_login = 'T_l!-' + i * 3
            test_name = 'test-name'
            test_category = 'category1'
            test_url = 'https://test.ru/'
            unit_obj.add_unit(
                self._test_user, self._test_pwd_user,
                test_login, test_pwd_login, test_name, category=test_category, url=test_url
            )
            units_category1.append(test_login, test_name, test_category, test_url)
            units_all.append(test_login, test_name, test_category, test_url)

        for i in '789':
            test_login = 'test-login-' + i
            test_pwd_login = 'T_l!-' + i * 3
            test_name = 'test-name-' + i
            test_category = 'category2'
            test_url = 'https://test.ru/' + i
            unit_obj.add_unit(
                self._test_user, self._test_pwd_user,
                test_login, test_pwd_login, test_name, category=test_category, url=test_url
            )
            units_category2.append(test_login, test_name, test_category, test_url)
            units_all.append(test_login, test_name, test_category, test_url)

        # check the equivalence of dictionary and result of get_logins method for all units
        self.assertEqual(units_all, unit_obj.get_logins())
        # check the equivalence of dictionary and result of get_logins method for units with 'default'-category
        self.assertEqual(units_default_category, unit_obj.get_logins(category='default'))
        # check the equivalence of dictionary and result of get_logins method for units with category1
        self.assertEqual(units_category1, unit_obj.get_logins(category='category1'))
        # check the equivalence of dictionary and result of get_logins method for units with category2
        self.assertEqual(units_category2, unit_obj.get_logins(category='category2'))

    def test_update_unit(self):
        """
        check for update_unit
        """
        # add unit to DB
        unit_obj = UnitManager(self._session_for_user, self._test_user)
        unit_obj.add_unit(
            self._test_user, self._test_pwd_user,
            self._test_login, self._test_pwd_login, self._test_name
        )

        # check that without a set of mutable attributes, the update_unit method doesn't change the unit
        unit_obj.update_unit(self._test_user, self._test_pwd_user, self._test_login, self._test_name)
        self.assertEqual(True, True if unit_obj.check_login(self._test_login, self._test_name) else False)

        # update unit
        new_login = 'new-login'
        new_pwd_login = 'new-password-for-login'
        new_url = 'https://test.ru/'
        new_name = 'new-name'
        unit_obj.update_unit(
            self._test_user, self._test_pwd_user, self._test_login, self._test_name,
            new_login, new_pwd_login, url=new_url, new_name=new_name
        )

        # checking query
        sql = "SELECT login, name, url FROM units WHERE login = ? and name = ? and url = ?"
        self._cursor_sqlite.execute(sql, ([new_login, new_name, new_url]))
        result = self._cursor_sqlite.fetchall()

        # check the equivalence of updated unit attributes and data from DB
        self.assertEqual(new_login, result[0][0])
        self.assertEqual(new_name, result[0][1])
        self.assertEqual(new_url, result[0][2])
        self.assertEqual(new_pwd_login, unit_obj.get_password(self._test_user, self._test_pwd_user,
                                                              new_login, new_name))

        # check that the unit with old attributes doesn't exist in DB
        self.assertEqual(False, True if unit_obj.check_login(self._test_login, self._test_name, msg_need=None) else False)

    def test_update_user(self):
        """
        check for update_user
        """
        user_obj = UserManager(self._session_for_user, self._test_user)

        # add unit to DB
        unit_obj = UnitManager(self._session_for_user, self._test_user)
        unit_obj.add_unit(
            self._test_user, self._test_pwd_user,
            self._test_login, self._test_pwd_login, self._test_name
        )

        # update username and password
        new_user = 'new-user'
        new_password = 'N_u!123'
        user_obj.update_user(self.file_path, self._test_pwd_user, new_user, new_password)

        # check that original user doesn't exist in DB
        self.assertEqual(False, user_obj.check_user(self._test_user))
        # check that new user exist in DB
        self.assertEqual(True, user_obj.check_user(new_user))
        # check that new password for new user is saved correctly
        user_obj = UserManager(self._session_for_user, new_user)
        self.assertEqual(True, user_obj.check_user_password(new_password))
        # check that unit from original user belongs now to new user and we can get its password
        unit_obj = UnitManager(self._session_for_user, new_user)
        self.assertEqual(self._test_pwd_login, unit_obj.get_password(new_user, new_password,
                                                                     self._test_login, self._test_name))

        # update username without changing password (the password must be stay on new_password)
        newer_user = 'newer-user'
        user_obj.update_user(self.file_path, new_password, newer_user)

        # check that parent user doesn't exist in DB
        self.assertEqual(False, user_obj.check_user(new_user))
        # check that newer user exist in DB
        self.assertEqual(True, user_obj.check_user(newer_user))
        # check that password for newer user doesn't changed
        user_obj = UserManager(self._session_for_user, newer_user)
        self.assertEqual(True, user_obj.check_user_password(new_password))
        # check that unit from parent user belongs now to newer user and we can get its password
        unit_obj = UnitManager(self._session_for_user, newer_user)
        self.assertEqual(self._test_pwd_login, unit_obj.get_password(newer_user, new_password,
                                                                     self._test_login, self._test_name))


if __name__ == '__main__':
    unittest.main()
