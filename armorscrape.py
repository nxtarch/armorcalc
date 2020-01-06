#! python3

# scraper for dark souls armor

import requests
import re
import sqlite3
from bs4 import BeautifulSoup
import time


# connecting to actual database
conn = sqlite3.connect("./databases/armor.db")

# testing connection
# conn = sqlite3.connect(":memory:")

c = conn.cursor()

with conn:
    c.execute("""CREATE TABLE IF NOT EXISTS armor(
    slot TEXT,
    name TEXT,
    durability REAL,
    weight REAL,
    physical REAL,
    strike REAL,
    slash REAL,
    thrust REAL,
    magic REAL,
    fire REAL,
    lightning REAL,
    poise REAL,
    bleed REAL,
    poison REAL,
    curse REAL)""")

# create tuple of item types which will be added to table
# tables on website contain no slot info but are always
# in this order so we map these to the items
item_slots = ("helmet", "chest", "gauntlets", "boots")

r = requests.get("https://darksouls.wiki.fextralife.com/Armor").text

soup = BeautifulSoup(r, "lxml")

delay = 0

for a in soup.find_all('a', class_ = "wiki_link wiki_tooltip", href=re.compile(r"\+Set")):

    # adaptive delay based on website response time
    time.sleep(delay)
    start = time.time()

    # website has both local and url reference links, this formats the request correctly
    if ".com" in a["href"]:
        page = requests.get(a["href"])
    else:
        page = requests.get(f"https://darksouls.wiki.fextralife.com{a['href']}")

    end = time.time()

    response_time = end - start

    delay = response_time * 10

    # if bad response from the link we skip attempting to process and move to next link
    if not page.ok:
        continue

    # print(page.url)

    info = BeautifulSoup(page.text, "lxml")

    # attempts to find second table on page, which has relevant info
    try:
        table = info.find_all("table")[1]
    except IndexError:
        continue

    # creates the iterator for pulling item type since info is not in table
    slots = iter(item_slots)

    # each row contains the name and stats of one armor item in the set
    for row in table.tbody:

        # list for containing scraped info to be stored in db
        vals = []

        # exception handling when trying to parse table data
        try:
            data = row.find_all("td")
        except AttributeError as e:
            pass
            # print(e)
        else:
            # first row only has <th> tags, this skips it
            if not data:
                continue

            # Names of items are contained in <a> tags which link to their pages
            # This check skips the total row at bottom of table preventing StopIteration Exception
            elif data[0].find('a') is not None:

                # each page's table is in order of the slots iterator
                vals.append(next(slots))
                for line in data:
                    vals.append(line.text)
                    # print(line.text)

                # once vals is populated we print the values and insert them into db
                with conn:
                    print(f"Inserting {vals}")
                    c.execute(f"INSERT INTO armor VALUES ({', '.join('?' for i in range(15))})", tuple(vals))

# finally insertion is confirmed by printing all values from db
with conn:
    for line in c.execute("SELECT * FROM armor"):
        print(line)
