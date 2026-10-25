"""Run the app locally: `uv run python -m aggrey`.

Forces a selector event loop: uvicorn picks the Proactor loop on Windows, which psycopg async
rejects. Linux already defaults to the selector loop, so this changes nothing in deploy.
"""

import uvicorn


def main() -> None:
    uvicorn.run(
        "aggrey.app:create_app",
        factory=True,
        host="127.0.0.1",
        port=8000,
        loop="asyncio:SelectorEventLoop",
    )


if __name__ == "__main__":
    main()
