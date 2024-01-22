from bs4 import BeautifulSoup
import requests, json
from sqlalchemy import create_engine
from sqlalchemy import String
from sqlalchemy.orm import Session

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column

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
            f"year={self.year!r}, text={self.text!r})"
        )

engine = create_engine("sqlite:///poems.db")
Base.metadata.create_all(engine)

# Webscrapiing Logic

# TODO: make page update -- inside while loop (inside session). If catch err -> stop
STARTING_URL = "https://poets.org/poems?field_occasion_target_id=All&field_poem_themes_target_id=1046&field_form_target_id=All&combine=&page=0"
result = requests.get(STARTING_URL)
soup = BeautifulSoup(result.text, "html.parser")
# print(soup.prettify())

POEM_URL_PREFIX = "https://poets.org"

# Creating db
with Session(engine) as session:
    # TODO: Some Loop for page navigation HERE

    '''
    Links in table, and create metadata list of tuples
    '''
    poem_links = []
    metadata = []
    table = soup.find("table")

    for row in table.find_all("tr"):
        link = row.find("a")

        if link:
            poem_links.append(link["href"])

            # metadata parsing
            meta_columns = row.find_all("td")
            title, author, year = (
                meta_columns[0].text.strip(), 
                meta_columns[1].text.strip(), 
                meta_columns[2].text.strip()
            )
            metadata.append((title, author, year))

    '''
    Visit each poem and write to csv each time poem is visited
    '''

    for poem_href in poem_links:

        # Visit Poem
        poem_page_url = POEM_URL_PREFIX + poem_href
        poem_result = requests.get(poem_page_url)
        poem_soup = BeautifulSoup(poem_result.text, "html.parser")

        #  Get block with Poem 
        poem_block = poem_soup.find("div", class_="field--body")

        filter_newline = [line.rstrip() for line in poem_block.stripped_strings if line != "\n"]
        poem_text = "\n".join(filter_newline).strip()

        # # Poem to db
        unpack = metadata.pop(0)
        # print(unpack)
        title, author, year = unpack

        poem_load = Poem(
            title = title,
            author = author,
            year = year,
            text = poem_text
        )

        session.add(poem_load)

    session.commit()
    session.close()

print("====== Success =======")
