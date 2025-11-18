from int_converter import *
from validator import *

if __name__ == '__main__':

    value = input("Введите конвертируемое целое число от 0 до триллиона:")
    case = input("\nВведите падеж:").strip()
    gender = input("\nВведите род:").strip()

    validated_value, validated_gender, validated_case = validator(value=value, gender=gender, case=case)

    if validated_value is None:
        print("\nОшибка: не удалось получить целое число. Программа завершена.")
        exit(1)

    if not validated_gender:
        print("\nОшибка: указанный падеж не найден. Программа завершена.")
        exit(1)

    if not validated_case:
        print("\nОшибка: указанный род не найден. Программа завершена.")
        exit(1)

    result = convert_number_to_words(value=validated_value, gender=validated_gender, case=validated_case)

    print(f"Результат: {result}")
