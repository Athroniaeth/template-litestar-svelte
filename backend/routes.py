from typing import Literal

import msgspec
from litestar import Controller, get


class Greeting(msgspec.Struct):
    message: str


class HealthCheck(msgspec.Struct):
    status: Literal["ok"] = "ok"


class ApiController(Controller):
    """Groups related routes. The /api prefix is applied by the root router in app.py,
    not here, so every controller stays prefix-agnostic. Add shared `guards`,
    `dependencies` here later."""

    @get("/hello", name="api:hello")
    async def hello(self) -> Greeting:
        return Greeting(message="Hello from Litestar")

    @get("/health", name="api:health")
    async def health_check(self) -> HealthCheck:
        return HealthCheck()
