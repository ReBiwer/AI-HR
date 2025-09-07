from pydantic import BaseModel
from langchain.prompts import PromptTemplate
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.memory import BaseCheckpointSaver

from source.infrastructure.settings.app import app_settings
from source.application.services.ai_service import IAIService
from source.domain.entities.response import ResponseToVacancyEntity
from source.domain.entities.vacancy import VacancyEntity
from source.domain.entities.resume import ResumeEntity
from source.domain.entities.employer import EmployerEntity
from source.domain.entities.base import BaseEntity


class AIServiceState(BaseModel):
    vacancy: VacancyEntity
    resume: ResumeEntity
    employer: EmployerEntity
    good_responses: list[ResponseToVacancyEntity]
    user_rules: dict
    response: str | None


class AIService(IAIService):

    def __init__(self):
        self.llm = ChatOpenAI(
            model=app_settings.OPENAI_MODEL,
            temperature=0,
            api_key=app_settings.OPENROUTER_API_KEY,
            base_url=app_settings.OPENROUTER_BASE_URL
        )
        self._workflow = self._build_workflow()

    def _build_workflow(self) -> CompiledStateGraph:
        workflow = StateGraph(AIServiceState)
        workflow.add_node("start", self._start_node)

        workflow.add_edge(START, "start")
        workflow.add_edge("start", END)
        return workflow.compile()

    async def _start_node(self, state: AIServiceState) -> AIServiceState:
        prompt = PromptTemplate(
            input_variables=["vacancy", "resume", "employer", "good_responses", "user_rules"],
            template="""
            Ты мой помощник в написании сопроводительных писем. 
            Тебе нужно составить сопроводительное опираясь на: \n
            
            1. мое резюме {resume};
            2. мои правила по составлению сопроводительного {user_rules};
            3. мои удачные отклики {good_responses}.\n
            
            На эту вакансию нужно составить сопроводительное: {vacancy}
            Также в конце нужно обязательно добавить абзац про мою мотивацию работы у работодателя
            опираясь на информацию из вакансии и описание работодателя. Вот описание: {employer}            
            """
        )
        message = HumanMessage(content=prompt.format(**state.model_dump()))
        response = await self.llm.ainvoke([message])
        state.response = response.text()
        return state

    async def generate_response(
            self,
            data: dict[str, BaseEntity]
    ) -> ResponseToVacancyEntity:
        start_state = AIServiceState.model_validate(data)
        result = await self._workflow.ainvoke(start_state)
        return ResponseToVacancyEntity(
            url_vacancy=result.vacancy.url_vacancy,
            vacancy_id=result.vacancy.id,
            resume_id=result.resume.id,
            message=result.response,
        )
