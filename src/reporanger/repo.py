import base64
import logging
import requests

from .util import get, post, put
from .token import Token
from .org import Org


class Repo:
    """A GitHub repository with methods to interact with it.

    Parameters
    ----------
    org : Org
        An instance of the Org class representing the GitHub organization.
    name : str
        The name of the GitHub repository.

    """

    def __init__(self, org, name):
        self.org = org
        self.name = name
        self.api_url = f"https://api.github.com/repos/{self.org.name}/{self.name}"

    def exists(self):
        """Check if the GitHub repository exists.

        Returns
        -------
        bool
            True if the repository exists, False otherwise.

        """
        url = self.api_url
        try:
            get(url, headers=Token.headers(), params=None)
            return True
        except ValueError:
            return False

    def file_content(self, path, branch="main"):
        """Get the decoded content of a file from the repository.

        Parameters
        ----------
        path : str
            Path to the file in the repository.
        branch : str, optional
            Branch name (default is "main").

        Returns
        -------
        str or None
            Decoded file content, or None if not found or decoding fails.

        """
        url = f"{self.api_url}/contents/{path}?ref={branch}"

        if not (content := get(url, headers=Token.headers()).get("content")):
            return None

        try:
            return base64.b64decode(content).decode("utf-8")
        except (ValueError, TypeError):
            return None

    def create(self, private=True, template=None):
        """Create a new repository.

        Parameters
        ----------
        private : bool, optional
            Whether the repository should be private (default is True).
        template : Repo, optional
            A template repository to base the new repository on (default is None).

        Raises
        ------
        ValueError
            If the repository already exists or if the template does not exist.

        """
        if self.exists():
            raise ValueError(
                f"Repository '{self.name}' already exists in organization '{self.org}'."
            )

        if template is not None:
            if not template.exists():
                raise ValueError(
                    f"Template '{template.org.name}/{template.name}' does not exist."
                )

            url = f"{template.api_url}/generate"
            data = {
                "owner": self.org.name,
                "name": self.name,
                "private": private,
            }
        else:
            url = f"{self.org.api_url}/repos"
            data = {
                "name": self.name,
                "private": private,
            }

        response = post(url, headers=Token.headers(), json=data)
        logging.info(f"Repository created at URL: {response['html_url']}")

    def commit(self, path, content, message, branch="main"):
        """Add or update a file in the repository.

        Parameters
        ----------
        path : str
            Path to the file in the repository.
        content : str
            Content of the file to be added or updated.
        message : str
            Commit message for the change.
        branch : str, optional
            Branch name (default is "main").

        """
        url = f"{self.api_url}/contents/{path}"
        base64_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")

        data = {
            "message": message,
            "content": base64_content,
            "branch": branch,
        }

        # Check if file exists to get its sha.
        response = requests.get(url, headers=Token.headers(), params={"ref": branch})
        if response.status_code == 200:
            data["sha"] = response.json().get("sha")

        response = put(url, headers=Token.headers(), json=data)
        logging.info(f"Committed file '{path}' to repository '{self.name}'.")

    def has_access(self, username):
        response = requests.get(
            f"{self.api_url}/collaborators/{username}", headers=Token.headers()
        )
        return response.status_code == 204

    def add_collaborators(self, collaborators):
        for collaborator in collaborators:
            if not self.has_access(collaborator):
                self._add_collaborator(collaborator)

    def _add_collaborator(self, username):
        response = requests.put(
            f"{self.api_url}/collaborators/{username}",
            headers=self.headers,
            json={"permission": "push"},
        )
        if response.status_code in [201, 204]:
            print(f"Added {username} as a collaborator.")
        else:
            self._handle_error(response)

    def _handle_error(self, response):
        try:
            error_message = response.json().get("message", "Unknown error occurred")
            print(f"Error: {error_message} (Status code: {response.status_code})")
        except ValueError:
            print(
                f"Error: Unable to parse error message (Status code: {response.status_code})"
            )
