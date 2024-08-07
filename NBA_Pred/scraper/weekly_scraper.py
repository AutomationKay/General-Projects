import requests  # For sending HTTP requests to the target website
from bs4 import BeautifulSoup  # For parsing HTML and extracting data from the web pages
import pandas as pd  # For handling and manipulating the data in DataFrame format
import logging  # For logging information, warnings, and errors
import time  # For handling delays and sleep functions

class WeeklyScraper:
    """
    A scraper to collect weekly NBA statistics data from basketball-reference.com.
    """

    def __init__(self):
        """
        Initialize the scraper with the URL for the current NBA season's totals.
        """
        self.url = 'https://www.basketball-reference.com/leagues/NBA_2024_totals.html'
        self.max_retries = 5  # Maximum number of retries for 429 errors
        self.retry_delay = 10  # Delay in seconds before retrying

    def fetch_data(self):
        """
        Fetch the HTML data for the current season.

        Returns:
            str: The HTML content of the fetched page.

        Raises:
            HTTPError: If the request fails.
        """
        logging.info(f'Fetching data from %s {self.url}')
        for attempt in range(self.max_retries):
            response = requests.get(self.url)
            if response.status_code == 429:
                logging.warning(f'429 Too Many Requests. Retrying in %s seconds... {self.retry_delay}')
                time.sleep(self.retry_delay)
            else:
                response.raise_for_status()  # Raise an error for bad status codes
                return response.text
        response.raise_for_status()  # Raise an error if all retries fail

    def parse_data(self, html):
        """
        Parse the HTML data to extract player statistics.

        Args:
            html (str): The HTML content of the page.

        Returns:
            DataFrame: A DataFrame containing the parsed player statistics.
        """
        logging.info('Parsing data')
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table', {'id': 'totals_stats'})
        
        # Check if the table exists
        if not table:
            logging.warning("No table found")
            return None
        
        headers = [th.getText() for th in table.find_all('th')[1:30]]  # Skip the first header as it's usually empty
        rows = table.find_all('tr')[1:]  # Skip the first row as it's the header
        player_data = []
        for row in rows:
            columns = row.find_all('td')
            if len(columns) == len(headers):
                player_data.append([td.getText() for td in columns])
            else:
                logging.warning(f'Skipping row with column length mismatch: expected %d columns, got %d colums {len(headers), {len(columns)}}')
        
        if player_data:
            stats_df = pd.DataFrame(player_data, columns=headers)
            return stats_df
        else: logging.warning('No valid player data found')
        return None

    def save_data(self, df, filename='weekly_nba_stats.csv'):
        """
        Save the collected data to a CSV file.

        Args:
            df (DataFrame): The DataFrame containing the player statistics.
            filename (str): The name of the file to save the data to. Defaults to 'weekly_nba_stats.csv'.

        Returns:
            None
        """
        logging.info(f'Saving data to %s {filename}')
        df.to_csv(filename, index=False)

    def run(self):
        """
        Run the scraper to fetch, parse, and save the data for the current week.

        Returns:
            None
        """
        html = self.fetch_data()
        df = self.parse_data(html)
        self.save_data(df)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = WeeklyScraper()
    scraper.run()
