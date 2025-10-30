from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup

from source.presentation.bot.storage_keys import CallbackKeys


def profile_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="profile", callback_data=CallbackKeys.PROFILE)
    builder.button(text="logout", callback_data=CallbackKeys.LOGOUT)
    builder.adjust(2, 1)
    return builder.as_markup()
