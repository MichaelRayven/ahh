import logging
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.prompts import PromptTemplate
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_postgres.vectorstores import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.common.hash import compute_file_hash
from src.config.settings import Settings
from src.vacancy.schemas import (
    CheckboxAnswer,
    CheckboxQuestion,
    RadioAnswer,
    RadioQuestion,
    RadioWithTextAnswer,
    RadioWithTextQuestion,
    TextAnswer,
    TextQuestion,
    Vacancy,
    VacancyQuestion,
    VacancyQuestionAnswer,
)

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.llm = ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=0.05,
        )
        self.embeddings = OllamaEmbeddings(
            model=settings.ollama_embedding_model,
            base_url=settings.ollama_base_url,
        )
        self.vector_store = PGVector(
            embeddings=self.embeddings,
            collection_name="resumes",
            connection=self.settings.postgres_url,
            use_jsonb=True,
        )

    def index_resume(self, pdf_path: str) -> str:
        """Loads a PDF resume, splits it into chunks, and indexes it in Postgres with metadata."""
        resume_id = compute_file_hash(pdf_path)

        # Check if already indexed
        existing = self.vector_store.similarity_search(
            "test", k=1, filter={"id": resume_id}
        )
        if existing:
            logger.info(
                f"Resume {pdf_path} (ID: {resume_id}) is already indexed. Skipping."
            )
            return resume_id

        logger.info(f"Indexing resume: {pdf_path}")
        loader = PyPDFLoader(pdf_path)
        docs = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            add_start_index=True,
        )
        splits = text_splitter.split_documents(docs)

        # Add the pdf_path to the metadata of each document chunk so we can filter by it
        for split in splits:
            split.metadata["id"] = resume_id

        self.vector_store.add_documents(splits)
        logger.info(f"Successfully indexed {len(splits)} chunks for {pdf_path}")

        return resume_id

    def query_resume(self, query: str, resume_id: str, k: int = 4) -> str:
        """Retrieves relevant chunks from the specified resume."""
        results = self.vector_store.similarity_search(
            query, k=k, filter={"id": resume_id}
        )
        return "\n\n".join(doc.page_content for doc in results)

    async def generate_cover_letter(
        self, vacancy: Vacancy, resume_id: str | None = None
    ) -> str:
        prompt = PromptTemplate.from_template(self.settings.prompts.cover_letter)
        chain = prompt | self.llm

        resume_context = ""
        if resume_id:
            query = f"Experience and skills relevant for: {vacancy.title}. Description: {vacancy.description}"
            try:
                resume_context = self.query_resume(query, resume_id)
            except Exception as e:
                logger.error(f"Failed to query resume for context: {e}")

        result = await chain.ainvoke(
            {
                "title": vacancy.title,
                "description": vacancy.description,
                "default_cover_letter": self.settings.default_cover_letter or "",
                "resume_context": resume_context,
            }
        )
        return str(getattr(result, "content", ""))

    async def generate_answers(
        self,
        vacancy: Vacancy,
        questions: list[VacancyQuestion],
        resume_id: str | None = None,
    ) -> list[VacancyQuestionAnswer]:
        answers = []

        for q in questions:
            resume_context = ""
            if resume_id:
                try:
                    resume_context = self.query_resume(q.question, resume_id)
                except Exception as e:
                    logger.error(
                        f"Failed to query resume for question '{q.question}': {e}"
                    )

            match q:
                case TextQuestion(question=question):
                    prompt = PromptTemplate.from_template(
                        self.settings.prompts.text_answer
                    )
                    chain = prompt | self.llm.with_structured_output(TextAnswer)

                    result = await chain.ainvoke(
                        {
                            "title": vacancy.title,
                            "question": question,
                            "default_answers": self.settings.default_answers,
                            "resume_context": resume_context,
                        }
                    )
                    answers.append(result)
                case RadioQuestion(question=question):
                    prompt = PromptTemplate.from_template(
                        self.settings.prompts.radio_answer
                    )
                    chain = prompt | self.llm.with_structured_output(RadioAnswer)

                    result = await chain.ainvoke(
                        {
                            "title": vacancy.title,
                            "question": question,
                            "options": q.format_options(),
                            "default_answers": self.settings.default_answers,
                            "resume_context": resume_context,
                        }
                    )
                    answers.append(result)
                case CheckboxQuestion(question=question):
                    prompt = PromptTemplate.from_template(
                        self.settings.prompts.checkbox_answer
                    )
                    chain = prompt | self.llm.with_structured_output(CheckboxAnswer)

                    result = await chain.ainvoke(
                        {
                            "title": vacancy.title,
                            "question": question,
                            "options": q.format_options(),
                            "default_answers": self.settings.default_answers,
                            "resume_context": resume_context,
                        }
                    )
                    answers.append(result)
                case RadioWithTextQuestion(question=question):
                    prompt = PromptTemplate.from_template(
                        self.settings.prompts.radio_answer
                    )
                    chain = prompt | self.llm.with_structured_output(
                        RadioWithTextAnswer
                    )

                    result = await chain.ainvoke(
                        {
                            "title": vacancy.title,
                            "question": question,
                            "options": q.format_options(),
                            "default_answers": self.settings.default_answers,
                            "resume_context": resume_context,
                        }
                    )
                    answers.append(result)
                case _:
                    raise ValueError(f"Unsupported question type: {question}")

        return answers
