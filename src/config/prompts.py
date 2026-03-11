from langchain_core.prompts import PromptTemplate

COVER_LETTER_PROMPT = PromptTemplate.from_template(
    "You are a professional applying for a job. Write a short, professional cover letter "
    "for the following vacancy. The output should ONLY contain the cover letter text.\n\n"
    "Job Title: {title}\n"
    "Description: {description}\n"
)

TEXT_ANSWER_PROMPT = PromptTemplate.from_template(
    "You are applying for a job. Answer this question based on the vacancy details.\n"
    "Vacancy Title: {title}\nQuestion: {question}\nProvide a concise text answer."
)

RADIO_ANSWER_PROMPT = PromptTemplate.from_template(
    "You are applying for a job. Answer this multiple choice question.\n"
    "Vacancy Title: {title}\nQuestion: {question}\nOptions: {options}\nProvide the index of the best option."
)

CHECKBOX_ANSWER_PROMPT = PromptTemplate.from_template(
    "You are applying for a job. Answer this multiple choice question (multiple answers allowed).\n"
    "Vacancy Title: {title}\nQuestion: {question}\nOptions: {options}\nProvide the indices of the best options."
)
