from abc import ABC

from source.application.repositories.base import ISQLRepository
from source.domain.entities.resume import JobExperienceEntity, ResumeEntity


class IResumeRepository[ET: ResumeEntity](ISQLRepository[ResumeEntity], ABC): ...


class IJobExperienceRepository[ET: JobExperienceEntity](
    ISQLRepository[JobExperienceEntity], ABC
): ...
