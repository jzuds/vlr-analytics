import os
import re
from typing import Dict, List, Optional, Set, Union, Tuple

import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.vlr.gg"
SIDES_CLASS = ["mod-t", "mod-ct", "mod-both"]


def get_webpage_data(url, params: Optional[str] = None) -> BeautifulSoup:
    """Fetches a webpage result as a BeautifulSoup object using the html.parser."""
    response = requests.get(url, params)
    return BeautifulSoup(response.content, "html.parser")


def find_all_table_tags(bs4_object: BeautifulSoup):
    """Extracts table data from a BeautifulSoup object."""
    return bs4_object.find_all("table")


def get_completed_matches(page:int = 1) -> List[Tuple[str]]:
    """Gets a list of match urls for a given page.
    Source example: https://www.vlr.gg/matches/results
    """
    
    results_url = f"{BASE_URL}/matches/results"
    PAGE_NUM = page
    vlr_params = {"page": PAGE_NUM}
    bs4_results = get_webpage_data(url=results_url, params=vlr_params)

    game_links = bs4_results.find_all("a", class_="match-item")
    pattern = r'/(\d+)/([a-z0-9-]+)'
    matches_on_page = []
    for game in game_links:
        game_href = game.get("href")
        match = re.match(pattern, game_href)
        if match:
            match_id = match.group(1)
            match_name = match.group(2)
            match_info = (match_id, match_name)
            matches_on_page.append(match_info)
    return matches_on_page

def get_match_overview_data(
    match_id: int, match_name: str, output_dir: Optional[str] = None
) -> Set[pd.DataFrame]:
    """Gets the raw match overview data from a specified game.
    Source example: https://www.vlr.gg/378662/gen-g-vs-sentinels-valorant-champions-2024-opening-b/?game=all&tab=overview
    """

    match_url = f"{BASE_URL}/{match_id}/{match_name}"
    vlr_params = {"game": "all", "tab": "overview"}
    bs4_overview = get_webpage_data(url=match_url, params=vlr_params)

    game_id_divs = bs4_overview.find_all("div", class_="vm-stats-game")
    game_ids = [id_.get("data-game-id") for id_ in game_id_divs]

    bs4_table_data = find_all_table_tags(bs4_overview)
    df = pd.DataFrame()
    headers = [
        "Rating",
        "Average Combat Score",
        "Kills",
        "Deaths",
        "Assists",
        "Kills - Deaths",
        "KAST %",
        "Average Damage per Round",
        "Headshot %",
        "First Kills",
        "First Deaths",
        "Kills - Deaths",
        "Player Side",
        "Match ID",
        "Map ID",
        "Agent",
        "Player Name",
        "Org",
    ]
    for idx, table in enumerate(bs4_table_data):
        # Extract rows for player side
        rows = []
        for side in SIDES_CLASS:
            for tr in table.find("tbody").find_all("tr"):
                player_div = tr.find("td", class_="mod-player")
                for s in player_div:
                    if s.text.strip():
                        player_name, org = [s.strip() for s in s.text.split(" ")]
                stats = tr.find_all("span", class_=side)
                row = [stat.get_text(strip=True) for stat in stats]  # Player Stats
                row.append(side)  # Player Side
                row.append(match_id)  # Match ID
                row.append(game_ids[idx // 2])  # Map ID
                row.append(tr.find("img").get("alt"))  # Agent
                row.append(player_name)  # Player Name
                row.append(org)  # Org

                rows.append(row)

        df = pd.concat([df, pd.DataFrame(rows, columns=headers)])

    if output_dir:
        if os.path.isdir(output_dir):
            full_path = os.path.join(output_dir, f"{match_id}_overview.csv")
            print(f"writing file to {full_path}")
            df.to_csv(full_path)

    return df


###################################
###################################
## Main
###################################
###################################

# print(
#     get_match_overview_data(
#         match_id=378662,
#         match_name="gen-g-vs-sentinels-valorant-champions-2024-opening-b",
#         output_dir="D:\\projects\\vlr-analytics\\test_data",
#     )
# )

# print(
#     get_completed_matches(page=1)
# )
# print(
#     get_completed_matches(page=2)
# )
# print(
#     get_completed_matches(page=3)
# )
