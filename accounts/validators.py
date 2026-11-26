from django.core.exceptions import ValidationError


def validate_phone_number(phone):
    if any(character not in "0123456789+() -" for character in phone):
        raise ValidationError("Введите корректный номер телефона.")

    if "+" in phone and (phone.count("+") != 1 or not phone.startswith("+")):
        raise ValidationError("Введите корректный номер телефона.")

    if not 7 <= sum(character.isdigit() for character in phone) <= 15:
        raise ValidationError("Введите корректный номер телефона.")
