from bs4 import BeautifulSoup
import requests, re, time, random
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

# Helper functions
def get_request(page_num):
    return requests.get(f"{STARTING_URL_PREFIX}{page_num}")

def get_last_page(soup):
    last_link_tag = soup.find("li", class_=re.compile("pager__item--last"))
    last_page_link = last_link_tag.find("a")["href"]
    match = re.search(r"page=(\d+)", last_page_link)
    return match.group(1)

# Webscrapiing Logic
STARTING_URL_PREFIX = "https://poets.org/poems?field_occasion_target_id=All&field_poem_themes_target_id=1226&field_form_target_id=All&combine=&page="
POEM_URL_PREFIX = "https://poets.org"
page_num = 0
last_page_num = 0
result = get_request(page_num)

#  Page navigation loop
while result.status_code == 200:
    print(f"====== Starting Page {page_num + 1} =====")

    soup = BeautifulSoup(result.text, "html.parser")
    # print(soup.prettify())

    #  if last page not set
    if last_page_num is None:
        last_page_num = get_last_page(soup)
        # print(last_page_num)

    # TODO: page_num < last_page_num

    # Create/Start db Session
    with Session(engine) as session:
        '''
        Links in table, and create metadata list of tuples
        '''
        poem_links = []
        metadata = []
        table = soup.find("table")

        for row in table.find_all("tr"):
            link = row.find("a")

            if link:
                # metadata parsing
                meta_columns = row.find_all("td")
                title, author, year = (
                    meta_columns[0].text.strip(), 
                    meta_columns[1].text.strip(), 
                    meta_columns[2].text.strip()
                )

                # if not audio only, add link and meta
                if "audio only" not in title:
                    metadata.append((title, author, year))
                    poem_links.append(link["href"])

        '''
        Visit each poem and write to db each time poem is visited
        '''

        # TODO: write poem_scraper fn
        # TODO: write to db in separate fn
        for poem_href in poem_links:
            # Visit Poem
            poem_page_url = POEM_URL_PREFIX + poem_href
            poem_result = requests.get(poem_page_url)
            poem_soup = BeautifulSoup(poem_result.text, "html.parser")

            #  Get block with Poem 
            poem_block = poem_soup.find("div", class_="field--body")

            poem_text = "".join(poem_block.strings).strip()

            # Poem to db
            unpack = metadata.pop(0)
            print(unpack)
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

        print(f"====== Page {page_num + 1} Completed =====")

        # Not overwhelm server
        time.sleep(random.randrange(1,5))

        page_num += 1
        result = get_request(page_num)

print("====== Success =======")
