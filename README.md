# clean-architecture-template

An opinionated Web API template with Python, built around Domain-Driven Design (DDD), CQRS, and Clean Architecture.

## Tech Stack

| Category | Package                                                       | Role |
|----------|---------------------------------------------------------------|------|
| **Package Manager** | [uv](https://github.com/astral-sh/uv)                         | Dependency management |
| **Web Framework** | [FastAPI](https://github.com/fastapi/fastapi)                 | REST API |
| **CLI** | [Typer](https://github.com/fastapi/typer)                     | Command line interface |
| **ORM** | [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy)        | Database access |
| **Migration** | [Alembic](https://github.com/sqlalchemy/alembic)              | Schema migrations |
| **Validation** | [Pydantic](https://github.com/pydantic/pydantic)              | Validation and serialization |
| **DI** | [python-injection](https://github.com/100nm/python-injection) | Dependency injection |
| **CQRS** | [python-cq](https://github.com/100nm/python-cq)               | Command/Query Responsibility Segregation |

---

## Architecture

```
src/
├── core/           # Domain + Application layers (business logic)
│   └── {context}/
│       ├── domain/     # Domain layer (entities, value objects, aggregates)
│       └── ...         # Application layer (commands, queries, ports, events)
├── services/       # Shared technical services (cross-cutting concerns)
└── infra/          # Infrastructure layer (concrete implementations)
```

---

## Domain Layer (`src/core/{context}/domain/`)

The **Domain** layer contains pure business models: entities, value objects, and aggregates. It has no dependencies on external frameworks. 

### Structure

```
src/core/{context}/domain/
├── {aggregate}.py      # Aggregates (entity that groups related objects and ensures they are always in a valid state together)
├── {entity}.py         # Entities (objects with unique identity)
└── {value_object}.py   # Value Objects (immutable, no identity)
```

### Packages

| Package | Role | Justification |
|---------|------|---------------|
| `pydantic` | Domain models | Native validation, immutability with `frozen=True` |

### Path Patterns

| Type | Path Pattern                                  | Description |
|------|-----------------------------------------------|-------------|
| **Aggregate** | `src/core/{context}/domain/{aggregate}.py`    | Entity that groups related objects and ensures they are always in a valid state together |
| **Entity** | `src/core/{context}/domain/{entity}.py`       | Object with unique identity |
| **Value Object** | `src/core/{context}/domain/{value_object}.py` | Immutable object without identity |

### Example: Entity `UserSession`

```python name=src/core/auth/domain/session.py
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, SecretStr, field_serializer

class UserSession(BaseModel):
    id: UUID
    user_id: UUID
    created_at: datetime
    last_use_at: datetime
    secret: SecretStr
```

---

## Application Layer (`src/core/{context}/`)

The **Application** layer contains use cases and orchestration logic: commands, queries, events, and ports. Everything in the bounded context folder except `domain/`.

### Structure

```
src/core/{context}/
├── domain/         # Domain layer (see above)
├── commands/       # Commands and their Handlers (write operations)
├── queries/        # Queries and their Views (read operation definitions)
├── events/         # Domain Events
├── ports/          # Interfaces (Protocols) for dependency inversion
│   └── repo/       # Repository interfaces
└── shared/         # Shared code within the bounded context
```

### Packages

| Package | Role | Justification                                |
|---------|------|----------------------------------------------|
| `python-cq` | CQRS | Command/Query separation, handler decoupling |
| `pydantic` | DTOs | Command/Event/Query/View validation          |

### Path Patterns

| Type | Path Pattern | Description |
|------|--------------|-------------|
| **Command** | `src/core/{context}/commands/{action}.py` | Action that modifies state |
| **Query** | `src/core/{context}/queries/{query_name}.py` | Data reading (Query + View) |
| **Event** | `src/core/{context}/events/{event}.py` | Domain event |
| **Port (Repository)** | `src/core/{context}/ports/repo/{aggregate}.py` | Persistence interface |
| **Port (Service)** | `src/core/{context}/ports/{service}.py` | External service interface |

### Example: Command with Handler

```python name=src/core/auth/commands/open_user_session.py
from typing import NamedTuple
from uuid import UUID

from cq import command_handler
from pydantic import BaseModel, SecretStr, field_serializer

from src.core.auth.domain.session import UserSession
from src.core.auth.ports.repo.user_permission import UserPermissionRepository
from src.core.auth.ports.repo.user_session import UserSessionRepository
from src.core.auth.ports.token_generator import TokenGenerator
from src.core.auth.shared.access_token import encode_access_token
from src.core.auth.shared.session_token import encode_session_token
from src.services.datetime.abc import DateTimeService
from src.services.hasher.abc import Hasher
from src.services.jwt.abc import JWTService
from src.services.uuid.abc import UUIDGenerator

class OpenUserSessionCommand(BaseModel):
    user_id: UUID

class UserTokens(BaseModel):
    access_token: SecretStr
    session_token: SecretStr

    @field_serializer("access_token", "session_token", when_used="json")
    def _dump_secret(self, value: SecretStr) -> str:
        return value.get_secret_value()

@command_handler
class OpenUserSessionHandler(NamedTuple):
    datetime: DateTimeService
    hasher: Hasher
    jwt: JWTService
    repo: UserSessionRepository
    token_generator: TokenGenerator
    user_permission_repo: UserPermissionRepository
    uuid: UUIDGenerator

    async def handle(self, command: OpenUserSessionCommand) -> UserTokens:
        user_id = command.user_id

        session_secret = self.token_generator.generate(128)
        session = self.new_session(user_id, session_secret)
        await self.repo.save(session)

        permissions = await self.user_permission_repo.get(user_id)
        access_token = encode_access_token(self.jwt, user_id, permissions)
        session_token = encode_session_token(session.id, session_secret)
        return UserTokens(
            access_token=SecretStr(access_token),
            session_token=SecretStr(session_token),
        )

    def new_session(self, user_id: UUID, session_secret: str) -> UserSession:
        now = self.datetime.utcnow()
        return UserSession(
            id=self.uuid.next(),
            user_id=user_id,
            created_at=now,
            last_use_at=now,
            secret=SecretStr(self.hasher.hash(session_secret)),
        )
```

### Example: Port (Repository Interface)

```python name=src/core/auth/ports/repo/user_session.py
from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from src.core.auth.domain.session import UserSession

class UserSessionRepository(Protocol):
    @abstractmethod
    async def delete(self, session_id: UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get(self, session_id: UUID) -> UserSession | None: 
        raise NotImplementedError

    @abstractmethod
    async def save(self, session: UserSession) -> None:
        raise NotImplementedError
```

### Example: Query and View

```python name=src/core/user_profile/queries/private.py
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

class GetPrivateUserProfileQuery(BaseModel):
    user_id: UUID

class PrivateUserProfileView(BaseModel):
    id: UUID
    created_at: datetime
    first_name: str
    last_name: str
```

---

## Shared Services (`src/services/`)

The **Services** layer defines abstract interfaces for common technical services used across the entire application. These are cross-cutting concerns that can be used by any layer.

### Structure

```
src/services/{service_name}/
├── abc.py          # Abstract interface (Protocol)
└── {impl}.py       # Implementation
```

### Path Patterns

| Type | Path Pattern | Description |
|------|--------------|-------------|
| **Service Interface** | `src/services/{service}/abc.py` | Abstract Protocol |
| **Implementation** | `src/services/{service}/{impl}.py` | Concrete implementation |

### Example: Abstract Service `Hasher`

```python name=src/services/hasher/abc.py
from abc import abstractmethod
from typing import Protocol

class Hasher(Protocol):
    @abstractmethod
    def hash(self, value: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def verify(self, value: str, hashed_value: str) -> bool:
        raise NotImplementedError

    def needs_rehash(self, hashed_value: str) -> bool:
        return False
```

### Example: Implementation `Argon2Hasher`

```python name=src/services/hasher/argon2.py
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from injection import injectable

from src.services.hasher.abc import Hasher

@injectable(on=Hasher)
class Argon2Hasher(Hasher):
    def __init__(self) -> None:
        self.__internal = PasswordHasher()

    def hash(self, value: str) -> str:
        return self.__internal.hash(value)

    def verify(self, value: str, hashed_value: str) -> bool:
        try: 
            return self.__internal.verify(hashed_value, value)
        except (InvalidHashError, VerificationError):
            return False

    def needs_rehash(self, hashed_value: str) -> bool:
        return self.__internal.check_needs_rehash(hashed_value)
```

---

## Infrastructure Layer (`src/infra/`)

The **Infrastructure** layer contains all concrete implementations: API, database, external integrations, etc.

### Structure

```
src/infra/
├── adapters/           # Port implementations (repositories, services)
│   └── {context}/
│       └── repo/       # SQLAlchemy repositories
├── api/
│   ├── builder.py      # FastAPI configuration
│   ├── dependencies.py # FastAPI dependencies (auth, locale, etc.)
│   └── routes/         # Endpoints by domain
├── cli/
│   ├── builder.py      # Typer configuration
│   └── apps/           # CLI commands
├── db/                 # Database
│   ├── tables.py       # SQLAlchemy table definitions
│   └── migrations/     # Alembic migrations
├── integrations/       # Third-party integrations (Stripe, etc.)
│   └── {provider}/
│       └── commands/   # Integration-specific commands
└── query_handlers/     # Query handlers (DB read operations)
```

### Packages

| Package | Role | Justification |
|---------|------|---------------|
| `fastapi` | API framework | Performance, native typing, auto OpenAPI |
| `uvicorn` + `uvloop` | ASGI server | Optimal async performance |
| `typer` | CLI | FastAPI-like API, autocompletion |
| `sqlalchemy[postgresql-asyncpg]` | Async ORM | Native async PostgreSQL support |
| `alembic` | Migrations | Standard for SQLAlchemy |
| `python-injection` | DI | Declarative dependency injection |

### Path Patterns

| Type | Path Pattern                                         | Description |
|------|------------------------------------------------------|-------------|
| **Adapter Repository** | `src/infra/adapters/{context}/repo/{aggregate}.py`   | SQLAlchemy implementation of Port |
| **Adapter Service** | `src/infra/adapters/{context}/{service}.py`          | Service implementation |
| **API Route** | `src/infra/api/routes/{route_set_name}.py`           | FastAPI endpoints |
| **DB Table** | `src/infra/db/tables.py`                             | SQLAlchemy models |
| **Query Handler** | `src/infra/query_handlers/{context}/{query_name}.py` | Read handler |
| **CLI App** | `src/infra/cli/apps/{app_name}.py`                   | Typer commands |
| **Integration** | `src/infra/integrations/{provider}/`                 | External provider specific code |

### Example: Adapter Repository

```python name=src/infra/adapters/auth/repo/user_session.py
from dataclasses import dataclass
from uuid import UUID

from injection import injectable
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth.domain.session import UserSession
from src.core.auth.ports.repo.user_session import UserSessionRepository
from src.infra.db.tables import UserSessionTable

@injectable(on=UserSessionRepository)
@dataclass(frozen=True)
class SQLAUserSessionRepository(UserSessionRepository):
    session: AsyncSession

    async def delete(self, session_id: UUID) -> None:
        stmt = delete(UserSessionTable).where(UserSessionTable.id == session_id)
        await self.session.execute(stmt)

    async def get(self, session_id: UUID) -> UserSession | None:
        stmt = (
            select("*")
            .select_from(UserSessionTable)
            .where(UserSessionTable.id == session_id)
        )
        row = (await self.session.execute(stmt)).mappings().one_or_none()

        if row is None:
            return None

        return UserSession.model_validate(row)

    async def save(self, session: UserSession) -> None:
        table = self.to_table(session)
        await self.session.merge(table)

    @classmethod
    def to_table(cls, session: UserSession) -> UserSessionTable: 
        return UserSessionTable(
            id=session.id,
            user_id=session.user_id,
            created_at=session.created_at,
            last_use_at=session.last_use_at,
            secret=session.secret.get_secret_value(),
        )
```

### Example: API Route

```python name=src/infra/api/routes/user.py
from typing import Annotated
from uuid import UUID

from cq import QueryBus
from fastapi import APIRouter, Depends, HTTPException, status
from injection.ext.fastapi import Inject

from src.core.user_profile.queries.private import GetPrivateUserProfileQuery, PrivateUserProfileView
from src.infra.api.dependencies import get_claimant_id

router = APIRouter(prefix="/users", tags=["User"])

@router.get("/me")
async def get_me(
    claimant_id: Annotated[UUID, Depends(get_claimant_id)],
    query_bus: Inject[QueryBus[PrivateUserProfileView | None]],
) -> PrivateUserProfileView:
    query = GetPrivateUserProfileQuery(user_id=claimant_id)
    view = await query_bus.dispatch(query)

    if view is None:
        raise HTTPException(status_code=status.HTTP_428_PRECONDITION_REQUIRED)

    return view
```

### Example: Query Handler

```python name=src/infra/query_handlers/user_profile/private.py
from typing import NamedTuple

from cq import query_handler
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.user_profile.queries.private import GetPrivateUserProfileQuery, PrivateUserProfileView
from src.infra.adapters.user_profile.repo.user_profile import UserStatus
from src.infra.db.tables import UserTable

@query_handler
class GetPrivateUserProfileHandler(NamedTuple):
    session: AsyncSession

    async def handle(
        self,
        query: GetPrivateUserProfileQuery,
    ) -> PrivateUserProfileView | None:
        stmt = select(
            UserTable.id,
            UserTable.created_at,
            UserTable.first_name,
            UserTable.last_name,
        ).where(
            UserTable.id == query.user_id,
            UserTable.status == UserStatus.READY,
        )
        row = (await self.session.execute(stmt)).mappings().one_or_none()

        if row is None:
            return None

        return PrivateUserProfileView.model_validate(row)
```

---

## Main script (`main.py`)

The `main.py` file is the entry point for both the API and CLI. Routers and CLI apps must be manually registered here.

```python name=main.py
from injection import find_instance

from src.infra.api.builder import FastAPIBuilder
from src.infra.api.routes import auth, registration, user
from src.infra.cli.apps import db
from src.infra.cli.builder import TyperBuilder

if __name__ == "__main__": 
    cli = (
        find_instance(TyperBuilder)
        .include_apps(
            db.app,
        )
        .build()
    )
    cli()

else:
    app = (
        find_instance(FastAPIBuilder)
        .include_routers(
            auth.router,
            registration.router,
            user.router,
        )
        .build()
    )
```

When adding new routes or CLI commands: 
- **New API router**: Add `from src.infra.api.routes import {module}` and include `{module}.router` in `include_routers()`
- **New CLI app**: Add `from src.infra.cli.apps import {module}` and include `{module}.app` in `include_apps()`

---

## Testing (`tests/`)

Test implementations should be placed in `tests/impl/`. This folder contains deterministic implementations that replace production services during tests, making unit tests predictable and fast.

### Structure

```
tests/
├── impl/               # Test implementations (deterministic replacements)
│   ├── services/       # Service test implementations
│   └── adapters/       # Adapter test implementations
├── core/               # Domain and application tests
├── infra/              # Infrastructure tests
└── services/           # Service tests
```

### Example:  Deterministic Hasher

Production uses `Argon2Hasher` which is slow and non-deterministic. For tests, we use a simple `SHA256Hasher`:

```python name=tests/impl/services/hasher.py
from hashlib import sha256

from injection.testing import test_injectable

from src.services.hasher.abc import Hasher

@test_injectable(on=Hasher)
class SHA256Hasher(Hasher):
    def hash(self, value: str) -> str:
        b = value.encode()
        h = sha256(b, usedforsecurity=False).hexdigest()
        return f"sha256:{h}"

    def verify(self, value: str, hashed_value: str) -> bool:
        return hashed_value == self.hash(value)

    def needs_rehash(self, hashed_value: str) -> bool:
        return False
```

The `@test_injectable(on=Hasher)` decorator registers this implementation only during test execution, replacing the production `Argon2Hasher`.

---

## Commands

```bash
# Installation
make install

# Development
make dev                  # Start uvicorn server in reload mode

# Database
make create-db            # Create the database
make drop-db              # Drop the database
make init-db              # Drop + Create + Migrate
make migrate              # Apply migrations
make makemigrations       # Generate a new migration

# Code quality
make lint                 # Ruff format + check
make pytest               # Run tests
make                      # lint + pytest
```

---

## Architecture Rules

### Do

1. **Domain depends on nothing** - Domain (`src/core/{context}/domain/`) must never import from `src/infra/`
2. **Use Protocols** - Define interfaces in `ports/` for dependency inversion
3. **Commands for writes** - All state modifications go through a Command
4. **Queries for reads** - Query Handlers are in infra because they access the DB directly
5. **Dependency injection** - Use `@injectable(on=Protocol)` for implementations
6. **Register routers and apps** - Always add new routers and CLI apps in `main.py`

### Don't

1. **No infra imports in core** - Never `from src.infra import ...` in `src/core/`
2. **No SQLAlchemy in domain** - Tables are only in `src/infra/db/tables.py`
3. **No business logic in routes** - Routes only dispatch Commands/Queries
