import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select

from backend.auth import get_user, get_admin
from database import Database
from database.models import AudioFile, User

file_router = APIRouter(prefix="/file", tags=["file"])


@file_router.post("/upload")
async def upload_file(user: User = Depends(get_user), file: UploadFile = File(...)):
    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Incorrect file type. Only audio files are allowed")

    file_id = uuid.uuid4()

    directory = os.path.join("uploads", str(user.id))
    os.makedirs(directory, exist_ok=True)

    file_location = os.path.join(directory, str(file_id))
    with open(file_location, "wb") as f:
        content = await file.read()
        f.write(content)

    print(file.filename)

    async with await Database().get_session() as session:
        async with session.begin():
            audio_file = AudioFile(id=file_id, filename=file.filename, user_id=user.id)

            session.add(audio_file)
            await session.commit()

    return {
        "id": str(audio_file.id),
        "filename": audio_file.filename,
        "user_id": str(audio_file.user_id)
    }


@file_router.get("/all")
async def get_all_audio_files(_: User = Depends(get_user)):
    async with await Database().get_session() as session:
        async with session.begin():
            audio_files: list[AudioFile] = list(
                (
                    await session.execute(
                        select(AudioFile)
                    )
                ).scalars().all()
            )
            return [
                {
                    "id": str(file.id),
                    "filename": file.filename,
                    "user_id": str(file.user_id)
                } for file in audio_files
            ]

class AudioFileUpdate(BaseModel):
    filename: str

@file_router.patch("/{file_id}")
async def update_audio_file(
        file_id: uuid.UUID,
        update: AudioFileUpdate,
        _: User = Depends(get_user)
):
    async with await Database().get_session() as session:
        async with session.begin():
            audio_file: AudioFile = (
                await session.execute(
                    select(AudioFile).where(AudioFile.id == file_id)
                )
            ).unique().scalar_one_or_none()

            if not audio_file:
                raise HTTPException(status_code=404, detail="Audio file not found.")

            audio_file.filename = update.filename
            await session.commit()
    return {
        "id": str(audio_file.id),
        "filename": audio_file.filename,
        "user_id": str(audio_file.user_id)
    }

@file_router.get("/{file_id}")
async def get_audio_file(file_id: uuid.UUID, _: User = Depends(get_user)):
    async with await Database().get_session() as session:
        async with session.begin():
            audio_file: AudioFile = (
                await session.execute(
                    select(AudioFile).where(AudioFile.id == file_id)
                )
            ).unique().scalar_one_or_none()

            if not audio_file:
                raise HTTPException(status_code=404, detail="Audio file not found.")

            return {
                "id": str(audio_file.id),
                "filename": audio_file.filename,
                "user_id": str(audio_file.user_id)
            }

@file_router.delete("/{file_id}")
async def delete_audio_file(file_id: uuid.UUID, _: User = Depends(get_admin)):
    async with await Database().get_session() as session:
        async with session.begin():
            audio_file: AudioFile = (
                await session.execute(
                    select(AudioFile).where(AudioFile.id == file_id)
                )
            ).unique().scalar_one_or_none()

            if not audio_file:
                raise HTTPException(status_code=404, detail="Audio file not found.")

            filepath = os.path.join("uploads", str(audio_file.user_id), str(audio_file.id))
            os.remove(filepath)

            await session.delete(audio_file)
            await session.commit()