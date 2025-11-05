from typing import Match
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from dishka.integrations.aiogram import FromDishka

from source.application.services.hh_service import IHHService
from source.domain.entities.response import ResponseToVacancyEntity
from source.presentation.bot.keyboards.inline import send_or_regenerate_ai_response
from source.constants.keys import CallbackKeys, StorageKeys
from source.constants.texts_message import AIMessages
from source.application.dtos.query import QueryCreateDTO, QueryRecreateDTO
from source.application.use_cases.generate_response import GenerateResponseUseCase
from source.application.use_cases.regenerate_response import RegenerateResponseUseCase
from source.domain.entities.resume import ResumeEntity
from source.domain.entities.user import UserEntity

reg_pattern = r"(?:https?://)?(?:[\w-]+\.)*hh\.ru/vacancy/(?P<vacancy_id>\d+)(?:[/?#][^\s.,!?)]*)?"

router = Router()


class RegenerateResponse(StatesGroup):
    user_comments = State()


@router.message(F.text.regexp(reg_pattern).as_("url"))
async def handler_hh_vacancy(
    message: Message,
    url: Match,
    state: FSMContext,
    user: FromDishka[UserEntity | None],
    resume: FromDishka[ResumeEntity | None],
    generate_case: FromDishka[GenerateResponseUseCase],
):
    if resume:
        await state.update_data({StorageKeys.CURRENT_VACANCY_URL: url.string})
        await state.update_data(
            {StorageKeys.CURRENT_VACANCY_HH_ID: url.group("vacancy_id")}
        )
        dto = QueryCreateDTO(
            subject=user.hh_id,
            user_id=user.id,
            url_vacancy=url.string,
            resume_hh_id=resume.hh_id,
        )
        response = await generate_case(dto)
        await message.answer(
            response.message, reply_markup=send_or_regenerate_ai_response()
        )
        return
    await message.answer(AIMessages.no_active_resume())


@router.callback_query(F.data == CallbackKeys.SEND_AI_RESPONSE)
async def send_ai_response(
    callback: CallbackQuery,
    state: FSMContext,
    resume: FromDishka[ResumeEntity],
    hh_service: FromDishka[IHHService],
):
    await callback.answer()
    response = ResponseToVacancyEntity(
        url_vacancy=await state.get_value(StorageKeys.CURRENT_VACANCY_URL),
        vacancy_hh_id=await state.get_value(StorageKeys.CURRENT_VACANCY_HH_ID),
        resume_hh_id=resume.hh_id,
        message=callback.message.text,
    )
    await hh_service.send_response_to_vacancy(response)


@router.callback_query(F.data == CallbackKeys.REGENERATE_AI_RESPONSE)
async def requesting_user_edits(
    callback: CallbackQuery,
    state: FSMContext,
):
    await callback.answer()
    await state.update_data({StorageKeys.AI_RESPONSE: callback.message.text})
    await callback.message.answer(AIMessages.request_user_comments())
    await state.set_state(RegenerateResponse.user_comments)


@router.message(RegenerateResponse.user_comments)
async def regenerate_response(
    message: Message,
    state: FSMContext,
    user: FromDishka[UserEntity | None],
    resume: FromDishka[ResumeEntity | None],
    regenerate_case: FromDishka[RegenerateResponseUseCase],
):
    url = await state.get_value(StorageKeys.CURRENT_VACANCY_URL)
    ai_response = await state.get_value(StorageKeys.AI_RESPONSE)
    user_comments = message.text
    dto = QueryRecreateDTO(
        subject=user.hh_id,
        user_id=user.id,
        url_vacancy=url,
        resume_hh_id=resume.hh_id,
        response=ai_response,
        user_comments=user_comments,
    )
    new_response = await regenerate_case(dto)
    await state.set_state()
    return message.answer(
        new_response.message, reply_markup=send_or_regenerate_ai_response()
    )
