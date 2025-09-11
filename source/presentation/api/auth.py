from typing import Annotated
from fastapi import APIRouter, Query, HTTPException
from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute

from source.application.services.hh_service import IHHService
from source.application.use_cases.auth_hh import OAuthHHUseCase


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    route_class=DishkaRoute,
)

@router.get("/hh/get_oauth_url")
async def get_oauth_url(hh_service: FromDishka[IHHService]) -> str:
    return hh_service.get_auth_url()

@router.get("/hh/get_tokens")
async def get_tokens(
    use_case: FromDishka[OAuthHHUseCase],
    code: Annotated[str, Query(description="Код авторизации от HeadHunter")],
) -> dict:
    """
    Эндпоинт для получения токенов после OAuth редиректа от HeadHunter.
    
    Параметры:
    - code: Обязательный код авторизации, который HeadHunter передает в query параметрах
    
    Возвращает словарь с токенами доступа.
    """
    try:
        # Получаем токены используя код авторизации
        tokens = await use_case(code)
        return {
            "message": "Авторизация прошла успешно",
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
        }
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
