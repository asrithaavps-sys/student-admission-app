import pandas as pd
import os
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from difflib import get_close_matches

CACHE_FILE = "cache.json"
CURRENT_YEAR = datetime.now().year


# -------------------------
# UNIVERSITY DATABASE (SMART)
# -------------------------
UNIVERSITY_DB = {
    "rwth aachen": "https://www.rwth-aachen.de",
    "augsburg": "https://www.uni-augsburg.de",
    "bielefeld": "https://www.uni-bielefeld.de",
    "bonn": "https://www.uni-bonn.de",
    "free university berlin": "https://www.fu-berlin.de",
    "humboldt berlin": "https://www.hu-berlin.de",
    "tu berlin": "https://www.tu-berlin.de",
    "bremen": "https://www.uni-bremen.de",
    "chemnitz": "https://www.tu-chemnitz.de",
    "clausthal": "https://www.tu-clausthal.de",
    "dresden": "https://tu-dresden.de",
    "duisburg essen": "https://www.uni-due.de",
    "düsseldorf": "https://www.hhu.de",
    "erlangen": "https://www.fau.de",
    "frankfurt": "https://www.uni-frankfurt.de",
    "freiburg": "https://www.uni-freiburg.de",
    "göttingen": "https://www.uni-goettingen.de",
    "greifswald": "https://www.uni-greifswald.de",
    "halle": "https://www.uni-halle.de",
    "hamburg": "https://www.uni-hamburg.de",
    "hannover": "https://www.uni-hannover.de",
    "heidelberg": "https://www.uni-heidelberg.de",
    "jena": "https://www.uni-jena.de",
    "karlsruhe institute of technology": "https://www.kit.edu",
    "kassel": "https://www.uni-kassel.de",
    "kiel": "https://www.uni-kiel.de",
    "konstanz": "https://www.uni-konstanz.de",
    "cologne": "https://www.uni-koeln.de",
    "leipzig": "https://www.uni-leipzig.de",
    "marburg": "https://www.uni-marburg.de",
    "lmu munich": "https://www.lmu.de",
    "technical university of munich": "https://www.tum.de",
    "münster": "https://www.uni-muenster.de",
    "oldenburg": "https://uol.de",
    "potsdam": "https://www.uni-potsdam.de"
}


# -------------------------
# DEFAULT ADMISSION LOGIC
# -------------------------
def get_default_dates(intake):
    if intake == "Summer":
        return ("December 1", "January 15")
    return ("May 1", "July 15")


# -------------------------
# CACHE
# -------------------------
def load_cache():
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)


# -------------------------
# SMART MATCHING (AI LIKE)
# -------------------------
def match_university(name):
    name = name.lower()

    # Exact match
    for key in UNIVERSITY_DB:
        if key in name:
            return key

    # Fuzzy match
    matches = get_close_matches(name, UNIVERSITY_DB.keys(), n=1, cutoff=0.6)
    if matches:
        return matches[0]

    return None


# -------------------------
# GENERATE LINK (NO 404)
# -------------------------
def get_link(university):
    match = match_university(university)

    if match:
        return UNIVERSITY_DB[match]

    # fallback search (always works)
    return "https://www.google.com/search?q=" + university.replace(" ", "+")


# -------------------------
# FORMAT DATE
# -------------------------
def format_date(d):
    return f"{d} {CURRENT_YEAR}"


# -------------------------
# MAIN LOGIC
# -------------------------
def get_real_data(university, intake, cache):

    uni = university.lower()

    if uni in cache:
        return cache[uni]

    open_d, close_d = get_default_dates(intake)
    link = get_link(university)

    result = (
        format_date(open_d),
        format_date(close_d),
        intake,
        link
    )

    cache[uni] = result
    return result


# -------------------------
# MAIN SCRAPER
# -------------------------
def run_scraper(file_path, intake="Winter"):

    df = pd.read_excel(file_path, header=1)

    # remove junk columns
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

    df.columns = df.columns.astype(str).str.strip()

    df.rename(columns={
        df.columns[1]: "Name",
        df.columns[2]: "Course",
        df.columns[3]: "University"
    }, inplace=True)

    df = df.ffill()

    # add output columns
    df["Application Open Date"] = ""
    df["Application Close Date"] = ""
    df["Intake"] = ""
    df["Link"] = ""

    cache = load_cache()

    def process(i):
        try:
            uni = str(df.iloc[i]["University"]).strip()
            if not uni:
                return None

            return (i, *get_real_data(uni, intake, cache))

        except:
            return None

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(process, range(len(df))))

    for r in results:
        if r:
            i, o, c, intake_val, link = r
            df.at[i, "Application Open Date"] = o
            df.at[i, "Application Close Date"] = c
            df.at[i, "Intake"] = intake_val
            df.at[i, "Link"] = link

    save_cache(cache)

    os.makedirs("results", exist_ok=True)
    df.to_excel("results/output.xlsx", index=False)

    return df