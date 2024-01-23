from scraper import poem_scraper
from database import create_db

if __name__ == "__main__":
    engine = create_db()
    poem_scraper(engine)
