class Token:
    _token = None

    @classmethod
    def set_token(cls, token):
        """Set the global GitHub token for the package."""
        cls._token = token

    @classmethod
    def get_token(cls):
        """Get the global GitHub token for the package."""
        return cls._token
