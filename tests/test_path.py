import unittest
from main import db_append
import os

class Test_get_path(unittest.TestCase):


    def test_get_path_databases(self):
        """Тестируем наличие папки darabases в рабочем каталоге"""
        self.assertEqual(os.path.exists("databases"), True)



    def test_get_path_username(self):
        """Тестируем наличие папки с именем юзера в папке databases"""
        username = ['pavel']
        self.assertEqual(os.listdir("databases"), username)

if __name__ == '__main__':
    unittest.main()