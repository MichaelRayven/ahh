from typing import Annotated, Literal, Self

from pydantic import BaseModel, EmailStr, Field, TypeAdapter, model_validator
from pydantic_extra_types.phone_numbers import PhoneNumber, PhoneNumberValidator

_PhoneNumberType = Annotated[
    PhoneNumber,
    PhoneNumberValidator(
        supported_regions=["RU", "KZ", "BY", "UZ"], number_format="E164"
    ),
]


class AccountDetails(BaseModel):
    login_type: Literal["phone", "email"]
    login: str
    password: str | None = Field(
        None, description="Optional password, 2FA will be used if not provided"
    )

    @model_validator(mode="after")
    def validate_login(self) -> Self:
        if self.login_type == "phone":
            self.login = TypeAdapter(_PhoneNumberType).validate_python(self.login)
        elif self.login_type == "email":
            self.login = TypeAdapter(EmailStr).validate_python(self.login)

        return self


class TwoFactorDetails(BaseModel):
    two_factor_code: str = Field(
        ..., min_length=4, max_length=4, pattern=r"^\d{4}$", description="2FA code"
    )
