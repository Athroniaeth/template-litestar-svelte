from typing import Literal

import msgspec
from litestar import Router, get


class Greeting(msgspec.Struct):
    message: str


class HealthCheck(msgspec.Struct):
    status: Literal["ok"] = "ok"


@get("/hello", name="api:hello")
async def hello() -> Greeting:
    return Greeting(message="Hello from Litestar")


@get("/health", name="api:health")
async def health_check() -> HealthCheck:
    return HealthCheck()


api_router = Router(path="/api", route_handlers=[hello, health_check])
