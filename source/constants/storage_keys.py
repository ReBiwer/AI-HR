class StorageKeys:
    """Ключи для хранения данных пользователя в FSM storage."""

    # Информация о пользователе HH
    USER_INFO = "user_data"
    ACTIVE_RESUME_ID = "active_resume_id"
    ACTIVE_RESUME_TITLE = "active_resume_title"


class CallbackKeys:
    """Ключи для хранения значений для вызова callback команд"""

    LOGIN = "login"
    PROFILE = "profile"
    LOGOUT = "logout"
