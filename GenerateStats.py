import requests
from arrxConfig import ValidateConfig


def get_arr_history(url: str, headers: dict, params: dict, end_month: int, target_year: int, verbose: bool = False) -> dict:
    """Make a request to the given url with the given headers and params."""
    arr_stats = {}
    try:
        arr_stats_request = requests.get(url=url, headers=headers, params=params)
        arr_stats_request.raise_for_status()

        if verbose:
            print(f'\nGetting history from {url}')
            print(f'Headers: {headers}')
            print(f'Params: {params}')
            print(f'Status: {arr_stats_request.status_code}\n')
        try:
            arr_stats_temp = arr_stats_request.json()
            """
            Because the API is only able to accept a "start" date, we need to manually filter out anything after the end_month (default is 12).
            Since the response is already sorted by date, we can just loop through the list and when we hit the first item that is after the end_month, we can break out of the loop.
            Using the index of the item, we can slice the list to only include the items we want (before the end_month)
            """
            for i, item in enumerate(arr_stats_temp):

                # check first 4 ints to see if its correct year then check month
                # [5:7] is the month portion of the date string (e.g. 2021-01-01 -> 01). This lets us avoid having to import/use the datetime module
                if int(item.get('date')[:4]) > target_year or int(item.get("date")[5:7]) > end_month:
                    arr_stats = arr_stats_temp[:i]
                    break

            # If no break was hit, then we can just use the entire list
            if len(arr_stats) == 0:
                arr_stats = arr_stats_temp

        except (requests.exceptions.JSONDecodeError, TypeError) as e:
            print(f'Error while decoding the JSON response: {e}')
        except Exception as e:
            print(f'Unknown error: {e}')
        else:
            return arr_stats
    except requests.exceptions.RequestException as e:
        print(f'Error while making the request: {e}')

    return arr_stats


class GenerateStats(ValidateConfig):
    def __init__(self, host: str, port: int, api_key: str, app_type: str, start_month: int, end_month: int, review_year: int, verbose: bool = False) -> None:
        # Validate the config and make sure we are able to connect to the given app
        super().__init__(host, port, api_key, app_type, verbose)

        self.start_month = start_month
        self.end_month = end_month
        self.review_year = review_year
        # Various counts
        self.total_grabs = 0
        self.total_repacks = 0
        # Total size of data grabbed
        self.byte_total_size = 0
        self.terabyte_total_size = 0
        # Dicts to hold various keys and their counts
        self.indexers = {}
        self.languages = {}
        self.release_groups = {}
        self.source_types = {}
        self.download_methods = {'torrent': 0, 'usenet': 0}
        self.unprocessed = {}  # This stores the json response from the arr application

    def make_request_for_history(self) -> None:
        """Format the request and call get_arr_history() func to get the history as a JSON object."""
        url = f'{self.host}:{self.port}/api/v3/history/since'
        headers = {'accept': 'application/json', 'X-Api-Key': self.api_key}
        params = {'eventType': 1, 'date': f'{self.review_year}-{self.start_month:02d}-01T00:00:00Z'}  # For eventType we use 1 to filter only 'grabbed' events
        # Assign the response to the unprocessed attribute
        self.unprocessed = get_arr_history(url, headers, params, self.end_month, self.review_year, self.verbose)
        self.total_grabs = len(self.unprocessed)

    def calculate_tb_size(self) -> float:
        """Calculate the total size of grabbed releases in TB."""
        self.terabyte_total_size = round(self.byte_total_size / 1000000000000, 2)
        return self.terabyte_total_size

    @staticmethod
    def add_to_dict(target_dict: dict, target_key: str) -> None:
        """Adds the given key to the given dictionary and increments the count."""
        return None if target_key is None else target_dict.update({target_key.lower(): target_dict.get(target_key.lower(), 0) + 1})

    @staticmethod
    def get_most_common_keys(target_dict, num_to_return: int = 5) -> dict:
        """Return the most used key/val pairs from the dict specified."""
        return dict(sorted(target_dict.items(), key=lambda x: x[1], reverse=True)[:num_to_return])

    def get_history(self) -> dict:
        """Return the unprocessed history."""
        return self.unprocessed
