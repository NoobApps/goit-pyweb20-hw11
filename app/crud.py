from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, extract, and_
from datetime import date, timedelta
from models import Contact
from schemas import ContactCreate, ContactUpdate
from logger import logger

async def create_contact(db: AsyncSession, contact_data: ContactCreate) -> Contact:
    contact = Contact(**contact_data.model_dump())
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    logger.info(f"Створено новий контакт ID={contact.id} ({contact.email})")
    return contact

async def get_contacts(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 100, 
    query: str | None = None
) -> list[Contact]:
    stmt = select(Contact)
    if query:
        search_pattern = f"%{query}%"
        stmt = stmt.where(
            or_(
                Contact.first_name.ilike(search_pattern),
                Contact.last_name.ilike(search_pattern),
                Contact.email.ilike(search_pattern)
            )
        )
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())

async def get_contact_by_id(db: AsyncSession, contact_id: int) -> Contact | None:
    stmt = select(Contact).where(Contact.id == contact_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def update_contact(db: AsyncSession, contact_id: int, contact_data: ContactUpdate) -> Contact | None:
    contact = await get_contact_by_id(db, contact_id)
    if not contact:
        return None
    
    update_dict = contact_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(contact, key, value)

    await db.commit()
    await db.refresh(contact)
    logger.info(f"Оновлено контакт ID={contact_id}")
    return contact

async def delete_contact(db: AsyncSession, contact_id: int) -> Contact | None:
    contact = await get_contact_by_id(db, contact_id)
    if not contact:
        return None
    
    await db.delete(contact)
    await db.commit()
    logger.info(f"Видалено контакт ID={contact_id}")
    return contact

async def get_upcoming_birthdays(db: AsyncSession, days: int = 7) -> list[Contact]:
    """
    Знаходить контакти, день народження яких наступає протягом наступних `days` днів.
    Корректно обробляє перехід через межу місяця/року.
    """
    today = date.today()
    upcoming_dates = [(today + timedelta(days=i)) for i in range(days + 1)]
    conditions = [
        and_(
            extract('month', Contact.birthday) == d.month,
            extract('day', Contact.birthday) == d.day
        )
        for d in upcoming_dates
    ]
    
    stmt = select(Contact).where(or_(*conditions))
    result = await db.execute(stmt)
    return list(result.scalars().all())