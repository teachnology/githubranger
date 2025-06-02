import requests
import base64


class Repo:
    def __init__(self, token, org, name):
        self.token = token
        self.org = org
        self.name = name
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json",
        }
        self.api_url = f"https://api.github.com/repos/{self.org}/{self.name}"

    def repository_exists(self):
        response = requests.get(self.api_url, headers=self.headers)
        return response.status_code == 200

    def create(self, private, template):
        if self.repository_exists():
            print("Repository already exists.")
            return

        data = {
            "name": self.name,
            "owner": self.org,
            "private": private,
        }

        response = requests.post(
            f"https://api.github.com/repos/{self.org}/{template}/generate",
            headers=self.headers,
            json=data,
        )
        if response.status_code == 201:
            print("Repository created successfully.")
            print("URL:", response.json()["html_url"])
        else:
            print("Failed to create repository")
            print("Status Code:", response.status_code)
            print("Response:", response.json())

    def has_access(self, username):
        response = requests.get(
            f"{self.api_url}/collaborators/{username}", headers=self.headers
        )
        return response.status_code == 204

    def add_collaborators(self, collaborators):
        for collaborator in collaborators:
            if not self.has_access(collaborator):
                self._add_collaborator(collaborator)

    def add_file(self, file_path, file_content, commit_message):
        url = f"{self.api_url}/contents/{file_path}"
        base64_content = base64.b64encode(file_content.encode("utf-8")).decode("utf-8")

        data = {
            "message": commit_message,
            "content": base64_content,
            "branch": "main",  # You can specify a different branch if needed
        }

        response = requests.put(url, headers=self.headers, json=data)
        if response.status_code in [200, 201]:
            print(f"File '{file_path}' added/updated successfully.")
            print("URL:", response.json()["content"]["html_url"])
        else:
            self._handle_error(response)

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

    def get_file(self, file_path, branch="main"):
        url = f"{self.api_url}/contents/{file_path}?ref={branch}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            content = response.json().get("content")
            if content:
                return base64.b64decode(content).decode("utf-8")
            else:
                print("Error: File content is empty or missing.")
                return None
        else:
            self._handle_error(response)
            return None
