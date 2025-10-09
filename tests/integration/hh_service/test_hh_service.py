from source.infrastructure.services.hh_service import HHService
from source.infrastructure.settings.test import TestAppSettings
from source.domain.entities.user import UserEntity
from source.domain.entities.resume import ResumeEntity
from source.domain.entities.vacancy import VacancyEntity
from source.domain.entities.employer import EmployerEntity
from source.domain.entities.response import ResponseToVacancyEntity


async def test_get_me(hh_service: HHService, test_settings: TestAppSettings):
    result = await hh_service.get_me(test_settings.HH_FAKE_SUBJECT)
    assert result
    assert isinstance(result, UserEntity)
    assert isinstance(result.resumes, list)
    assert isinstance(result.resumes[0], ResumeEntity)


async def test_get_vacancy_data(
    hh_service: HHService,
    test_settings: TestAppSettings,
    test_vacancy: VacancyEntity,
):
    result = await hh_service.get_vacancy_data(test_vacancy.hh_id)
    assert result
    assert isinstance(result, VacancyEntity)


async def test_get_employer_data(
    hh_service: HHService,
    test_settings: TestAppSettings,
    test_vacancy: VacancyEntity,
):
    result = await hh_service.get_employer_data(test_vacancy.employer_id)
    assert result
    assert isinstance(result, EmployerEntity)


async def test_get_good_responses(
    hh_service: HHService,
    test_settings: TestAppSettings,
):
    result = await hh_service.get_good_responses()
    assert result
    assert isinstance(result, list)
    assert isinstance(result[0], ResponseToVacancyEntity)


async def test_data_collect_for_llm(
    hh_service: HHService, test_vacancy: VacancyEntity, test_settings: TestAppSettings
):
    data_user = await hh_service.get_me(test_settings.HH_FAKE_SUBJECT)
    result = await hh_service.data_collect_for_llm(
        data_user.id, test_vacancy.hh_id, data_user.resumes[0].hh_id
    )
    assert result
    assert isinstance(result["vacancy"], VacancyEntity)
    assert isinstance(result["resume"], ResumeEntity)
    assert isinstance(result["employer"], EmployerEntity)
    assert isinstance(result["good_responses"], list)
    assert isinstance(result["good_responses"][0], ResponseToVacancyEntity)
