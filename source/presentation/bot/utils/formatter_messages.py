from source.domain.entities.user import UserEntity


def profile_text(user: UserEntity) -> str:
    """Получение текст для отображения профиля пользователя"""
    return f"👤 <b>Ваш профиль HH.ru</b>\n\n{user.name}"
