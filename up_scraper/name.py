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


def load_names():
    """
    Load names from a file.
    """
    with open('names_list.txt', 'r') as file:
        names_list = file.readlines()

    return [name.strip() for name in names_list]