import re
import uuid
import uvicorn
from fastapi.routing import APIRouter
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, field_validator, ValidationInfo
from sqlalchemy import Column, Boolean, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from config import settings

##############################################
# BLOCK FOR COMMON INTERACTION WITH DATABASE #
##############################################

# create engine
engine = create_async_engine(
    str(settings.SQLALCHEMY_DATABASE_URI), future=True, echo=True
)

# create session
assync_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

##############################
# BLOCK WITH DATABASE MODELS #
##############################

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    is_active = Column(Boolean(), default=True)


###########################################################
# BLOCK FOR INTERACTION WITH DATABASE IN BUSINESS CONTEXT #
###########################################################


class UserDAL:
    """Data Access Layer for operating user info"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_user(self, name: str, surname: str, email: str) -> User:
        new_user = User(
            name=name,
            surname=surname,
            email=email,
        )
        self.db_session.add(new_user)
        await self.db_session.flush()
        return new_user


#########################
# BLOCK WITH API MODELS #
#########################

LETTER_MATCH_PATTERN = re.compile(r"^[a-zA-Z\-]+$")


class TunedModel(BaseModel):
    class Config:
        """pydantic convert even non dict obj to json"""

        from_attributes = True


class ShowUser(TunedModel):
    user_id: uuid.UUID
    name: str
    surname: str
    email: str
    is_active: bool


class UserCreate(BaseModel):
    name: str
    surname: str
    email: EmailStr

    @field_validator("name", mode="before")
    def validate_name(cls, v: str):
        if not LETTER_MATCH_PATTERN.match(v):
            raise HTTPException(
                status_code=422, detail="Name should contains only letters"
            )
        return v

    @field_validator("surname", mode="before")
    def validate_surname(cls, v: str):
        if not LETTER_MATCH_PATTERN.match(v):
            raise HTTPException(
                status_code=422, detail="Surname should contains only letters"
            )
        return v


##########################
# BLOCK WITH API ROUTERS #
##########################

app = FastAPI(title="my-little-blog")

user_router = APIRouter()


async def _create_new_user(body: UserCreate) -> ShowUser:
    async with assync_session() as session:
        async with session.begin():
            user_dal = UserDAL(session)
            user = await user_dal.create_user(
                name=body.name,
                surname=body.surname,
                email=body.email,
            )
            return ShowUser(
                user_id=user.user_id,
                name=user.name,
                surname=user.surname,
                email=user.email,
                is_active=user.is_active,
            )


@user_router.post("/", response_model=ShowUser)
async def create_user(body: UserCreate) -> ShowUser:
    return await _create_new_user(body)


main_api_router = APIRouter()

main_api_router.include_router(user_router, prefix="/user", tags=["Users"])
app.include_router(main_api_router)

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
