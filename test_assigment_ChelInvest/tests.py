import pytest
from int_converter import convert_number_to_words


def test_zero_all_cases():
    """Тест нуля во всех падежах"""
    # Именительный
    assert convert_number_to_words(0, 'м', 'и') == 'ноль'
    assert convert_number_to_words(0, 'ж', 'и') == 'ноль'
    assert convert_number_to_words(0, 'с', 'и') == 'ноль'

    # Родительный
    assert convert_number_to_words(0, 'м', 'р') == 'ноля'
    assert convert_number_to_words(0, 'ж', 'р') == 'ноля'
    assert convert_number_to_words(0, 'с', 'р') == 'ноля'

    # Дательный
    assert convert_number_to_words(0, 'м', 'д') == 'нолю'
    assert convert_number_to_words(0, 'ж', 'д') == 'нолю'
    assert convert_number_to_words(0, 'с', 'д') == 'нолю'

    # Винительный
    assert convert_number_to_words(0, 'м', 'в') == 'ноль'
    assert convert_number_to_words(0, 'ж', 'в') == 'ноль'
    assert convert_number_to_words(0, 'с', 'в') == 'ноль'

    # Творительный
    assert convert_number_to_words(0, 'м', 'т') == 'нолём'
    assert convert_number_to_words(0, 'ж', 'т') == 'нолём'
    assert convert_number_to_words(0, 'с', 'т') == 'нолём'

    # Предложный
    assert convert_number_to_words(0, 'м', 'п') == 'ноле'
    assert convert_number_to_words(0, 'ж', 'п') == 'ноле'
    assert convert_number_to_words(0, 'с', 'п') == 'ноле'


def test_ones_all_cases():
    """Тест единиц во всех падежах"""
    # Мужской род
    assert convert_number_to_words(1, 'м', 'и') == 'один'
    assert convert_number_to_words(1, 'м', 'р') == 'одного'
    assert convert_number_to_words(1, 'м', 'д') == 'одному'
    assert convert_number_to_words(1, 'м', 'в') == 'один'
    assert convert_number_to_words(1, 'м', 'т') == 'одним'
    assert convert_number_to_words(1, 'м', 'п') == 'одном'

    assert convert_number_to_words(2, 'м', 'и') == 'два'
    assert convert_number_to_words(2, 'м', 'р') == 'двух'
    assert convert_number_to_words(2, 'м', 'д') == 'двум'
    assert convert_number_to_words(2, 'м', 'в') == 'два'
    assert convert_number_to_words(2, 'м', 'т') == 'двумя'
    assert convert_number_to_words(2, 'м', 'п') == 'двух'

    # Женский род
    assert convert_number_to_words(1, 'ж', 'и') == 'одна'
    assert convert_number_to_words(1, 'ж', 'р') == 'одной'
    assert convert_number_to_words(1, 'ж', 'д') == 'одной'
    assert convert_number_to_words(1, 'ж', 'в') == 'одну'
    assert convert_number_to_words(1, 'ж', 'т') == 'одной'
    assert convert_number_to_words(1, 'ж', 'п') == 'одной'

    assert convert_number_to_words(2, 'ж', 'и') == 'две'
    assert convert_number_to_words(2, 'ж', 'р') == 'двух'
    assert convert_number_to_words(2, 'ж', 'д') == 'двум'
    assert convert_number_to_words(2, 'ж', 'в') == 'две'
    assert convert_number_to_words(2, 'ж', 'т') == 'двумя'
    assert convert_number_to_words(2, 'ж', 'п') == 'двух'

    # Средний род
    assert convert_number_to_words(1, 'с', 'и') == 'одно'
    assert convert_number_to_words(1, 'с', 'р') == 'одного'
    assert convert_number_to_words(1, 'с', 'д') == 'одному'
    assert convert_number_to_words(1, 'с', 'в') == 'одно'
    assert convert_number_to_words(1, 'с', 'т') == 'одним'
    assert convert_number_to_words(1, 'с', 'п') == 'одном'

    assert convert_number_to_words(2, 'с', 'и') == 'два'
    assert convert_number_to_words(2, 'с', 'р') == 'двух'
    assert convert_number_to_words(2, 'с', 'д') == 'двум'
    assert convert_number_to_words(2, 'с', 'в') == 'два'
    assert convert_number_to_words(2, 'с', 'т') == 'двумя'
    assert convert_number_to_words(2, 'с', 'п') == 'двух'


