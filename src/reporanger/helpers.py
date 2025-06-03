import logging


def ensure_repo_state(repo, template=None, private=True, users=None):
    """Refresh the repo by creating it if it doesn't exist, or updating it if it does.

    The intention for this function is to be run in a loop, so it will not raise an
    error if the repository already exists. All warnings will be logged instead.

    Parameters
    ----------
    repo : Repo
        An instance of the Repo class representing the GitHub repository.
    template : Repo, optional
        An instance of the Repo class representing the template repository to use for
        creating the new repository. If None, the repository will be created without a
        template.
    private : bool, optional
        Whether the repository should be private (default is True).
    users : list of User, optional
        A list of User instances representing the GitHub users to add as collaborators
        to the repository (default is None).

    """
    if not repo.exists():
        repo.create(private=private, template=template)
    else:
        logging.warning(f"Repository '{repo}' already exists.")

    if users:
        for user in users:
            if not user.exists():
                logging.warning(f"User '{user}' does not exist.")
                continue

            if user.can_access(repo):
                logging.warning(f"User '{user}' already has access to repo '{repo}'.")
            else:
                repo.add_user(user)
