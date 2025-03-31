import uuid

from sqlalchemy import Boolean, Column, String, UUID
from sqlalchemy.orm import relationship

from database import SqlAlchemyBase


class User(SqlAlchemyBase):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
    yandex_id = Column(String, unique=True, index=True, nullable=True)
    email = Column(String, unique=True, nullable=True)
    name = Column(String, nullable=True)
    is_superuser = Column(Boolean, default=False)

    audio_files = relationship("AudioFile", back_populates="owner")