def test_tens_all_cases():
    """Тест десятков во всех падежах"""
    # 20-90
    assert convert_number_to_words(20, 'м', 'и') == 'двадцать'
    assert convert_number_to_words(20, 'м', 'р') == 'двадцати'
    assert convert_number_to_words(20, 'м', 'д') == 'двадцати'
    assert convert_number_to_words(20, 'м', 'в') == 'двадцать'
    assert convert_number_to_words(20, 'м', 'т') == 'двадцатью'
    assert convert_number_to_words(20, 'м', 'п') == 'двадцати'

    # Составные числа
    assert convert_number_to_words(21, 'м', 'и') == 'двадцать один'
    assert convert_number_to_words(21, 'м', 'р') == 'двадцати одного'
    assert convert_number_to_words(21, 'м', 'д') == 'двадцати одному'
    assert convert_number_to_words(21, 'м', 'в') == 'двадцать один'
    assert convert_number_to_words(21, 'м', 'т') == 'двадцатью одним'
    assert convert_number_to_words(21, 'м', 'п') == 'двадцати одном'

    assert convert_number_to_words(22, 'ж', 'и') == 'двадцать две'
    assert convert_number_to_words(22, 'ж', 'р') == 'двадцати двух'
    assert convert_number_to_words(22, 'ж', 'д') == 'двадцати двум'
    assert convert_number_to_words(22, 'ж', 'в') == 'двадцать две'
    assert convert_number_to_words(22, 'ж', 'т') == 'двадцатью двумя'
    assert convert_number_to_words(22, 'ж', 'п') == 'двадцати двух'


def test_hundreds_all_cases():
    """Тест сотен во всех падежах"""
    assert convert_number_to_words(100, 'м', 'и') == 'сто'
    assert convert_number_to_words(100, 'м', 'р') == 'ста'
    assert convert_number_to_words(100, 'м', 'д') == 'ста'
    assert convert_number_to_words(100, 'м', 'в') == 'сто'
    assert convert_number_to_words(100, 'м', 'т') == 'ста'
    assert convert_number_to_words(100, 'м', 'п') == 'ста'

    assert convert_number_to_words(200, 'м', 'и') == 'двести'
    assert convert_number_to_words(200, 'м', 'р') == 'двухсот'
    assert convert_number_to_words(200, 'м', 'д') == 'двумстам'
    assert convert_number_to_words(200, 'м', 'в') == 'двести'
    assert convert_number_to_words(200, 'м', 'т') == 'двумястами'
    assert convert_number_to_words(200, 'м', 'п') == 'двухстах'

    # Составные числа с сотнями
    assert convert_number_to_words(123, 'м', 'и') == 'сто двадцать три'
    assert convert_number_to_words(123, 'м', 'р') == 'ста двадцати трёх'
    assert convert_number_to_words(123, 'м', 'д') == 'ста двадцати трём'
    assert convert_number_to_words(123, 'м', 'в') == 'сто двадцать три'
    assert convert_number_to_words(123, 'м', 'т') == 'ста двадцатью тремя'
    assert convert_number_to_words(123, 'м', 'п') == 'ста двадцати трёх'


def test_thousands_all_cases():
    """Тест тысяч во всех падежах"""
    # 1000
    assert convert_number_to_words(1000, 'ж', 'и') == 'одна тысяча'
    assert convert_number_to_words(1000, 'ж', 'р') == 'одной тысячи'
    assert convert_number_to_words(1000, 'ж', 'д') == 'одной тысяче'
    assert convert_number_to_words(1000, 'ж', 'в') == 'одну тысячу'
    assert convert_number_to_words(1000, 'ж', 'т') == 'одной тысячей'
    assert convert_number_to_words(1000, 'ж', 'п') == 'одной тысяче'

    # 2000
    assert convert_number_to_words(2000, 'ж', 'и') == 'две тысячи'
    assert convert_number_to_words(2000, 'ж', 'р') == 'двух тысяч'
    assert convert_number_to_words(2000, 'ж', 'д') == 'двум тысячам'
    assert convert_number_to_words(2000, 'ж', 'в') == 'две тысячи'
    assert convert_number_to_words(2000, 'ж', 'т') == 'двумя тысячами'
    assert convert_number_to_words(2000, 'ж', 'п') == 'двух тысячах'

    # 5000
    assert convert_number_to_words(5000, 'ж', 'и') == 'пять тысяч'
    assert convert_number_to_words(5000, 'ж', 'р') == 'пяти тысяч'
    assert convert_number_to_words(5000, 'ж', 'д') == 'пяти тысячам'
    assert convert_number_to_words(5000, 'ж', 'в') == 'пять тысяч'
    assert convert_number_to_words(5000, 'ж', 'т') == 'пятью тысячами'
    assert convert_number_to_words(5000, 'ж', 'п') == 'пяти тысячах'

    # Составные числа с тысячами
    assert convert_number_to_words(1234, 'ж', 'и') == 'одна тысяча двести тридцать четыре'
    assert convert_number_to_words(1234, 'ж', 'р') == 'одной тысячи двухсот тридцати четырёх'
    assert convert_number_to_words(1234, 'ж', 'д') == 'одной тысяче двумстам тридцати четырём'
    assert convert_number_to_words(1234, 'ж', 'в') == 'одну тысячу двести тридцать четыре'
    assert convert_number_to_words(1234, 'ж', 'т') == 'одной тысячей двумястами тридцатью четырьмя'
    assert convert_number_to_words(1234, 'ж', 'п') == 'одной тысяче двухстах тридцати четырёх'


