"""
Константы для ключей данных в FSM Storage.

Этот модуль содержит все ключи, используемые для хранения данных пользователя
в FSM storage. Использование констант помогает избежать опечаток и упрощает
рефакторинг.

Почему это важно:
- Централизованное управление ключами
- Автодополнение в IDE
- Легче отслеживать, какие данные где хранятся
- Избегаем магических строк в коде
"""


class StorageKeys:
    """Ключи для хранения данных пользователя в FSM storage."""

    # Токены авторизации HH.ru
    HH_ACCESS_TOKEN = "hh_access_token"
    HH_REFRESH_TOKEN = "hh_refresh_token"
    HH_TOKEN_EXPIRES_AT = "hh_token_expires_at"
    HH_TOKEN_TYPE = "hh_token_type"

    # Информация о пользователе HH
    HH_USER_ID = "hh_user_id"
    HH_USER_NAME = "hh_user_name"
    HH_USER_MID_NAME = "hh_user_mid_name"

    # Временные данные для процессов
    CURRENT_VACANCY_ID = "current_vacancy_id"
    CURRENT_RESUME_ID = "current_resume_id"
    SELECTED_RESPONSE_ID = "selected_response_id"

    # Настройки пользователя
    PREFERRED_LANGUAGE = "preferred_language"
    NOTIFICATION_ENABLED = "notification_enabled"
