from abc import ABC

from source.application.repositories.base import ISQLRepository
from source.domain.entities.resume import ResumeEntity, JobExperienceEntity


class IResumeRepository[ET: ResumeEntity](ISQLRepository[ResumeEntity], ABC): ...


class IJobExperienceRepository[ET: JobExperienceEntity](
    ISQLRepository[JobExperienceEntity], ABC
): ...
