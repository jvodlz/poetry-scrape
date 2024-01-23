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

def get_last_page(soup) -> int:
    last_link_tag = soup.find("li", class_=re.compile("pager__item--last"))
    if last_link_tag is None:
        print("No other pages available to navigate")
        return -1
    last_page_link = last_link_tag.find("a")["href"]
    match = re.search(r"page=(\d+)", last_page_link)
    return int(match.group(1))

def clean_title(title):
    pattern = re.compile(r"^\[(.*)\]")
    match = pattern.match(title)
    if match:
        return match.group(1)
    return title

def clean_author(author):
    if author == "":
        return "[unkown]"
    return author

def clean_year(year):
    if year == "":
        return "[undated]"
    return year

def poem_scraper(poem_href) -> str:
    # Visit Poem
    poem_page_url = POEM_URL_PREFIX + poem_href
    poem_result = requests.get(poem_page_url)
    poem_soup = BeautifulSoup(poem_result.text, "html.parser")

    #  Get block with Poem 
    poem_block = poem_soup.find("div", class_="field--body")
    return " ".join(poem_block.strings).strip()

def insert_poem(poem_text, fields):
    with Session(engine) as session:
        title, author, year = fields

        poem_load = Poem(
            title = title,
            author = author,
            year = year,
            text = poem_text
        )
        session.add(poem_load)
        session.commit()
        print(f"--- Successfully inserted:  {fields}")
    session.close()


# Webscrapiing Logic
STARTING_URL_PREFIX = "https://poets.org/poems?field_occasion_target_id=All&field_poem_themes_target_id=1226&field_form_target_id=All&combine=&page="
POEM_URL_PREFIX = "https://poets.org"
page_num = 0
last_page_num = None
result = get_request(page_num)

#  Page navigation loop
while result.status_code == 200:
    print(f"====== Starting Page {page_num + 1} =====")

    soup = BeautifulSoup(result.text, "html.parser")

    if last_page_num is None:
        last_page_num = get_last_page(soup)

    if last_page_num < page_num:
        break

    '''
    Links in table, and create fields list of tuples
    '''
    poem_links = []
    fields = []
    table = soup.find("table")
    if table is None:
        print("No more pages available")
        break

    for row in table.find_all("tr"):
        link = row.find("a")

        if link:
            # fields parsing
            meta_columns = row.find_all("td")
            title, author, year = (
                meta_columns[0].text.strip(), 
                meta_columns[1].text.strip(), 
                meta_columns[2].text.strip()
            )

            # if not audio only, add link and meta
            if "audio only" not in title:
                title = clean_title(title)
                author = clean_author(author)
                year = clean_year(year)
                fields.append((title, author, year))
                poem_links.append(link["href"])

    '''
    Visit each poem and write to db each time poem is visited
    '''
    for poem_href in poem_links:
        poem_text = poem_scraper(poem_href)
        unpack = fields.pop(0)
        insert_poem(poem_text, unpack)

    print(f"====== Page {page_num + 1} Completed =====")

    # Not overwhelm server
    time.sleep(random.randrange(1,5))

    page_num += 1
    result = get_request(page_num)

print("====== Finished =======")
