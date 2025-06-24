from pathlib import Path

import index

if __name__ == "__main__":
    index.handler(
        {"body": Path("test-body.json").read_text(), "isBase64Encoded": False},
        {"test": True},
    )
