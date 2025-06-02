import requests
import pandas as pd
import inspect

from .token import Token


class Org:
    """
    A GitHub organization with methods to interact with it.

    Parameters
    ----------
    name : str
        The name of the GitHub organization.

    """

    def __init__(self, name):
        self.name = name

        self.api_url = f"https://api.github.com/orgs/{self.name}"
        self.headers = (
            {"Authorization": f"token {Token.get_token()}"} if Token.get_token() else {}
        )

    def _get(self, url, params=None):
        """
        Make a request.

        Parameters
        ----------
        url : str
            The URL to request.
        params : dict, optional
            URL parameters to pass with the request.

        Returns
        -------
        dict or list
            Parsed JSON response.

        Raises
        ------
        ConnectionError
            For network issues.
        RuntimeError
            For unexpected HTTP responses or JSON decode errors.
        ValueError
            If the resource is not found (404).
        """
        context = inspect.stack()[1].function

        try:
            response = requests.get(
                url, headers=self.headers, params=params, timeout=10
            )
        except requests.exceptions.Timeout:
            raise ConnectionError(f"Request timed out in {context}().")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Network connection error in {context}().")
        except requests.RequestException as e:
            raise RuntimeError(f"Error in {context}(): {str(e)}")

        if response.status_code == 200:
            try:
                return response.json()
            except ValueError:
                raise RuntimeError(f"Failed to parse JSON in {context}().")
        elif response.status_code == 404:
            raise ValueError(f"Resource not found in {context}().")
        elif (
            response.status_code == 403
            and response.headers.get("X-RateLimit-Remaining") == "0"
        ):
            raise RuntimeError("GitHub API rate limit exceeded.")
        else:
            raise RuntimeError(
                f"Unexpected response ({response.status_code}) in {context}(): {response.text}"
            )

    def exists(self):
        """
        Check if the GitHub organization exists.

        Returns
        -------
        bool
            True if the organization exists.

        """
        url = self.api_url
        try:
            self._get(url, params=None)
            return True
        except ValueError:
            return False

    def get_repos(self):
        """
        Fetch all repositories in the organization and return as pd.DataFrame.

        Returns
        -------
        pandas.DataFrame
            A DataFrame where each row represents a repository and columns represent repository metadata.

        """
        df_ = pd.DataFrame()
        url = f"{self.api_url}/repos"
        params = {"per_page": 100, "page": 1}

        while True:
            data = (
                pd.DataFrame(self._get(url, params=params))
                .loc[
                    :,
                    [
                        "id",
                        "name",
                        "full_name",
                        "description",
                        "private",
                        "is_template",
                        "url",
                        "html_url",
                        "clone_url",
                        "fork",
                        "created_at",
                        "updated_at",
                        "pushed_at",
                        "default_branch",
                        "size",
                        "archived",
                    ],
                ]
                .set_index("id", verify_integrity=True)
                .assign(
                    created_at=lambda df_: pd.to_datetime(
                        df_.created_at
                    ).dt.tz_localize(None),
                    updated_at=lambda df_: pd.to_datetime(
                        df_.updated_at
                    ).dt.tz_localize(None),
                    pushed_at=lambda df_: pd.to_datetime(df_.pushed_at).dt.tz_localize(
                        None
                    ),
                )
            )

            if data.empty:
                break

            df_ = pd.concat([df_, data], axis=0)

            params["page"] += 1

            if params["page"] > 2:
                break

        return df_
