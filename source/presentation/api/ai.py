from fastapi import APIRouter
from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute

from source.application.dtos.query import QueryCreateDTO, QueryRecreateDTO
from source.application.use_cases.generate_response import GenerateResponseUseCase
from source.application.use_cases.regenerate_response import RegenerateResponseUseCase
from source.application.services.hh_service import IHHService
from source.domain.entities.response import ResponseToVacancyEntity


router = APIRouter(
    prefix="/ai",
    tags=["ai"],
    route_class=DishkaRoute,
)

@router.post("/responses/generate")
async def generate_response(
        query: QueryCreateDTO,
        use_case: FromDishka[GenerateResponseUseCase],
) -> ResponseToVacancyEntity:
    result = await use_case(query)
    return result

@router.post("/responses/regenerate")
async def regenerate_response(
        query: QueryRecreateDTO,
        use_case: FromDishka[RegenerateResponseUseCase],
) -> ResponseToVacancyEntity:
    result = await use_case(query)
    return result

@router.post("/responses/send")
async def send_response(
        response: ResponseToVacancyEntity,
        hh_service: FromDishka[IHHService]
) -> None:
    await hh_service.send_response_to_vacancy(response)
