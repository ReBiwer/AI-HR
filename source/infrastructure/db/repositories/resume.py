from source.application.repositories.resume import (
    IJobExperienceRepository,
    IResumeRepository,
)
from source.domain.entities.resume import JobExperienceEntity, ResumeEntity
from source.infrastructure.db.models.resume import JobExperienceModel, ResumeModel
from source.infrastructure.db.repositories.base import SQLAlchemyRepository


class ResumeRepository[ET: ResumeEntity, DBModel: ResumeModel](
    SQLAlchemyRepository, IResumeRepository
):
    model_class = ResumeModel
    entity_class = ResumeEntity


class JobExperienceRepository[ET: JobExperienceEntity, DBModel: JobExperienceModel](
    SQLAlchemyRepository, IJobExperienceRepository
):
    model_class = JobExperienceModel
    entity_class = JobExperienceEntity
