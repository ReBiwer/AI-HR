def split_long_message(text: str) -> list[str]:
    """Умное разбиение с учетом переносов строк и форматирования"""

    MAX_LENGTH = 4096

    if len(text) <= MAX_LENGTH:
        return [text]

    # Разбиваем по абзацам
    parts = []
    current_part = ""

    for paragraph in text.split("\n\n"):
        # Если текущая часть + параграф влезают
        if len(current_part) + len(paragraph) + 2 <= MAX_LENGTH:
            current_part += paragraph + "\n\n"
        else:
            # Сохраняем текущую часть и начинаем новую
            if current_part:
                parts.append(current_part.strip())
            current_part = paragraph + "\n\n"

    if current_part:
        parts.append(current_part.strip())

    return parts
