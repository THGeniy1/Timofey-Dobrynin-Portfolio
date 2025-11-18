from constants import *


def _validate_input_int(value: str):
    if not value or not isinstance(value, str):
        return None
    print(int(value))
    try:
        convert_value = int(value)
    except ValueError:
        return None

    if abs(convert_value) > pow(1000, SCALE):
        return None

    return convert_value


def _validate_input_str(value: str, validate_list: list):
    if not value or not isinstance(value, str):
        return None

    value = value.strip().strip('"\'')

    if not value:
        return None

    first_char = value[0].lower()

    if first_char in validate_list:
        return first_char
    return None


def validator(value: str, gender: str, case: str):
    validated_input = _validate_input_int(value=value)
    validated_gender = _validate_input_str(value=gender, validate_list=GENDER_LIST)
    validated_case = _validate_input_str(value=case, validate_list=CASE_LIST)

    return validated_input, validated_gender, validated_case
