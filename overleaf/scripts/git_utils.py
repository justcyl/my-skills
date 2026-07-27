"""Git URL helpers for official and self-hosted Overleaf instances."""


OFFICIAL_WEB_HOSTS = {"overleaf.com", "www.overleaf.com"}


def default_git_base_url(host: str) -> str:
    """Return the Git endpoint used by an Overleaf web host."""
    normalized_host = host.lower().rstrip(".")
    if normalized_host in OFFICIAL_WEB_HOSTS:
        return "https://git.overleaf.com"
    return f"https://{host}/git"
