from constants import *


def _get_word_form(gender: str, case: str, form_key: str, forms: dict):
    if 'о' in forms.keys():
        gender_values = forms.get('о')
    else:
        gender_values = forms.get(gender)

    if 'ч' in gender_values.keys():
        form_values = gender_values.get('ч')

    else:
        form_values = gender_values.get(form_key)

    return form_values.get(case)


def _get_convert_triplet(triplet: int, gender: str, case: str, form_key: str = 'е'):
    convert_triplet_list = []

    hundreds = triplet // 100
    tens = triplet % 100
    ones = triplet % 10

    if hundreds:
        convert_triplet_list.append(_get_word_form(gender=gender, case=case,
                                                   forms=HUNDREDS[hundreds - 1], form_key=form_key))

    if 10 <= tens < 20:
        convert_triplet_list.append(_get_word_form(gender=gender, case=case,
                                                   forms=TEENS[tens % 10], form_key=form_key))

    else:
        if tens >= 20:
            convert_triplet_list.append(_get_word_form(gender=gender, case=case,
                                                       forms=TENS[tens // 10 - 2], form_key=form_key))

        if ones > 0:
            convert_triplet_list.append(_get_word_form(gender=gender, case=case,
                                                       forms=ONES[ones], form_key=form_key))

    return convert_triplet_list


def _get_triplet_params(case: str, triplet_ones: int):
    triplet_case = case
    level_case = case
    level_form_key = 'е'

    if 2 <= triplet_ones <= 4:
        if case in ['и', 'в']:
            triplet_case, level_case = 'и', 'р'
        else:
            level_form_key = 'м'

    elif 5 <= triplet_ones:
        if case in ['и', 'в']:
            triplet_case, level_case, level_form_key = 'и', 'р', 'м'
        else:
            level_form_key = 'м'

    return triplet_case, level_case, level_form_key


def _get_convert_level_triplet(triplet: int, case: str, scale_index: int):
    level_gender = 'ж' if scale_index == 1 else 'м'
    tens = triplet % 100
    triplet_ones = triplet % 10

    if 11 <= tens <= 19:
        triplet_case, level_case, level_triplet_key = case, 'р', 'м'
    else:
        triplet_case, level_case, level_form_key = _get_triplet_params(case, triplet_ones)
        level_triplet_key = level_form_key

    level_triplet = _get_convert_triplet(
        triplet=triplet,
        gender=level_gender,
        case=triplet_case,
        form_key=level_triplet_key
    )

    level_triplet.append(_get_word_form(
        gender=level_gender,
        case=level_case,
        forms=LEVELS[scale_index - 1],
        form_key=level_triplet_key
    ))

    return level_triplet


def convert_number_to_words(value: int, gender: str, case: str):
    parts = []
    all_parts = []

    result = ''
    scale_index = 0

    if value == 0:
        return _get_word_form(gender=gender, case=case, forms=ONES[0], form_key='е')

    if value < 0:
        result += "минус" + ' '
        value = abs(value)

    while value > 0 and scale_index < SCALE:
        triplet = value % 1000

        if triplet:
            if scale_index == 0:
                triplet_words = _get_convert_triplet(triplet=triplet, gender=gender, case=case)

            else:
                triplet_words = _get_convert_level_triplet(triplet=triplet, case=case, scale_index=scale_index)

            parts.append(triplet_words)

        value = value // 1000
        scale_index += 1

    for part in reversed(parts):
        all_parts.append(' '.join(part))

    result += ' '.join(all_parts)

    return result
