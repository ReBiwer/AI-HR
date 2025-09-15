from typing import Annotated
from fastapi import APIRouter, Query, HTTPException, Request
from fastapi.responses import RedirectResponse
from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute

from source.application.services.hh_service import IHHService
from source.application.services.state_manager import IStateManager

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    route_class=DishkaRoute,
)


@router.get(
    "/hh/oauth/url",
    name="get_oauth_url"
)
async def get_oauth_url(
        state: Annotated[str, Query(description="Текущее состояние, для возврата после авторизации")],
        hh_service: FromDishka[IHHService]
) -> str:
    """
    Эндпоинт для получения ссылки для авторизации

    :param state: Текущее состояние куда нужно будет выполнить редирект после получения токенов
    :param hh_service: Сервис для работы с hh.ru
    :return:
    """
    return hh_service.get_auth_url(state)


@router.get(
    "/hh/tokens",
    name="get_hh_token"
)
async def get_tokens(
        request: Request,
        hh_service: FromDishka[IHHService],
        state_manager: FromDishka[IStateManager],
        code: Annotated[str, Query(description="Код авторизации от HeadHunter")],
        state: Annotated[str, Query(description="Состояние переданное для возврата после авторизации")],
) -> RedirectResponse:
    """
    Эндпоинт для получения токенов после OAuth редиректа от HeadHunter.

    :param request: Объект запроса для получения redirect_url по имени (state)
    :param hh_service: Сервис для работы с hh.ru
    :param state_manager: Сервис для создания url'ов для редиректа
    :param code: Обязательный код авторизации, который HeadHunter передает в query параметрах
    :param state: Обязательное состояние для редиректа после получения токенов
    :return:
    """
    try:
        redirect_url = await state_manager.state_converter(state, request)
        tokens = await hh_service.auth(code)
        response = RedirectResponse(redirect_url)
        response.set_cookie("access_token", value=tokens["access_token"])
        response.set_cookie("refresh_token", value=tokens["refresh_token"])
        return response
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
