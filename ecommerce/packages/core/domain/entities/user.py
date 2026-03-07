from dataclasses import dataclass

from packages.core.domain.exceptions import ValidationError


@dataclass(slots=True)
class User:
    id: str
    email: str
    hashed_password: str
    is_admin: bool = False

    def __post_init__(self) -> None:
        if not self.id.strip():
            msg = "user id cannot be empty"
            raise ValidationError(msg)
        if "@" not in self.email or self.email.startswith("@") or self.email.endswith("@"):
            msg = "user email is invalid"
            raise ValidationError(msg)
        if not self.hashed_password.strip():
            msg = "hashed password cannot be empty"
            raise ValidationError(msg)
