# Установка приложения:
# $ pipenv install -e .
#
# Создание установщика для Windows
# $ python setup.py bdist --format=msi
# Установщик в папке dist
from setuptools import setup

setup(
    name='saverpwd',
    version='1.1',
    py_modules=['cli'],
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        saverpwd=cli:cli
    ''',
)
