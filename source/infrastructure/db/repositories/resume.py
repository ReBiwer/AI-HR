from source.infrastructure.db.repositories.base import SQLAlchemyRepository
from source.infrastructure.db.models.resume import ResumeModel, JobExperienceModel
from source.application.repositories.resume import IResumeRepository, IJobExperienceRepository
from source.domain.entities.resume import ResumeEntity, JobExperienceEntity


class ResumeRepository[ET: ResumeEntity, DBModel: ResumeModel](SQLAlchemyRepository, IResumeRepository):
    model_class = ResumeModel
    entity_class = ResumeEntity


class JobExperienceRepository[ET: JobExperienceEntity, DBModel: JobExperienceModel](SQLAlchemyRepository, IJobExperienceRepository):
    model_class = JobExperienceModel
    entity_class = JobExperienceEntity
