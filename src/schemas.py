from typing import Literal

from pydantic import BaseModel, Field, computed_field


class SearchQuery(BaseModel):
    text: str | None = Field(None, description="Ключевые слова")
    search_field: list[Literal["name", "company_name", "description"]] = Field(
        default_factory=list, description="Поля для поиска ключевых слов"
    )
    excluded_text: str | None = Field(None, description="Исключенные слова")
    area: list[int] | None = Field(None, description="Код региона")
    salary: int | None = None
    salary_mode: (
        Literal["MONTH", "HOUR", "SHIFT", "FLY_IN_FLY_OUT", "SERVICE"] | None
    ) = None
    currency_code: Literal["RUR", "USD", "EUR"] = "RUR"
    accept_temporary: bool | None = Field(
        None, description="Оформление по ГПХ или по совместительству"
    )
    experience: Literal[
        "doesNotMatter", "noExperience", "between1And3", "between3And6", "moreThan6"
    ] = Field("doesNotMatter", description="Требуемый опыт работы")
    employment_form: list[Literal["FULL", "PROJECT", "PART", "FLY_IN_FLY_OUT"]] = Field(
        default_factory=list, description="Тип занятости"
    )
    work_format: list[Literal["REMOTE", "ON_SITE", "HYBRID", "FIELD_WORK"]] = Field(
        default_factory=list, description="Формат работы"
    )
    order_by: Literal["relevance", "publication_time", "salary_desc", "salary_asc"] = (
        Field("relevance", description="Сортировка")
    )
    search_period: Literal[0, 1, 3, 7, 30] = Field(
        0,
        description="Период поиска вакансий",
    )
    items_on_page: Literal[20, 50, 100] = Field(
        100, description="Количество вакансий на странице"
    )
    low_performance: bool | None = Field(
        None, description="Вакансии у которых меньше 10 откликов"
    )
    accredited_it: bool | None = Field(None, description="Аккредитованные IT-компании")

    @computed_field
    @property
    def url_params(self) -> str:
        params = dict.keys(self.__fields__)
        result = ""
        for param in params:
            value = getattr(self, param)
            if value:
                if isinstance(value, list):
                    for item in value:
                        result += f"&{param}={item}"
                else:
                    result += f"&{param}={value}"

        return result
