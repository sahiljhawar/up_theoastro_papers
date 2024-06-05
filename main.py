import arxivscraper
import pandas as pd
import requests
import json
from bs4 import BeautifulSoup
from datetime import date
import datetime


def get_department_members():
    """
    Scrapes the department website for a list of people in the department.

    Outputs
    -------
        :names: (list of strs) names of members in the department.
    """

    URL = "https://www.uni-potsdam.de/en/theoretical-astrophysics/group/overview-1"
    page = requests.get(URL)

    soup = BeautifulSoup(page.content, "html.parser")

    divs = soup.find_all("div", class_="twentyfour columns up-content-contact-box-header")

    names = [div.find("h2").text.strip() for div in divs]

    replacements = {"ä": "ae", "ö": "oe", "ü": "ue", "Ä": "Ae", "Ö": "Oe", "Ü": "Ue"}

    cleaned_names = []
    for name in names:
        # Remove titles
        name = name.replace("Prof. ", "").replace("Dr. ", "").replace("Professor ", "")
        # Replace umlauts
        for umlaut, replacement in replacements.items():
            name = name.replace(umlaut, replacement)
        cleaned_names.append(name)

    return [name.lower() for name in cleaned_names]


def permutate_name(name):
    """
    Makes a list of potential permutations of a name.
    """
    parts = name.split(" ")

    # Handle cases with one part (shouldn't happen but just in case)
    if len(parts) == 1:
        return [name]

    # First and last name are always the first and last elements
    first = parts[0]
    last = parts[-1]

    # Middle names are everything in between
    middle_names = parts[1:-1]

    first_initial = first[0]
    permutations = [name]

    # Construct permutations with middle initials if there are any middle names
    if middle_names:
        initial_middle = " ".join([m[0] + "." for m in middle_names])
        permutations.append(f"{first_initial}. {initial_middle} {last}")
        permutations.append(f"{first_initial}. {last}")
        permutations.append(f"{last}, {first} {initial_middle}")
    else:
        permutations.append(f"{first_initial}. {last}")
        permutations.append(f"{last}, {first}")

    return permutations


def scrape_papers(days):
    """
    Scrapes arxiv for papers published in the last week.

    Output
    ------
        :df: (pd.DataFrame) object containing all the papers published on astro-oh in the last week.
    """
    today = date.today()

    week_ago = today - datetime.timedelta(days=days)
    
    def _category(category):

        scraper = arxivscraper.Scraper(
            category=category, date_from=week_ago.strftime("%Y-%m-%d"), date_until=today.strftime("%Y-%m-%d")
        )
        output = scraper.scrape()

        cols = ("id", "title", "categories", "abstract", "doi", "created", "updated", "authors", "affiliation", "url")

        return pd.DataFrame(output, columns=cols)
    
    astroph = _category("physics:astro-ph")
    grqc = _category("physics:gr-qc")

    df = pd.concat([astroph, grqc], ignore_index=True)
    df = df.drop_duplicates(subset='id')

    return df


def cross_match_papers(df, names):
    """
    Cross matches name permutations against the DataFrame author list and saves matched author names and papers as JSON.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing arxiv papers.
    names : list of str
        List of names to cross match against.

    Output
    ------
        :matches: dict
            Dictionary containing matched author names and their corresponding papers.
    """
    matches = {}

    for name in names:
        permutations = permutate_name(name)
        matched_papers = []
        for _, row in df.iterrows():
            for author in row["authors"]:
                if author in permutations:
                    matched_papers.append(
                        {
                            "title": row["title"],
                        }
                    )
                    break  # If one permutation matches, no need to check others

        # Ensure the key in matches is the original name, not the permutation
        if matched_papers:
            matches[name] = matched_papers

    return matches


if __name__ == "__main__":
    print("Fetching department members...")
    cleaned_names = get_department_members()
    print()

    print("Scraping arxiv for papers...")
    df = scrape_papers(7)
    print()

    print("Cross matching names and papers")

    matches = cross_match_papers(df, cleaned_names)
    today = date.today().strftime("%Y-%m-%d")

    with open(f"data/matched_authors_and_papers-{today}.json", "w") as f:
        json.dump(matches, f, indent=4)

    print(f"Data saved to matched_authors_and_papers-{today}.json")
