import openai
from typing import TypedDict
from langchain.prompts import PromptTemplate
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.memory import BaseCheckpointSaver

from source.infrastructure.settings.app import app_settings
from source.application.services.ai_service import IAIService, GenerateResponseData
from source.domain.entities.response import ResponseToVacancyEntity
from source.domain.entities.vacancy import VacancyEntity
from source.domain.entities.resume import ResumeEntity
from source.domain.entities.employer import EmployerEntity


class AIServiceState(TypedDict):
    vacancy: VacancyEntity
    resume: ResumeEntity
    employer: EmployerEntity
    good_responses: list[ResponseToVacancyEntity]
    user_rules: dict
    response: str | None
    user_comments: str | None


def gen_png_graph(app_obj, name_photo: str = f"{app_settings.BASE_DIR}/schema_graph.png") -> None:
    """
    Генерирует PNG-изображение графа и сохраняет его в файл.

    Args:
        app_obj: Скомпилированный объект графа
        name_photo: Имя файла для сохранения (по умолчанию "schema_graph.png" в директории проекта)
    """
    with open(name_photo, "wb") as f:
        f.write(app_obj.get_graph().draw_mermaid_png())


class AIService(IAIService):

    def __init__(self, checkpointer: BaseCheckpointSaver):
        self.llm = ChatOpenAI(
            model=app_settings.OPENAI_MODEL,
            temperature=0.7,
            api_key=app_settings.OPENROUTER_API_KEY,
            base_url=app_settings.OPENROUTER_BASE_URL
        )
        self._workflow = self._build_workflow(checkpointer)
        gen_png_graph(self._workflow)


    @staticmethod
    def _get_config(user_id: int) -> RunnableConfig:
        return RunnableConfig(
            configurable={
                "thread_id": f"user_{user_id}",
            }
        )


    def _build_workflow(self, checkpointer: BaseCheckpointSaver) -> CompiledStateGraph:
        workflow = StateGraph(AIServiceState) # type: ignore
        workflow.add_node("fake_node", lambda x: x)
        workflow.add_node("generate_response", self._generate_response_node)
        workflow.add_node("regenerate_response", self._regenerate_response_node)

        workflow.add_conditional_edges(
            "fake_node",
            self._check_exist_response,
            {
                "generate_response": "generate_response",
                "regenerate_response": "regenerate_response"
            }
        )
        workflow.add_edge(START, "fake_node")
        workflow.add_edge("generate_response", END)
        workflow.add_edge("regenerate_response", END)
        return workflow.compile(checkpointer=checkpointer)


    @staticmethod
    def _check_exist_response(state: AIServiceState) -> str:
        if state["response"] is None and state["user_comments"] is None:
            return "generate_response"
        return "regenerate_response"


    async def _generate_response_node(self, state: AIServiceState) -> dict[str, str]:
        prompt = PromptTemplate(
            input_variables=["vacancy", "resume", "employer", "good_responses", "user_rules"],
            template="""
            Ты мой помощник в написании сопроводительных писем. 
            Тебе нужно составить сопроводительное письмо к этой вакансии: {vacancy}\n
            Письмо составляй учитывая следующую информацию: \n
            
            1. мое резюме {resume};\n
            2. описание работодателя если оно есть {employer}\n
            3. мои удачные отклики {good_responses}.\n
            4. мои правила по составлению сопроводительного {user_rules};\n
            
            Также в конце нужно обязательно добавить абзац про мою мотивацию работы у работодателя
            опираясь на информацию из вакансии и описание работодателя (если оно есть).            
            """
        )
        message = HumanMessage(content=prompt.format(**state))
        try:
            response = await self.llm.ainvoke([message])
            return {"response": response.text()}
        except openai.NotFoundError as e:
            print(f"Ошибка отправки промтпа: {e}")
            raise


    async def _regenerate_response_node(self, state: AIServiceState) -> dict[str, str]:
        prompt = PromptTemplate(
            input_variables=["vacancy", "resume", "employer", "good_responses", "user_rules", "response", "user_comments"],
            template="""
            Ты мой помощник в написании сопроводительных писем. 
            Тебе нужно скорректировать сопроводительное составленное ранее {response}\n.
            В исправлении учитывай следующую информацию: \n

            1. описание вакансии {vacancy}\n 
            2. мое резюме {resume};\n 
            3. описание работодателя если оно есть {employer}\n
            4. мои правила по составлению сопроводительного {user_rules};\n
            5. мои удачные отклики {good_responses}.\n
            6. мои комментарии {user_comments}

            Также в конце нужно обязательно добавить абзац про мою мотивацию работы у работодателя
            опираясь на информацию из вакансии и описание работодателя (если оно есть)            
            """
        )
        message = HumanMessage(content=prompt.format(**state))
        try:
            response = await self.llm.ainvoke([message])
            return {"response": response.text()}
        except openai.NotFoundError as e:
            print(f"Ошибка отправки промтпа: {e}")
            raise


    async def generate_response(
            self,
            data: GenerateResponseData
    ) -> ResponseToVacancyEntity:
        start_state = AIServiceState(**data)
        config = self._get_config(data["user_id"])
        result = await self._workflow.ainvoke(start_state, config=config) # type: ignore
        return ResponseToVacancyEntity(
            url_vacancy=result["vacancy"].url_vacancy,
            vacancy_id=result["vacancy"].id,
            resume_id=result["resume"].id,
            message=result["response"],
        )

    async def regenerate_response(
            self,
            user_id: int,
            response: str,
            user_comments: str,
            data: GenerateResponseData | None = None,
    ) -> ResponseToVacancyEntity:
        config = self._get_config(user_id)
        if not data:
            state: AIServiceState | None = self._workflow.get_state(config=config) # type: ignore

            if not state.values:
                raise ValueError("Не найдено сохраненного состояния. Необходимо собрать актуальную информацию")
        
            result = await self._workflow.ainvoke(
                {"response": response, "user_comments": user_comments}, # type: ignore
                config
            )
        else:
            start_state = AIServiceState(**data)
            start_state["response"] = response
            start_state["user_comments"] = user_comments
            result = await self._workflow.ainvoke(start_state, config=config)  # type: ignore

        return ResponseToVacancyEntity(
            url_vacancy=result["vacancy"].url_vacancy,
            vacancy_id=result["vacancy"].id,
            resume_id=result["resume"].id,
            message=result["response"],
        )
