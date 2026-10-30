import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
# from fastapi.middleware.cors import CORSMiddleware##

from database import get_db, engine, Base
from schemas import ContactCreate, ContactUpdate, ContactResponse
from logger import logger
import crud as crud

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Автоматичне створення таблиць під час запуску (для розробки)
    logger.info("Ініціалізація бази даних...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Додаток успішно запущено.")
    yield
    logger.info("Зупинка додатка...")

app = FastAPI(
    title="Contacts REST API",
    description="API для управління контактами з можливістю пошуку та нагадування про дні народження.",
    version="1.0.0",
    lifespan=lifespan
)

# origins = ["*"]  # Дозволяє запити з будь-якого джерела

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,            # Дозволені джерела (origins)
#     allow_credentials=True,           # Дозвіл на передачу cookie/headers авторизації
#     allow_methods=["*"],              # Дозволені HTTP-методи (GET, POST, PUT, DELETE тощо)
#     allow_headers=["*"],              # Дозволені HTTP-заголовки
# )

@app.post("/contacts/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(contact: ContactCreate, db: AsyncSession = Depends(get_db)):
    logger.info(f"Запит на створення контакту email={contact.email}")
    return await crud.create_contact(db, contact)

@app.get("/contacts/", response_model=list[ContactResponse])
async def read_contacts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    query: str | None = Query(None, description="Пошук за ім'ям, прізвищем або email"),
    db: AsyncSession = Depends(get_db)
):
    return await crud.get_contacts(db, skip=skip, limit=limit, query=query)

@app.get("/contacts/upcoming-birthdays", response_model=list[ContactResponse])
async def upcoming_birthdays(db: AsyncSession = Depends(get_db)):
    logger.info("Запит контактів з днями народження на найближчі 7 днів")
    return await crud.get_upcoming_birthdays(db, days=7)

@app.get("/contacts/{contact_id}", response_model=ContactResponse)
async def read_contact(contact_id: int, db: AsyncSession = Depends(get_db)):
    contact = await crud.get_contact_by_id(db, contact_id)
    if not contact:
        logger.warning(f"Контакт з ID={contact_id} не знайдено")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Контакт не знайдено")
    return contact

@app.put("/contacts/{contact_id}", response_model=ContactResponse)
async def update_contact(contact_id: int, contact: ContactUpdate, db: AsyncSession = Depends(get_db)):
    updated_contact = await crud.update_contact(db, contact_id, contact)
    if not updated_contact:
        logger.warning(f"Неможливо оновити: контакт ID={contact_id} не знайдено")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Контакт не знайдено")
    return updated_contact

@app.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(contact_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await crud.delete_contact(db, contact_id)
    if not deleted:
        logger.warning(f"Неможливо видалити: контакт ID={contact_id} не знайдено")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Контакт не знайдено")
    return None

# Блок для прямого запуску файлу
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)