import unittest
from main import get_hash
import hashlib

""" Тест функции get_hash. Задаем вручную пароль 1 и сравниваем с заранее определнном для него хешем"""

class Test_get_hash(unittest.TestCase):


    def test_get_hashe(self):
        password = '1'
        password_code = password.encode("utf-8")
        self.assertEqual(get_hash(password_code), '6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b')

if __name__ == '__main__':
    unittest.main()
