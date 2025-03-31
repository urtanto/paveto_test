import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select

from backend.auth import get_admin, get_user
from database import Database
from database.models import AudioFile, User

file_router = APIRouter(prefix="/file", tags=["file"])


class AudioFileResponse(BaseModel):
    """
    Модель ответа для аудиофайла.
    """
    id: str = Field(..., description="Идентификатор аудиофайла")
    filename: str = Field(..., description="Исходное имя файла")
    filepath: str = Field(..., description="Путь к файлу на сервере")
    user_id: str = Field(..., description="Идентификатор пользователя")


class AudioFilesListResponse(BaseModel):
    """
    Модель ответа для списка аудиофайлов.
    """
    files: list[AudioFileResponse] = Field(..., description="Список аудиофайлов")


class AudioFileUpdate(BaseModel):
    """
    Модель для обновления имени аудиофайла.
    """
    filename: str = Field(..., description="Новое имя аудиофайла")


@file_router.post("/upload", response_model=AudioFileResponse)
async def upload_file(user: User = Depends(get_user), file: UploadFile = File(...)):
    """
    Загружает аудиофайл и сохраняет его на сервере.

    Принимает файл, проверяет его тип (должен быть аудио), сохраняет файл
    в директории, зависящей от идентификатора пользователя, и создаёт запись
    в базе данных.
    """
    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Incorrect file type. Only audio files are allowed")

    file_id = uuid.uuid4()

    directory = os.path.join("uploads", str(user.id))
    os.makedirs(directory, exist_ok=True)

    filename, file_extension = os.path.splitext(file.filename)
    file_location = os.path.join(directory, f"{file_id}{file_extension}")
    with open(file_location, "wb") as f:
        content = await file.read()
        f.write(content)

    async with await Database().get_session() as session:
        async with session.begin():
            audio_file = AudioFile(id=file_id, filename=file.filename, user_id=user.id)

            session.add(audio_file)
            await session.commit()

    return AudioFileResponse(
        id=str(audio_file.id),
        filename=audio_file.filename,
        filepath=file_location,
        user_id=str(audio_file.user_id)
    )


@file_router.get("/all", response_model=AudioFilesListResponse)
async def get_all_audio_files(_: User = Depends(get_user)):
    """
    Возвращает список всех аудиофайлов.
    """
    async with await Database().get_session() as session:
        async with session.begin():
            audio_files: list[AudioFile] = list(
                (
                    await session.execute(
                        select(AudioFile)
                    )
                ).scalars().all()
            )
            files = [
                AudioFileResponse(
                    id=str(file.id),
                    filename=file.filename,
                    filepath=os.path.join("uploads", str(file.user_id), str(file.id)),
                    user_id=str(file.user_id)
                ) for file in audio_files
            ]
            return AudioFilesListResponse(files=files)


@file_router.get("/user/{user_id}", response_model=AudioFilesListResponse)
async def get_user_files(
        user_id: uuid.UUID,
        _: User = Depends(get_user)
):
    async with await Database().get_session() as session:
        async with session.begin():
            audio_files: list[AudioFile] = list(
                (
                    await session.execute(
                        select(AudioFile).where(AudioFile.user_id == user_id)
                    )
                ).scalars().all()
            )

            files = [
                AudioFileResponse(
                    id=str(file.id),
                    filename=file.filename,
                    filepath=os.path.join("uploads", str(file.user_id), str(file.id)),
                    user_id=str(file.user_id)
                ) for file in audio_files
            ]
            return AudioFilesListResponse(files=files)


@file_router.patch("/{file_id}", response_model=AudioFileResponse)
async def update_audio_file(
        file_id: uuid.UUID,
        update: AudioFileUpdate,
        _: User = Depends(get_user)
):
    """
    Обновляет данные аудиофайла.

    Находит аудиофайл по идентификатору, обновляет его имя и сохраняет изменения в базе данных.
    """
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
    return AudioFileResponse(
        id=str(audio_file.id),
        filename=audio_file.filename,
        filepath=os.path.join("uploads", str(audio_file.user_id), str(audio_file.id)),
        user_id=str(audio_file.user_id)
    )


@file_router.get("/{file_id}", response_model=AudioFileResponse)
async def get_audio_file(file_id: uuid.UUID, _: User = Depends(get_user)):
    """
    Возвращает данные аудиофайла по его идентификатору.
    """
    async with await Database().get_session() as session:
        async with session.begin():
            audio_file: AudioFile = (
                await session.execute(
                    select(AudioFile).where(AudioFile.id == file_id)
                )
            ).unique().scalar_one_or_none()

            if not audio_file:
                raise HTTPException(status_code=404, detail="Audio file not found.")

            return AudioFileResponse(
                id=str(audio_file.id),
                filename=audio_file.filename,
                filepath=os.path.join("uploads", str(audio_file.user_id), str(audio_file.id)),
                user_id=str(audio_file.user_id)
            )


@file_router.delete("/{file_id}")
async def delete_audio_file(file_id: uuid.UUID, _: User = Depends(get_admin)):
    """
    Удаляет аудиофайл по его идентификатору.

    Находит аудиофайл в базе данных, удаляет файл с диска и запись из базы данных.
    Для выполнения операции требуется статус администратора.
    """
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
