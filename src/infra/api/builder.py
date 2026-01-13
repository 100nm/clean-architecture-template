from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import AsyncContextManager, Self

from fastapi import APIRouter, Depends, FastAPI, Request, Response, status
from fastapi.exceptions import ValidationException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from injection import adefine_scope, injectable
from pydantic import ValidationError

from src.infra.entrypoint import lifespan
from src.settings import Scope, Settings


@injectable
@dataclass(frozen=True)
class FastAPIBuilder:
    settings: Settings
    routers: list[APIRouter] = field(default_factory=list, init=False)

    def build(self) -> FastAPI:
        app = FastAPI(
            debug=self.settings.debug,
            dependencies=[Depends(_request_scope)],
            lifespan=self._fastapi_lifespan,
        )

        for router in self.routers:
            app.include_router(router)

        app.add_middleware(
            CORSMiddleware,
            allow_credentials=True,
            allow_headers=["*"],
            allow_methods=["*"],
            allow_origins=self.settings.allow_origins,
        )

        @app.exception_handler(ValidationError)
        async def _(request: Request, exception: ValidationError) -> Response:
            return ORJSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "errors": exception.errors(
                        include_url=False,
                        include_context=True,
                        include_input=False,
                    )
                },
            )

        @app.exception_handler(ValidationException)
        async def _(request: Request, exception: ValidationException) -> Response:
            return ORJSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={"errors": exception.errors()},
            )

        return app

    def include_routers(self, *routers: APIRouter) -> Self:
        self.routers.extend(routers)
        return self

    def _fastapi_lifespan(self, _app: FastAPI) -> AsyncContextManager[None]:
        return lifespan(self.settings.profile)


async def _request_scope() -> AsyncIterator[None]:
    async with adefine_scope(Scope.REQUEST):
        yield
