import arxivscraper
import pandas as pd
import requests
import json
from bs4 import BeautifulSoup
from datetime import date
import datetime
from name import permutate_name, load_names

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