def test_millions_all_cases():
    """Тест миллионов во всех падежах"""
    # 1 000 000
    assert convert_number_to_words(1000000, 'м', 'и') == 'один миллион'
    assert convert_number_to_words(1000000, 'м', 'р') == 'одного миллиона'
    assert convert_number_to_words(1000000, 'м', 'д') == 'одному миллиону'
    assert convert_number_to_words(1000000, 'м', 'в') == 'один миллион'
    assert convert_number_to_words(1000000, 'м', 'т') == 'одним миллионом'
    assert convert_number_to_words(1000000, 'м', 'п') == 'одном миллионе'

    # 2 000 000
    assert convert_number_to_words(2000000, 'м', 'и') == 'два миллиона'
    assert convert_number_to_words(2000000, 'м', 'р') == 'двух миллионов'
    assert convert_number_to_words(2000000, 'м', 'д') == 'двум миллионам'
    assert convert_number_to_words(2000000, 'м', 'в') == 'два миллиона'
    assert convert_number_to_words(2000000, 'м', 'т') == 'двумя миллионами'
    assert convert_number_to_words(2000000, 'м', 'п') == 'двух миллионах'

    # 5 000 000
    assert convert_number_to_words(5000000, 'м', 'и') == 'пять миллионов'
    assert convert_number_to_words(5000000, 'м', 'р') == 'пяти миллионов'
    assert convert_number_to_words(5000000, 'м', 'д') == 'пяти миллионам'
    assert convert_number_to_words(5000000, 'м', 'в') == 'пять миллионов'
    assert convert_number_to_words(5000000, 'м', 'т') == 'пятью миллионами'
    assert convert_number_to_words(5000000, 'м', 'п') == 'пяти миллионах'


def test_billions_all_cases():
    """Тест миллиардов во всех падежах"""
    # 1 000 000 000
    assert convert_number_to_words(1000000000, 'м', 'и') == 'один миллиард'
    assert convert_number_to_words(1000000000, 'м', 'р') == 'одного миллиарда'
    assert convert_number_to_words(1000000000, 'м', 'д') == 'одному миллиарду'
    assert convert_number_to_words(1000000000, 'м', 'в') == 'один миллиард'
    assert convert_number_to_words(1000000000, 'м', 'т') == 'одним миллиардом'
    assert convert_number_to_words(1000000000, 'м', 'п') == 'одном миллиарде'

    # 2 000 000 000
    assert convert_number_to_words(2000000000, 'м', 'и') == 'два миллиарда'
    assert convert_number_to_words(2000000000, 'м', 'р') == 'двух миллиардов'
    assert convert_number_to_words(2000000000, 'м', 'д') == 'двум миллиардам'
    assert convert_number_to_words(2000000000, 'м', 'в') == 'два миллиарда'
    assert convert_number_to_words(2000000000, 'м', 'т') == 'двумя миллиардами'
    assert convert_number_to_words(2000000000, 'м', 'п') == 'двух миллиардах'


def test_complex_numbers_all_cases():
    """Тест сложных чисел во всех падежах"""
    # 123 456 789
    assert convert_number_to_words(123456789, 'м',
                                   'и') == 'сто двадцать три миллиона четыреста пятьдесят шесть тысяч семьсот восемьдесят девять'
    assert convert_number_to_words(123456789, 'м',
                                   'р') == 'ста двадцати трёх миллионов четырёхсот пятидесяти шести тысяч семисот восьмидесяти девяти'
    assert convert_number_to_words(123456789, 'м',
                                   'д') == 'ста двадцати трём миллионам четырёмстам пятидесяти шести тысячам семистам восьмидесяти девяти'
    assert convert_number_to_words(123456789, 'м',
                                   'в') == 'сто двадцать три миллиона четыреста пятьдесят шесть тысяч семьсот восемьдесят девять'
    assert convert_number_to_words(123456789, 'м',
                                   'т') == 'ста двадцатью тремя миллионами четырьмястами пятьюдесятью шестью тысячами семьюстами восемьюдесятью девятью'
    assert convert_number_to_words(123456789, 'м',
                                   'п') == 'ста двадцати трёх миллионах четырёхстах пятидесяти шести тысячах семистах восьмидесяти девяти'


