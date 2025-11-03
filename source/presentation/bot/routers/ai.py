from typing import Match
from aiogram import Router, F
from aiogram.types import Message
from dishka.integrations.aiogram import FromDishka

from source.constants.texts_message import AIMessages
from source.application.dtos.query import QueryCreateDTO
from source.application.use_cases.generate_response import GenerateResponseUseCase
from source.domain.entities.resume import ResumeEntity
from source.domain.entities.user import UserEntity

reg_pattern = r"(?:https?://)?(?:[\w-]+\.)*hh\.ru/vacancy/(?P<vacancy_id>\d+)(?:[/?#][^\s.,!?)]*)?"

router = Router()


@router.message(F.text.regexp(reg_pattern).as_("url"))
async def handler_hh_vacancy(
    message: Message,
    url: Match,
    user: FromDishka[UserEntity | None],
    resume: FromDishka[ResumeEntity | None],
    generate_case: FromDishka[GenerateResponseUseCase],
):
    if resume:
        dto = QueryCreateDTO(
            subject=user.hh_id,
            user_id=user.id,
            url_vacancy=url.string,
            resume_hh_id=resume.hh_id,
        )
        response = await generate_case(dto)
        await message.answer(response.message)
        return
    await message.answer(AIMessages.no_active_resume())
