import requests


class ValidateConfig:
    def __init__(self, host: str, port: int, api_key: str, app_type: str, verbose: bool = False) -> None:
        self.host = host.rstrip("/")  # Remove trailing slash if present
        self.port = port
        self.api_key = api_key
        self.app_type = app_type
        self.verbose = verbose

    def verify_arr(self) -> bool:
        """Verify the arr application is up and running."""
        try:
            if self.verbose:
                print(f'Verifying {self.app_type} instance is up and running...')
                print(f'GET: {self.host}:{self.port}/api/system/status')

            r = requests.get(f'{self.host}:{self.port}/api/v3/system/status?apikey={self.api_key}')
            r.raise_for_status()
            if r.ok:
                return self.verify_arr_type(r)
        except requests.exceptions.HTTPError as e:
            match e.response.status_code:
                case 401:
                    print(f'\nAUTHENTICATION ERROR (401):\n\t--> Is this the correct API key: "{self.api_key}" for "{self.host}:{self.port}"?')
                case 404:
                    print(f'\nNOT FOUND ERROR (404):\n\t--> Is this the correct URL/PORT: "{self.host}:{self.port}"?')
                case _:
                    print(f'\nUNKNOWN ERROR:\n\t--> {e}')
        except Exception as e:
            print(f'\nCatch All Error: {e}\n')

        return False  # If a successful response was not received, return False

    def verify_arr_type(self, r: requests.Response) -> bool:
        """Verify the arr application type."""
        try:
            if self.verbose:
                print(f'Verifying {self.app_type} instance is the correct type...')

            arr_system_info = r.json()
            if not self.app_type.casefold().__eq__(arr_system_info.get("appName").casefold()):
                raise ValueError(f'Application type mismatch:\nExpected: {self.app_type}\nReceived: {arr_system_info.get("appName")} (from API)\n')

            return True  # Otherwise, return True
        except ValueError as e:
            print(f'\n{e}')
        except Exception as e:
            print(f'\nCatch All Error: {e}\n')

    def __str__(self):
        """Return a string representation of the object."""
        return f'\n{self.app_type} Config:\n\tHost: {self.host}\n\tPort: {self.port}\n\tAPI Key: {self.api_key}'
