from source.infrastructure.db.repositories.base import SQLAlchemyRepository
from source.infrastructure.db.models.user import UserModel
from source.infrastructure.db.models.resume import ResumeModel, JobExperienceModel
from source.application.repositories.user import IUserRepository
from source.domain.entities.user import UserEntity


class UserRepository[ET: UserEntity, DBModel: UserModel](
    SQLAlchemyRepository, IUserRepository
):
    model_class = UserModel
    entity_class = UserEntity

    def _validate_entity_to_db_model(self, data: ET) -> DBModel:
        resume_instances = [
            ResumeModel(
                job_experience=[
                    JobExperienceModel(**job_exp.model_dump())
                    for job_exp in resume.job_experience
                ],
                **resume.model_dump(exclude={"job_experience"}),
            )
            for resume in data.resumes
        ]
        model_instance = self.model_class(
            **data.model_dump(exclude={"resumes"}), resumes=resume_instances
        )
        return model_instance
