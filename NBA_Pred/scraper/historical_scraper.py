import requests  # For sending HTTP requests to the target website
from bs4 import BeautifulSoup  # For parsing HTML and extracting data from the web pages
import pandas as pd  # For handling and manipulating the data in DataFrame format
import logging  # For logging information, warnings, and errors
import time  # For handling delays and sleep functions

class HistoricalScraper:
    """
    A scraper to collect historical NBA statistics data from basketball-reference.com.
    
    """

    def __init__(self):
        """
        Initialize the scraper with the base URL, year range, data storage, and retry settings.
        """
        self.base_url = 'https://www.basketball-reference.com/leagues/'
        self.years = range(1950, 2024)
        self.data = []
        self.max_retries = 5  # Maximum number of retries for 429 errors
        self.retry_delay = 10  # Delay in seconds before retrying

    def fetch_data(self, year):
        """
        Fetch the HTML data for a given year.

        Args:
            year (int): The year for which to fetch the data.

        Returns:
            str: The HTML content of the fetched page.

        Raises:
            HTTPError: If the request fails after all retries.
        """
        url = f'{self.base_url}NBA_{year}_totals.html'
        logging.info(f'Fetching data from %s {url}')
        for attempt in range(self.max_retries):
            response = requests.get(url)
            if response.status_code == 429:
                logging.warning(f'429 Too Many Requests. Retrying in %s seconds... {self.retry_delay}')
                time.sleep(self.retry_delay)
            else:
                response.raise_for_status()  # Raise an error for bad status codes
                return response.text
        response.raise_for_status()  # Raise an error if all retries fail

    def parse_data(self, html, year):
        """
        Parse the HTML data to extract player statistics.

        Args:
            html (str): The HTML content of the page.
            year (int): The year for which to parse the data.

        Returns:
            None
        """
        logging.info(f'Parsing data for year %s {year}')
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table', {'id': 'totals_stats'})

        # Check if the table exists
        if not table:
            logging.warning('No table found for year %s', year)
            return

        headers = [th.getText() for th in table.find_all('th')[1:30]]  # Capture only the first 29 headers
        rows = table.find_all('tr', class_=lambda x: x != 'thead')  # Exclude header rows

        player_data = []
        for row in rows:
            columns = row.find_all('td')
            if len(columns) == 29:  # Ensure the correct number of columns
                player_data.append([td.getText() for td in columns])

        if player_data:
            stats_df = pd.DataFrame(player_data, columns=headers)
            stats_df['Year'] = year
            self.data.append(stats_df)
        else:
            logging.warning(f'No data found for year %s {year}')

    def save_data(self, filename='historical_nba_stats.csv'):
        """
        Save the collected data to a CSV file.

        Args:
            filename (str): The name of the file to save the data to. Defaults to 'historical_nba_stats.csv'.

        Returns:
            None
        """
        logging.info(f'Saving data to %s {filename}')
        all_data = pd.concat(self.data, ignore_index=True)
        all_data.to_csv(filename, index=False)

    def run(self):
        """
        Run the scraper to fetch, parse, and save the data for the specified years.

        Returns:
            None
        """
        for year in self.years:
            html = self.fetch_data(year)
            self.parse_data(html, year)
            time.sleep(5)  # Delay between requests to avoid hitting the rate limit
        self.save_data()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    scraper = HistoricalScraper()
    scraper.run()
