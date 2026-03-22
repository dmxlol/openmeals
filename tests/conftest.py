import os

os.environ["ENVIRONMENT"] = "test"

from dotenv import load_dotenv  # noqa: E402

load_dotenv(".env.test", override=True)
