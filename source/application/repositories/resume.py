from abc import ABC

from source.application.repositories.base import IRepository
from source.domain.entities.resume import ResumeEntity, JobExperienceEntity


class IResumeRepository[ET: ResumeEntity](IRepository[ResumeEntity], ABC):
    ...


class IJobExperienceRepository[ET: JobExperienceEntity](IRepository[JobExperienceEntity], ABC):
    ...
