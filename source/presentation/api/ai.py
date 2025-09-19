from fastapi import APIRouter
from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute

from source.application.dtos.query import QueryCreateDTO
from source.application.use_cases.generate_response import GenerateResponseUseCase
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