def test_negative_numbers_all_cases():
    """Тест отрицательных чисел во всех падежах"""
    assert convert_number_to_words(-1, 'м', 'и') == 'минус один'
    assert convert_number_to_words(-1, 'м', 'р') == 'минус одного'
    assert convert_number_to_words(-1, 'м', 'д') == 'минус одному'
    assert convert_number_to_words(-1, 'м', 'в') == 'минус один'
    assert convert_number_to_words(-1, 'м', 'т') == 'минус одним'
    assert convert_number_to_words(-1, 'м', 'п') == 'минус одном'

    assert convert_number_to_words(-123, 'ж', 'и') == 'минус сто двадцать три'
    assert convert_number_to_words(-123, 'ж', 'р') == 'минус ста двадцати трёх'
    assert convert_number_to_words(-123, 'ж', 'д') == 'минус ста двадцати трём'
    assert convert_number_to_words(-123, 'ж', 'в') == 'минус сто двадцать три'
    assert convert_number_to_words(-123, 'ж', 'т') == 'минус ста двадцатью тремя'
    assert convert_number_to_words(-123, 'ж', 'п') == 'минус ста двадцати трёх'


def test_special_cases():
    """Тест особых случаев"""
    # Числа 11-19
    assert convert_number_to_words(11, 'м', 'и') == 'одиннадцать'
    assert convert_number_to_words(11, 'м', 'р') == 'одиннадцати'
    assert convert_number_to_words(11, 'м', 'д') == 'одиннадцати'
    assert convert_number_to_words(11, 'м', 'в') == 'одиннадцать'
    assert convert_number_to_words(11, 'м', 'т') == 'одиннадцатью'
    assert convert_number_to_words(11, 'м', 'п') == 'одиннадцати'

    # 40
    assert convert_number_to_words(40, 'м', 'и') == 'сорок'
    assert convert_number_to_words(40, 'м', 'р') == 'сорока'
    assert convert_number_to_words(40, 'м', 'д') == 'сорока'
    assert convert_number_to_words(40, 'м', 'в') == 'сорок'
    assert convert_number_to_words(40, 'м', 'т') == 'сорока'
    assert convert_number_to_words(40, 'м', 'п') == 'сорока'

    # 90
    assert convert_number_to_words(90, 'м', 'и') == 'девяносто'
    assert convert_number_to_words(90, 'м', 'р') == 'девяноста'
    assert convert_number_to_words(90, 'м', 'д') == 'девяноста'
    assert convert_number_to_words(90, 'м', 'в') == 'девяносто'
    assert convert_number_to_words(90, 'м', 'т') == 'девяноста'
    assert convert_number_to_words(90, 'м', 'п') == 'девяноста'

    # 100
    assert convert_number_to_words(100, 'м', 'и') == 'сто'
    assert convert_number_to_words(100, 'м', 'р') == 'ста'
    assert convert_number_to_words(100, 'м', 'д') == 'ста'
    assert convert_number_to_words(100, 'м', 'в') == 'сто'
    assert convert_number_to_words(100, 'м', 'т') == 'ста'
    assert convert_number_to_words(100, 'м', 'п') == 'ста'


def test_mixed_gender_cases():
    """Тест смешанных родов в составных числах"""
    # Тысячи (ж) + единицы (м/ж/с)
    assert convert_number_to_words(1001, 'м', 'и') == 'одна тысяча один'
    assert convert_number_to_words(1001, 'ж', 'и') == 'одна тысяча одна'
    assert convert_number_to_words(1001, 'с', 'и') == 'одна тысяча одно'

    assert convert_number_to_words(2002, 'м', 'и') == 'две тысячи два'
    assert convert_number_to_words(2002, 'ж', 'и') == 'две тысячи две'
    assert convert_number_to_words(2002, 'с', 'и') == 'две тысячи два'

    # Миллионы (м) + тысячи (ж) + единицы (м/ж/с)
    assert convert_number_to_words(1001001, 'м', 'и') == 'один миллион одна тысяча один'
    assert convert_number_to_words(1001001, 'ж', 'и') == 'один миллион одна тысяча одна'
    assert convert_number_to_words(1001001, 'с', 'и') == 'один миллион одна тысяча одно'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])