import datetime as dt
from typing import List
from settings import TIME_SESSION_CLOSE
from operator import attrgetter
from db_manager.models import Base


# deprecated
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
    def __get_format_row(self, count: int) -> str:
        """Получение стандартного форматирования для строки вывода""" 
        return "{:^30}" * count

    def __sorted_by_attrs(self, data_objects: List[Base], sort_values_attrs: List[str],
                          reverse=False) -> List:
        """Сортировка объектов по указанному атрибуту.
        Возрастающая или убывающая зависит от reverse"""
        return sorted(data_objects, key=attrgetter(*sort_values_attrs), reverse=reverse)

    def prepare_data(self, data_objects: List[Base], box_attrs: List[str],
                     sort_values_attrs: List[str] = [], reverse=False) -> List[str]:
        """Сборка списка строк для вывода по переданным данным
        Input:
            data_objects - список экземпляров объектов из БД
            box_attrs - список string (атрибутов объекта), которые будут участвовать в выводе
            sort_values_attrs - список string (названий атрибутов объекта), по которым будет
                производиться сортировка (при указании более одного string сначала применяется 
                сортировка по первому указанному атрибуту, вторичная сортировка по второму и т.д.)
            reverse - порядок сортировки списка (True - по убыванию, False - по возрастанию)
            
        Если sort_values_attrs не переданы, сортировка будет произведена по первому атрибуту, 
            который передан в box_attrs"""
        if not sort_values_attrs:
            sort_values_attrs = [box_attrs[0], ]
        format_row = self.__get_format_row(len(box_attrs))
        _data_external = [format_row.format(*box_attrs)]
        data_sorted = self.__sorted_by_attrs(
            data_objects=data_objects,
            sort_values_attrs=sort_values_attrs,
            reverse=reverse
        )
        for obj in data_sorted:
            massive_value = [getattr(obj, name_attr, 'empty') for name_attr in box_attrs]
            if 'empty' in massive_value:
                raise Exception
            _data_external.append(
                format_row.format(*massive_value)
            )
        return _data_external
