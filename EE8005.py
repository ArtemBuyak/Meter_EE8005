import serial
import time
from abc import abstractmethod


class Meters:
    """Базовый класс для всех счетчиков."""

    def __init__(self, com_port, meter_id):
        """
        Инициализация счетчика.
        :param com_port: COM-порт на котороый подключен счетчик. Объект типа Serial.
        :param meter_id: Заводской номер счетчика.
        """
        self.__energy1 = 0.0
        self.__energy2 = 0.0
        self.__energy3 = 0.0
        self.__energy4 = 0.0
        self.energy_summ = 0.0


        self.com_port = com_port
        self.meter_id = meter_id
        """Промежуточный буфер для хранения ответа от счетчика"""
        self.buff = []

    @property
    def energy_t1(self):
        """Показания счетчика по тарифу 1."""
        return self.__energy1

    @energy_t1.setter
    def energy_t1(self, energy_t1):
        print(energy_t1)
        """
        Проверка и запись свойства.
        """
        assert energy_t1 >= 0, "Energy must be non-negative"
        self.__energy1 = energy_t1

    @property
    def energy_t2(self):
        """Показания счетчика по тарифу 2."""
        return self.__energy2

    @energy_t2.setter
    def energy_t2(self, energy_t2):
        """
        Проверка и запись свойства.
        """
        assert energy_t2 >= 0, "Energy must be non-negative"
        self.__energy2 = energy_t2

    @property
    def energy_t3(self):
        """Показания счетчика по тарифу 3."""
        return self.__energy3

    @energy_t3.setter
    def energy_t3(self, energy_t3):
        """
        Проверка и запись свойства.
        """
        assert energy_t3 >= 0, "Energy must be non-negative"
        self.__energy3 = energy_t3

    @property
    def energy_t4(self):
        """Показания счетчика по тарифу 4."""
        return self.__energy4

    @energy_t4.setter
    def energy_t4(self, energy_t4):
        """
        Проверка и запись свойства.
        """
        assert energy_t4 >= 0, "Energy must be non-negative"
        self.__energy4 = energy_t4

    @property
    def energy_summ(self):
        """Сумма показаний счетчика по всем тарифам."""
        return self.__energy_summ

    @energy_summ.setter
    def energy_summ(self, energy_summ):
        """
        Проверка и запись свойства.
        """
        assert energy_summ >= 0, "Energy must be non-negative"
        self.__energy_summ = energy_summ

    def read_answer(self):
        """
        Чтение, первичная обработка, и сохранение принятой последовательности в буфер.
        Метод может использоваться для большинства счетчиков без переопределения.
        """
        self.buff.clear()
        while self.com_port.read():
            data = self.com_port.readline()
            for character in data:
                self.buff.append(hex(character))  # Преобразуем в шестнадцатиричный код.

    @abstractmethod
    def request_current_energy(self):
        """
        Отправка запроса на чтение текущих показаний энергии.
        Метод абстрактный, т.к. запрос у каждого счетчика свой, в соответствии с протоколом.
        :return: Ничего не возвращает.
        """

    @abstractmethod
    def process_data_current_energy(self):
        """
        Обработка ответа от счетчика в соответствии с протоколом обмена.
        Записывет результаты в свойства energy_t1, ... energy_t4, energy_summ класса.
        Метод абстрактный т.к. зависит от протокола конкретного счетчика.
        :return: Ничего не возвращает.
        """


class EE8003Meter(Meters):
    """Счетчик ЭЭ8003/ЭЭ8005. Производства ОАО «ВЗЭП» г. Витебск."""

    def request_current_energy(self):
        """
        Отправка запроса на чтение текущих показаний энергии в соответствии с протоколом.
        :return:
        """
        if self.com_port.is_open:
            """Байт инициализации."""
            self.com_port.write(b'\x99')
            """Задержка 0,1 сек."""
            time.sleep(0.1)
            """Запрос текущих показаний в соответствии с протоколом обмена."""
            bytearr = bytearray()
            self.id_to_bcd(bytearr)
            self.crc_id(bytearr)
            bytearr += b'\x01\x00\x00\x01\x01\x00\x00\x01\x00\xaa\xa0\x05\x41\x18'
            self.com_port.write(bytearr)

    def process_data_current_energy(self):
        """
        Обработка ответа от счетчика в соответствии с протоколом обмена.
        Записывет результаты в свойства energy_t1, ... energy_t4, energy_summ класса.
        :return:
        """
        self.energy_t1 = self.bcd_to_int(58)
        self.energy_t2 = self.bcd_to_int_t2(63)
        self.energy_t3 = self.bcd_to_int(69)
        self.energy_t4 = self.bcd_to_int(74)
        self.energy_summ = round((self.energy_t1 + self.energy_t2 + self.energy_t3 + self.energy_t4), 2)

    def bcd_to_int(self, start):
        """
        Преобразование числа из BCD в обычное десятичное.
        :param start: Стартовый байт.
        :return: Результат в десятичном виде.
        """
        return int(
            str(self.buff[start + 3])[2:] + str(self.buff[start + 2])[2:] + str(self.buff[start + 1])[2:] + str(
                self.buff[start])[2:]) / 100

    def bcd_to_int_t2(self, start):
        """
        Преобразование числа из BCD в обычное десятичное.
        Отдельная ф-я для 2-го тарифа, т.к. в этом блоке есть байт промежуточной контрольной суммы.
        :param start: Стартовый байт.
        :return: Результат в десятичном виде.
        """
        return int(
            str(self.buff[start + 4])[2:] + str(self.buff[start + 3])[2:] + str(self.buff[start + 2])[2:] + str(
                self.buff[start])[2:]) / 100

    def id_to_bcd(self, bytearr):
        """
        Преобразует заводской номер счетчика в формат для передачи в соотв. с протоколом.
        :return:
        """
        bytearr.append(int(str(self.meter_id)[4:6], 16))
        bytearr.append(int(str(self.meter_id)[2:4], 16))
        bytearr.append(int(str(self.meter_id)[0:2], 16))

    @staticmethod
    def crc_id(bytearr):
        """
        Вычисление контрольной суммы заводского номера счетчика в соотв. с протоколом.
        :return:
        """
        crc = bytearr[0] + bytearr[1] + bytearr[2]
        crc = str(hex(crc))[-2:]
        bytearr.append(int(crc, 16))

    def read_current_energy(self):
        """
        Последовательный вызов функций для чтения текущих показаний со счетчика.
        :return:
        """
        self.request_current_energy()
        self.read_answer()
        self.process_data_current_energy()


serial_port = serial.Serial("COM7", 19200)
serial_port.timeout = 1

meter1_ee8003 = EE8003Meter(serial_port, 409969)  # Заводской номер счетчика 409969
meter1_ee8003.read_current_energy()


text = str('Показания счетчика ЭЭ8005:\nТариф 1: {0} кВт\nТариф 2: {1} кВт\nТариф 3: {2} кВт'
           '\nТариф 4: {3} кВт\nСумма по тарифам: {4} кВт'.format(
            meter1_ee8003.energy_t1, meter1_ee8003.energy_t2, meter1_ee8003.energy_t3,
            meter1_ee8003.energy_t4, meter1_ee8003.energy_summ))
print(text)
