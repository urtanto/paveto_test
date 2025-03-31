import uuid

from sqlalchemy import Column, ForeignKey, String, UUID
from sqlalchemy.orm import relationship

from database import SqlAlchemyBase


class AudioFile(SqlAlchemyBase):
    __tablename__ = "audio_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
    filename = Column(String, nullable=False)
    user_id = Column(String, ForeignKey("users.id"))

    owner = relationship("User", back_populates="audio_files")
