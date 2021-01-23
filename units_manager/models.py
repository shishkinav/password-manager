import datetime as dt
from typing import List
from settings import TIME_SESSION_CLOSE


class UnitsComposition:
    """Класс компоновки юнитов на выдачу
    
    Пока общими словами описываю данные, т.к. сопоставление точек соприкосновения
    мы ещё не делали

    IN: 
        Получает на вход выгруженные данные из БД
    OUT:
        отдаёт на выходе json, собрав его в зависимости от наших потребностей,
        которые возникнут по коду
    """
    _data_obj = {}

    def __init__(self, data_obj=None):
        if data_obj is None:
            data_obj = {}
        self._data_obj = data_obj

    def prepare_data(self, data_obj=None):
        """Подготовка списка логинов"""
        if not data_obj:
            data_obj = self._data_obj
        for key, lst in data_obj.items():
            # Ищем максимальную длину строки в столбце
            max_len = len(key)
            for item in lst:
                if len(item) > max_len:
                    max_len = len(item)

            # Добавляем пробелы в столбцы, для одинаковой длины столбцов
            for i in range(len(lst)):
                data_obj[key][i] = data_obj[key][i].ljust(max_len+1)
            data_obj[key].insert(0, key.ljust(max_len+1))

        self._data_obj = data_obj

    def make_str_logins(self, flags=None, data_obj=None):
        """Печатем логины с флагами"""
        if not flags:
            flags = {}
        if not data_obj:
            data_obj = self._data_obj

        res_str = ""
        is_first_line = True

        for i in range(len(data_obj['logins'])):
            str_for_print = data_obj['logins'][i]
            delimiter_str = "-" * len(data_obj['logins'][i])
            for key in data_obj.keys():
                if key in flags.keys() and flags[key]:
                    str_for_print += '| ' + data_obj[key][i]
                    delimiter_str += '+-' + '-' * len(data_obj[key][i])
            res_str += str_for_print + '\n'
            if is_first_line:
                res_str += delimiter_str + '\n'
                is_first_line = False

        return res_str.strip()


class TimeoutController:
    """Класс проверки истечения времени активной сессии
    
    IN:
        Получаем на вход объект БД с атрибутом времени посещения
    OUT:
        Если delta между текущим временем и полученным в атрибуте БД больше
        _default_time_session, то возвращаем False; если меньше, то возвращаем
        True и запрашиваем обновление времени в БД по этому объекту
    """
    _default_time_session = TIME_SESSION_CLOSE

    def check_time_permission(self, check_datetime):
        """
        проверка дельты между переданным datetime и текущим,
        возвращаем True, если дельта меньше дефолтного времени, отведённого на длительность сессии, иначе False
        """
        return dt.datetime.today() - check_datetime \
            < dt.timedelta(seconds=self._default_time_session)


class PrintComposition:
    """Класс формирования единой выдачи"""
    # _boxs = {
    #     "users": ['username'],
    #     "units": ['name', 'login']
    # }

    def get_format_row(self, ) -> str:
        """[obj, obj]"""
        # получение формата 
        pass

    def prepare_data(self, data_objects: List, box_attrs: List = []) -> List[str]:
        # формирование строки заголовка и строки данных по формату
        for obj in data_objects:
            [
                print(
                    getattr(obj, name_attr, None)
                ) for name_attr in box_attrs
            ]