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
    _composition = PrintComposition()

    def setUp(self) -> None:
        # очищаем таблицу пользователей в БД
        self.user_proxy.delete_obj(filters={})

        # создаём тестовых пользователей в БД
        for _username, _password in (
            (self._login_user, self._password_user),
            ("second", "second_password"),
            ('special', 'my_password'),
            ('bamby', 'hide_password')
        ):
            self.user_proxy.add_obj({
                "username": _username,
                "password": _password
            })

    @classmethod
    def tearDownClass(cls):
        """Очистка тестовой базы"""
        cls.user_proxy.manager.session.close_all()
        cls.user_proxy.manager.destroy_db()

    def test_raises_exception(self):
        """Проверка возбуждения исключений при некорректной передаче значений
        атрибутов, участвующих в подготовке списка строк"""
        _users = self.user_proxy.manager.get_objects(filters={})

        with self.assertRaises(Exception):
            self._composition.prepare_data(data_objects=_users, box_attrs=["id", "username", "login"])

    def test_print_users(self):
        """Количественная проверка возвращаемого списка после подготовки
        данных на вывод"""
        
        _users = self.user_proxy.manager.get_objects(filters={})
        
        data = self._composition.prepare_data(
            data_objects=_users, 
            box_attrs=["id", "username"]
            )
        
        self.assertTrue(len(data) == 5,
            msg="Количество строк в подготовленных данных не соответствует")

    def test_ascending_sort(self):
        """Проверка сортировки по возрастанию"""
        _users = self.user_proxy.manager.get_objects(filters={})
        data = self._composition.prepare_data(
                data_objects=_users, 
                box_attrs=["id", "username"],
                sort_values_attrs=['username']
            )
        for i, s in enumerate(('bamby', 'second', 'special', 'temp'), start=1):
            self.assertTrue(
                s in data[i],
                msg=f'Порядок сортировки нарушен: текст "{s}" должен присутствовать в строке '
                    f'c порядковым номером {i} и значением "{data[i]}"'
            )

    def test_descending_sort(self):
        """Проверка сортировки по убыванию"""
        _users = self.user_proxy.manager.get_objects(filters={})
        data = self._composition.prepare_data(
                data_objects=_users, 
                box_attrs=["id", "username"],
                sort_values_attrs=['username'],
                reverse=True
            )

        for i, s in enumerate(('temp', 'special', 'second', 'bamby'), start=1):
            self.assertTrue(
                s in data[i],
                msg=f'Порядок сортировки нарушен: текст "{s}" должен присутствовать в строке '
                    f'c порядковым номером {i} и значением "{data[i]}"'
            )