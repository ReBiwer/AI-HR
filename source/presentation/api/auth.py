from typing import Annotated
from fastapi import APIRouter, Query, HTTPException
from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute

from source.application.services.hh_service import IHHService


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    route_class=DishkaRoute,
)

@router.get("hh/get_oauth_url")
async def get_oauth_url(hh_service: FromDishka[IHHService]) -> str:
    return hh_service.get_auth_url()

@router.get("/hh/get_tokens")
async def get_tokens(
    hh_service: FromDishka[IHHService],
    code: Annotated[str, Query(description="Код авторизации от HeadHunter")],
    state: Annotated[str | None, Query(description="State параметр для проверки безопасности")] = None,
) -> dict:
    """
    Эндпоинт для получения токенов после OAuth редиректа от HeadHunter.
    
    Параметры:
    - code: Обязательный код авторизации, который HeadHunter передает в query параметрах
    - state: Опциональный параметр состояния для дополнительной безопасности
    
    Возвращает словарь с токенами доступа.
    """
    # Базовая валидация state параметра (можно расширить для хранения в сессии/кэше)
    if state is not None and len(state.strip()) == 0:
        raise HTTPException(
            status_code=400,
            detail="State параметр не может быть пустым"
        )
    
    try:
        # Получаем токены используя код авторизации
        tokens = await hh_service.auth(code)
        return {
            "message": "Авторизация прошла успешно",
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"]
        }
    except ValueError as e:
        # Ошибки валидации кода авторизации
        raise HTTPException(
            status_code=400,
            detail=f"Неверный код авторизации: {str(e)}"
        )
    except ConnectionError as e:
        # Ошибки соединения с API HeadHunter
        raise HTTPException(
            status_code=503,
            detail="Сервис HeadHunter временно недоступен. Попробуйте позже."
        )
    except Exception as e:
        # Общие ошибки
        raise HTTPException(
            status_code=500,
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )
