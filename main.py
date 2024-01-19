'''
Poems on friendship
1) Get links in table

'''

from bs4 import BeautifulSoup
import requests, json, csv

# TODO: make page update -- inside while loop. If catch err -> stop
STARTING_URL = "https://poets.org/poems?field_occasion_target_id=All&field_poem_themes_target_id=1046&field_form_target_id=All&combine=&page=0"
result = requests.get(STARTING_URL)
soup = BeautifulSoup(result.text, "html.parser")
# print(soup.prettify())

POEM_URL_PREFIX = "https://poets.org"
META_FIELDS = ["Title", "Author", "Year", "Poem Text"]

with open("poems.csv", "w", newline="", encoding="utf-8") as csvfile:
    metadata = []
    writer = csv.writer(csvfile)
    writer.writerow(META_FIELDS)

    #### Some Loop for page navigation
    # Modularise operations (once first page is written)

    '''
    Links in table, and create metadata list of tuples
    '''
    poem_links = []
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

        # Prep getting poem
        tag = poem_soup.find("script")
        json_data = json.loads(tag.string)
        poem_text = json_data["@graph"][0]["description"]

        # Poem to CSV
        unpack = metadata.pop(0)
        title, author, year = unpack
        writer.writerow([
            title,
            author,
            year,
            poem_text
        ])

    print("==== Completed Page ====")