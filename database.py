from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String

class Base(DeclarativeBase):
    pass

class Poem(Base):
    __tablename__ = "poem"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String())
    author: Mapped[str] = mapped_column(String())
    year: Mapped[str] = mapped_column(String(4))
    text: Mapped[str] = mapped_column(String())

    def __repr__(self) -> str:
        return (
            f"Poem(id={self.id!r}, "
            f"title={self.title!r}, "
            f"year={self.year!r})"
        )

def create_db():
    engine = create_engine("sqlite:///poems.db")
    Base.metadata.create_all(engine)
    return engine
