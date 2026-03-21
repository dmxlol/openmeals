"""Generate a local ID token for development.

Usage:
    make script name=create_local_token

The token can be used as the `code` parameter in:
    GET /api/v1/auth/local/callback?code=<token>
"""

import argparse

from core.config import settings
from libs.auth.local import LocalProvider

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a local OAuth ID token")
    parser.add_argument("--sub", default="local-dev-user", help="Subject identifier")
    parser.add_argument("--email", default="dev@openmeals.local", help="Email address")
    parser.add_argument("--name", default="Dev User", help="Display name")
    args = parser.parse_args()

    provider = LocalProvider()
    token = provider.encode({"sub": args.sub, "email": args.email, "name": args.name}, settings)
    print(token)
