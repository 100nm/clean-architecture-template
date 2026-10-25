# clean-architecture-template

An opinionated Web API template with Python, built around Domain-Driven Design (DDD), CQRS, and Clean Architecture.

> [!NOTE]
> The template ships with an empty `src/core/`. The code examples below (`auth`, `user_profile` contexts) are
> illustrative: they show the conventions to follow, they are not included in the repository.

## Tech Stack

| Category            | Package                                                                                                         | Role                                     |
|---------------------|-----------------------------------------------------------------------------------------------------------------|------------------------------------------|
| **Package Manager** | [uv](https://github.com/astral-sh/uv)                                                                           | Dependency management                    |
| **Web Framework**   | [FastAPI](https://github.com/fastapi/fastapi)                                                                   | REST API                                 |
| **ASGI Server**     | [Granian](https://github.com/emmett-framework/granian)                                                          | HTTP server (with uvloop)                |
| **CLI**             | [Typer](https://github.com/fastapi/typer)                                                                       | Command line interface                   |
| **Database**        | [PostgreSQL](https://www.postgresql.org)                                                                        | Relational database                      |
| **ORM**             | [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy)                                                          | Database access (async, asyncpg)         |
| **Migration**       | [Alembic](https://github.com/sqlalchemy/alembic)                                                                | Schema migrations                        |
| **Validation**      | [Pydantic](https://github.com/pydantic/pydantic)                                                                | Validation and serialization             |
| **Settings**        | [pydantic-settings](https://github.com/pydantic/pydantic-settings)                                              | Configuration from environment           |
| **DI**              | [python-injection](https://github.com/100nm/python-injection)                                                   | Dependency injection                     |
| **CQRS**            | [python-cq](https://github.com/100nm/python-cq)                                                                 | Command/Query Responsibility Segregation |
| **Lint & Format**   | [Ruff](https://github.com/astral-sh/ruff)                                                                       | Linter and formatter                     |
| **Type Checker**    | [ty](https://github.com/astral-sh/ty)                                                                           | Static type checking                     |
| **Tests**           | [pytest](https://github.com/pytest-dev/pytest) + [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio) | Test runner                              |

---

## Getting Started

### Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) (it installs Python 3.15 automatically)
- A PostgreSQL server, either local or started with `docker compose up -d database`

### Using the template

1. Create a repository from this template.
2. Rename the project in `pyproject.toml` (`name`, `description`).
3. Declare your profiles in `src/settings.py` (see [Profiles](#profiles)), if you need any.

### Quickstart

```bash
make install              # Install dependencies
cp .env.example .env      # Configure the environment (see Configuration)
cp .env.example .env.test # Configure the test environment, with another DB__NAME
make init-db              # Drop + Create + Migrate the database
DB__NAME=<test_db_name> make init-db  # Same for the test database
make dev                  # Start the API at http://localhost:8000 (docs at /docs)
```

### Docker

```bash
docker compose up --build
```

The `api` service reads `.env` and reaches the `database` service through `DB__HOST=database`. The `database` service
is created with the `root`/`root` credentials: keep the `DB__USER` and `DB__PASSWORD` defaults, or change both files.
Migrations are not applied automatically: run `uv run alembic upgrade head` against the database before using the API.

The image version is set with the `VERSION` build argument (`docker build --build-arg VERSION=1.2.3 .`) and exposed
as the FastAPI app version.

---

## Configuration (`src/settings.py`)

Settings are loaded by `pydantic-settings` from the environment and from a `.env` file. Nested settings use `__` as
delimiter (`db.name` → `DB__NAME`). See `.env.example`.

| Variable        | Default      | Description                                           |
|-----------------|--------------|-------------------------------------------------------|
| `DB__NAME`      | **required** | Database name                                         |
| `DB__USER`      | `root`       | Database user                                         |
| `DB__PASSWORD`  | `root`       | Database password                                     |
| `DB__HOST`      | `localhost`  | Database host                                         |
| `DB__PORT`      | `5432`       | Database port                                         |
| `DEBUG`         | `false`      | FastAPI debug mode                                    |
| `ALLOW_ORIGINS` | `["*"]`      | CORS allowed origins (JSON list)                      |
| `VERSION`       | `0.0.0`      | Semantic version of the application                   |
| `PROFILE`       | none         | Injection profile to load (see [Profiles](#profiles)) |

Tests read `.env.test` instead of `.env`, so that they never run against the development database.

`Settings` is registered as an injectable constant: declare a `settings: Settings` dependency to use it anywhere.

---

## Architecture

```
src/
├── core/           # Domain + Application layers (business logic)
│   └── {context}/
│       ├── domain/     # Domain layer (entities, value objects, aggregates)
│       └── ...         # Application layer (commands, queries, ports, events)
├── seedwork/       # Base classes shared by every bounded context
├── services/       # Shared technical services (cross-cutting concerns)
├── infra/          # Infrastructure layer (concrete implementations)
│   └── entrypoint.py   # Lifespan and DI scopes setup
└── settings.py     # Application settings
```

---

## Seedwork (`src/seedwork/`)

The **Seedwork** contains the base classes every bounded context builds upon. Always inherit from them instead of
`pydantic.BaseModel` directly.

| Class               | Module                | Description                                                                   |
|---------------------|-----------------------|-------------------------------------------------------------------------------|
| `Entity[ID]`        | `src/seedwork/domain` | Object with an `id`; mutable, every assignment is validated                   |
| `AggregateRoot[ID]` | `src/seedwork/domain` | Entity at the root of an aggregate, the only one loaded/saved by a repository |
| `ValueObject`       | `src/seedwork/domain` | Immutable object (`frozen=True`) without identity                             |
| `DTO`               | `src/seedwork/app`    | Immutable data transfer object (results, views)                               |
| `Command`           | `src/seedwork/app`    | Message that modifies state                                                   |
| `Query`             | `src/seedwork/app`    | Message that reads state                                                      |
| `Event`             | `src/seedwork/app`    | Message that notifies something happened                                      |

---

## Domain Layer (`src/core/{context}/domain/`)

The **Domain** layer contains pure business models: entities, value objects, and aggregates. It depends only on the
seedwork and Pydantic, never on the application layer, services or infrastructure.

### Packages

| Package    | Role          | Justification                                                     |
|------------|---------------|-------------------------------------------------------------------|
| `pydantic` | Domain models | Native validation, assignment validation, immutability for values |

### Path Patterns

| Type                             | Path Pattern                                   | Description                                                                 |
|----------------------------------|------------------------------------------------|-----------------------------------------------------------------------------|
| **Aggregate**                    | `src/core/{context}/domain/{aggregate}.py`     | Aggregate root, its states, and the entities and value objects only it uses |
| **Shared Entity / Value Object** | `src/core/{context}/domain/{shared_object}.py` | Entity or value object used by several aggregates of the context            |

An entity or value object (status enum included) lives in the module of the aggregate that uses it, and only moves to
its own module once a second aggregate of the context uses it.

### Rules

- **Pure, or at least deterministic**: no `async`, no randomness (`uuid4`, `random`), no current time
  (`datetime.now`). Such values are passed in as arguments.
- **Business validation with Pydantic**: business rules are expressed with types, field constraints and validators.
- **Mutable entities, immutable values**: entity methods change their state (validated on assignment), value objects
  are frozen. Value objects may also be immutable primitives (`Annotated[str, ...]`, `Enum`, `Decimal`).
- **One class per state when the state changes the fields**: e.g. `PendingOrder`, `ConfirmedOrder`, a transition being
  a method returning the object of the new state (`PendingOrder.confirm() -> ConfirmedOrder`).
- **Bounded collections**: a collection always has a maximum size (`Field(max_length=MAX_CART_ITEMS)`), so an
  aggregate never loads an unbounded number of items. It is a `tuple`, unless an entity needs to change it.

### Example: Aggregate `UserSession`

```python name=src/core/auth/domain/session.py
from datetime import datetime
from uuid import UUID

from pydantic import SecretStr

from src.seedwork.domain import AggregateRoot


class UserSession(AggregateRoot[UUID]):
    user_id: UUID
    created_at: datetime
    last_use_at: datetime
    secret: SecretStr
```

---

## Application Layer (`src/core/{context}/`)

The **Application** layer contains use cases and orchestration logic: commands, queries, events, and ports. Everything
in the bounded context folder except `domain/`.

Handlers live right below their message, in the same module, because every uncertain mechanism (persistence, time, id
generation, external services) is behind a port. The exception is a query handler that is a plain SQL query: it lives
in the infrastructure (see [Query Handler](#example-query-handler)).

### Packages

| Package     | Role | Justification                                |
|-------------|------|----------------------------------------------|
| `python-cq` | CQRS | Command/Query separation, handler decoupling |
| `pydantic`  | DTOs | Command/Event/Query/View validation          |

### Path Patterns

| Type                              | Path Pattern                                                | Description                                          |
|-----------------------------------|-------------------------------------------------------------|------------------------------------------------------|
| **Command**                       | `src/core/{context}/commands/{command_name}.py`             | Action that modifies state, and its handler          |
| **Query**                         | `src/core/{context}/queries/{query_name}.py`                | Data reading: query, view, and handler if port-based |
| **Event**                         | `src/core/{context}/events/{event_name}.py`                 | Event emitted by the context, and its own handlers   |
| **Event Handler (other context)** | `src/core/{context}/events/{other_context}/{event_name}.py` | Handlers reacting to another context's event         |
| **Port (Repository)**             | `src/core/{context}/ports/repo/{aggregate}.py`              | Persistence interface                                |
| **Port (Service)**                | `src/core/{context}/ports/{service}.py`                     | External service interface                           |
| **Shared**                        | `src/core/{context}/shared/{module}.py`                     | Code shared within the bounded context               |

### Naming

| Element       | Convention                                           | Example                                              |
|---------------|------------------------------------------------------|------------------------------------------------------|
| Command       | Business intent + `Command`                          | `CancelOrderCommand`, not `UpdateOrderStatusCommand` |
| Query         | `Get…` / `List…` + `Query`                           | `GetOrderQuery`                                      |
| Event         | Fact in the past tense + `Event`                     | `OrderPlacedEvent`, not `PlaceOrderEvent`            |
| View          | Result of a query or command + `View`                | `OrderView`                                          |
| Handler       | Message name without its suffix + `Handler`          | `CancelOrderHandler`, `GetOrderHandler`              |
| Event Handler | What it does + `Handler` (an event can have several) | `SendOrderConfirmationHandler`                       |

### Commands

- **Return as little as possible**: a command handler returns `None` whenever possible. To avoid returning the id of a
  created object, the entry point generates it with `UUIDGenerator` and passes it in the command.
- **Return what the caller needs right after**: when the handler produces data the caller must return right away
  (e.g. tokens, a payment URL), it returns a `View` instead of the caller dispatching a query just after.
- **Default shape**: `get()` the aggregate root from its repository → modify it → `save()` it.
- **Emit events with `RelatedEvents`**: the handler declares a `RelatedEvents` dependency and `add()`s its events.

### Example: Command with Handler

```python name=src/core/auth/commands/open_user_session.py
from typing import NamedTuple
from uuid import UUID

from cq import RelatedEvents, command_handler
from pydantic import SecretStr, field_serializer

from src.core.auth.domain.session import UserSession
from src.core.auth.events.user_session_opened import UserSessionOpenedEvent
from src.core.auth.ports.repo.user_permission import UserPermissionRepository
from src.core.auth.ports.repo.user_session import UserSessionRepository
from src.core.auth.ports.token_generator import TokenGenerator
from src.core.auth.shared.access_token import encode_access_token
from src.core.auth.shared.session_token import encode_session_token
from src.seedwork.app import DTO, Command
from src.services.datetime.abc import DateTimeService
from src.services.hasher.abc import Hasher
from src.services.jwt.abc import JWTService
from src.services.uuid.abc import UUIDGenerator


class OpenUserSessionCommand(Command):
    user_id: UUID


class UserTokensView(DTO):
    access_token: SecretStr
    session_token: SecretStr

    @field_serializer("access_token", "session_token", when_used="json")
    def _dump_secret(self, value: SecretStr) -> str:
        return value.get_secret_value()


@command_handler
class OpenUserSessionHandler(NamedTuple):
    datetime: DateTimeService
    events: RelatedEvents
    hasher: Hasher
    jwt: JWTService
    repo: UserSessionRepository
    token_generator: TokenGenerator
    user_permission_repo: UserPermissionRepository
    uuid: UUIDGenerator

    async def handle(self, command: OpenUserSessionCommand) -> UserTokensView:
        user_id = command.user_id

        session_secret = self.token_generator.generate(128)
        session = self.new_session(user_id, session_secret)
        await self.repo.save(session)
        self.events.add(UserSessionOpenedEvent(session_id=session.id, user_id=user_id))

        permissions = await self.user_permission_repo.get(user_id)
        access_token = encode_access_token(self.jwt, user_id, permissions)
        session_token = encode_session_token(session.id, session_secret)
        return UserTokensView(
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

### Events

- **Events are a context's public contract**: a bounded context only imports another context's events, never its
  domain, commands or queries.
- **Handlers live in the reacting context**: a handler of context A reacting to an event of context B lives in
  `src/core/{a}/events/{b}/{event_name}.py`. A handler reacting to its own context's event is defined right below it.
- **Only command handlers emit messages**: an event handler never dispatches a command, query or event. It does the
  work itself, shaped like a command handler (`get()` → modify → `save()`).
- **Same request, same transaction**: events added to `RelatedEvents` are dispatched to every matching
  `@event_handler` after the emitting command handler, in the same request, so they share its transaction.
- **Chain the commands at the entry point**: when a use case needs several commands, the route or CLI command
  dispatches them in order with python-cq's `dispatch_sequentially`.

### Example: Event and Handler

```python name=src/core/auth/events/user_session_opened.py
from uuid import UUID

from src.seedwork.app import Event


class UserSessionOpenedEvent(Event):
    session_id: UUID
    user_id: UUID
```

```python name=src/core/security/events/auth/user_session_opened.py
from typing import NamedTuple

from cq import event_handler

from src.core.auth.events.user_session_opened import UserSessionOpenedEvent
from src.core.security.ports.new_session_notifier import NewSessionNotifier


@event_handler
class NotifyNewSessionHandler(NamedTuple):
    notifier: NewSessionNotifier

    async def handle(self, event: UserSessionOpenedEvent) -> None:
        await self.notifier.notify(event.user_id, event.session_id)
```

### Example: Port (Repository Interface)

Ports are `Protocol`s containing only `@abstractmethod`s, each raising `NotImplementedError`, and never defining
default values. A repository only declares the methods its handlers need, and `get()` returns `None` when nothing is
found: the business error to raise is up to the handler.

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

from src.seedwork.app import DTO, Query


class GetPrivateUserProfileQuery(Query):
    user_id: UUID


class PrivateUserProfileView(DTO):
    id: UUID
    created_at: datetime
    first_name: str
    last_name: str
```

---

## Shared Services (`src/services/`)

The **Services** layer defines abstract interfaces for common technical services used across the entire application.
These are cross-cutting concerns that can be used by any layer.

### Path Patterns

| Type                  | Path Pattern                       | Description             |
|-----------------------|------------------------------------|-------------------------|
| **Service Interface** | `src/services/{service}/abc.py`    | Abstract Protocol       |
| **Implementation**    | `src/services/{service}/{impl}.py` | Concrete implementation |

DI factories of framework objects used across the project (e.g. the SQLAlchemy engine and session) live in modules at
the root of `src/services/` (`sqla.py`). They are not ports: the application layer never imports them.

### Example: Abstract Service `Hasher`

Unlike the ports of a context, the ports of `src/services/` may provide default implementations built on their
abstract methods (here `needs_rehash`).

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
        except InvalidHashError, VerificationError:  # PEP 758, catches both
            return False

    def needs_rehash(self, hashed_value: str) -> bool:
        return self.__internal.check_needs_rehash(hashed_value)
```

---

## Dependency Injection

Implementations are registered with `python-injection` decorators and resolved from type annotations: handlers,
FastAPI routes (`Inject[...]`) and CLI commands receive their dependencies automatically.

| Decorator                   | Lifetime                                         | Example                          |
|-----------------------------|--------------------------------------------------|----------------------------------|
| `@injectable(on=Protocol)`  | New instance on each injection                   | Repositories, stateless services |
| `@singleton(on=Protocol)`   | One instance for the process                     | Clients, caches                  |
| `@constant`                 | One instance, without injecting its dependencies | `Settings`                       |
| `@scoped(DIScope.LIFESPAN)` | One instance per application run                 | SQLAlchemy `AsyncEngine`         |
| `@scoped(DIScope.REQUEST)`  | One instance per request / command               | SQLAlchemy `AsyncSession`        |

The `REQUEST` scope wraps each HTTP request and each CLI command. The `AsyncSession` opens a transaction that is
committed at the end of the request, or rolled back if an exception is raised.

Only the packages loaded in `src/infra/entrypoint.py` (`core`, `services`, `infra.adapters`, `infra.query_handlers`)
are scanned for registrations. Put your implementations there, or add the package to `load_packages`. Every folder
must be a Python package (with an `__init__.py`), otherwise the loader skips it.

### Conventions

- **Inject anything unpredictable**: current time, random values, generated ids and external services always go
  through a port (`DateTimeService`, `UUIDGenerator`), never `datetime.now()` or `uuid4()`, so tests swap them instead
  of patching.
- **Adapters inherit explicitly from their port**, and are named after it, prefixed by what they use
  (`SQLAOrderRepository`, `Argon2Hasher`).
- **Adapters with attributes are `@dataclass(frozen=True)`** when their construction needs no specific logic.
- **Never inject `Settings` into an adapter**: its constructor takes only the values it needs, and a protected
  factory (`_<name>_factory`) registered in the DI receives `Settings` and builds it:

```python name=src/services/email/smtp.py
@dataclass(frozen=True)
class SMTPEmailSender(EmailSender):
    host: str
    port: int

    async def send(self, email: Email) -> None: ...


@injectable(on=EmailSender)
def _email_sender_factory(settings: Settings) -> SMTPEmailSender:
    return SMTPEmailSender(host=settings.smtp.host, port=settings.smtp.port)
```

### Profiles

A profile replaces some implementations with others in a given environment (e.g. a fake email sender in
development). Declare it in `src/settings.py`, register the alternative implementation in it, and select it with the
`PROFILE` variable.

```python name=src/settings.py
class Profile(StrEnum):
    DEV = auto()
```

```python name=src/services/email/console.py
from injection import mod

from src.services.email.abc import EmailSender
from src.settings import Profile


@mod(Profile.DEV).injectable(on=EmailSender)
class ConsoleEmailSender(EmailSender): ...
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
│   ├── dependencies.py # FastAPI dependencies (auth, locale, etc.), to create
│   └── routes/         # Endpoints by domain
├── cli/
│   ├── builder.py      # Typer configuration
│   └── apps/           # CLI commands
├── db/                 # Database
│   ├── tables.py       # SQLAlchemy table definitions
│   └── migrations/     # Alembic migrations
├── integrations/       # Third-party integrations (Stripe, etc.), to create
│   └── {provider}/
│       └── commands/   # Integration-specific commands
├── query_handlers/     # Query handlers (DB read operations)
└── entrypoint.py       # Lifespan and DI scopes setup
```

### Packages

| Package                          | Role          | Justification                            |
|----------------------------------|---------------|------------------------------------------|
| `fastapi`                        | API framework | Performance, native typing, auto OpenAPI |
| `granian` + `uvloop`             | ASGI server   | Optimal async performance                |
| `typer`                          | CLI           | FastAPI-like API, autocompletion         |
| `sqlalchemy[postgresql-asyncpg]` | Async ORM     | Native async PostgreSQL support          |
| `alembic`                        | Migrations    | Standard for SQLAlchemy                  |
| `python-injection`               | DI            | Declarative dependency injection         |

### Path Patterns

| Type                   | Path Pattern                                         | Description                       |
|------------------------|------------------------------------------------------|-----------------------------------|
| **Adapter Repository** | `src/infra/adapters/{context}/repo/{aggregate}.py`   | SQLAlchemy implementation of Port |
| **Adapter Service**    | `src/infra/adapters/{context}/{service}.py`          | Service implementation            |
| **API Route**          | `src/infra/api/routes/{route_set_name}.py`           | FastAPI endpoints                 |
| **DB Table**           | `src/infra/db/tables.py`                             | SQLAlchemy models                 |
| **Query Handler**      | `src/infra/query_handlers/{context}/{query_name}.py` | Read handler                      |
| **CLI App**            | `src/infra/cli/apps/{app_name}.py`                   | Typer commands                    |
| **Integration**        | `src/infra/integrations/{provider}/`                 | External provider specific code   |

### Example: Adapter Repository

Repositories use the SQLAlchemy query builder with `.mappings()`, and Pydantic's `model_validate` to build domain
objects. They only serve the write side (a handler loads an aggregate to modify it), so every read locks its rows with
`.with_for_update(key_share=True)`: two concurrent transitions of the same aggregate are serialized instead of the last
one silently overwriting the other. `save()` lists the columns one by one and uses `session.merge()`, so the same method
handles creation and update. Never commit manually: the session is committed at the end of the request.

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
            .with_for_update(key_share=True)
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

### Example: API Routes

An endpoint checks that the request is authorized through a reusable FastAPI dependency
(`src/infra/api/dependencies.py`), builds the command or query from the request data, and dispatches it through the
matching bus. No business logic in routes: only API-related handling, e.g. returning a 404 when a query returns `None`.

- Queries' views are returned as is.
- Every route sets its `operation_id` in UpperCamelCase, so the OpenAPI document stays clean.
- Parameters are ordered: path parameters, other request data, `Depends` dependencies, then `Inject` dependencies.

```python name=src/infra/api/routes/user.py
from typing import Annotated
from uuid import UUID

from cq import CommandBus, QueryBus
from fastapi import APIRouter, Depends, HTTPException, status
from injection.ext.fastapi import Inject

from src.core.auth.commands.open_user_session import (
    OpenUserSessionCommand,
    UserTokensView,
)
from src.core.user_profile.queries.private import (
    GetPrivateUserProfileQuery,
    PrivateUserProfileView,
)
from src.infra.api.dependencies import get_claimant_id

router = APIRouter(prefix="/users", tags=["User"])


@router.get("/me", operation_id="GetMe")
async def get_me(
    claimant_id: Annotated[UUID, Depends(get_claimant_id)],
    query_bus: Inject[QueryBus[PrivateUserProfileView | None]],
) -> PrivateUserProfileView:
    query = GetPrivateUserProfileQuery(user_id=claimant_id)
    view = await query_bus.dispatch(query)

    if view is None:
        raise HTTPException(status_code=status.HTTP_428_PRECONDITION_REQUIRED)

    return view


@router.post(
    "/me/sessions",
    operation_id="OpenSession",
    status_code=status.HTTP_201_CREATED,
)
async def open_session(
    claimant_id: Annotated[UUID, Depends(get_claimant_id)],
    command_bus: Inject[CommandBus[UserTokensView]],
) -> UserTokensView:
    command = OpenUserSessionCommand(user_id=claimant_id)
    return await command_bus.dispatch(command)
```

### Example: Query Handler

A query returns its own view, shaped for the reader, never a domain object. By default, query handlers read the same
tables as the commands, and build their view like repositories build domain objects.

```python name=src/infra/query_handlers/user_profile/private.py
from typing import NamedTuple

from cq import query_handler
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.user_profile.domain.user import UserStatus
from src.core.user_profile.queries.private import (
    GetPrivateUserProfileQuery,
    PrivateUserProfileView,
)
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

### Example: CLI App

CLI commands are synchronous Typer functions. Wrap the async body with `@main(autocall=True)` from
`src/infra/entrypoint.py`: it opens the lifespan and request scopes, injects the parameters, and runs it with uvloop.

```python name=src/infra/cli/apps/user.py
from typing import Annotated
from uuid import UUID

from cq import CommandBus
from typer import Argument, Typer, echo

from src.core.auth.commands.open_user_session import (
    OpenUserSessionCommand,
    UserTokensView,
)
from src.infra.entrypoint import main

app = Typer(name="user")


@app.command("open-session")
def open_session(user_id: Annotated[UUID, Argument()]) -> None:
    @main(autocall=True)
    async def _(command_bus: CommandBus[UserTokensView]) -> None:
        tokens = await command_bus.dispatch(OpenUserSessionCommand(user_id=user_id))
        echo(tokens.model_dump_json())
```

```bash
uv run main.py user open-session <user_id>
```

---

## Main script (`main.py`)

The `main.py` file is the entry point for both the API (`granian main:app`) and the CLI (`uv run main.py ...`).
Routers and CLI apps must be manually registered here.

```python name=main.py
from injection import find_instance

from src.infra.api.builder import FastAPIBuilder
from src.infra.api.routes import user
from src.infra.cli.apps import db
from src.infra.cli.builder import TyperBuilder

if __name__ == "__main__":
    cli = (
        find_instance(TyperBuilder)
        .include_apps(
            db.app,
            # Add your typer apps here.
        )
        .build()
    )
    cli()

else:
    app = (
        find_instance(FastAPIBuilder)
        .include_routers(
            user.router,
            # Add your routers here.
        )
        .build()
    )
```

When adding new routes or CLI commands:

- **New API router**: Add `from src.infra.api.routes import {module}` and include `{module}.router` in
  `include_routers()`
- **New CLI app**: Add `from src.infra.cli.apps import {module}` and include `{module}.app` in `include_apps()`

---

## Testing (`tests/`)

Tests need a PostgreSQL database configured in `.env.test`. Environment variables take precedence over `.env`, so it
can be prepared with `DB__NAME=<test_db_name> make init-db`.

Two fixtures from `conftest.py` are applied to every test:

- `load_test_impl` loads `tests/impl/` and activates the test implementations.
- `test_client` starts the FastAPI app and provides an `httpx` `AsyncClient` to call it.

Both fixtures run around every test (test profile, then the app's lifespan), so singletons and scoped instances are
reset between tests. Each test runs inside a
single database transaction that is **rolled back** at the end, so tests are isolated and leave the database unchanged.

### What to test

- **Domain**: business rules only, not model structure nor Pydantic's own behavior.
- **Commands and queries**: their handlers, dispatched through the buses.
- **Events**: that commands emit the expected events, and the side effects of event handlers (through the ports).
- **Adapters replaced during tests**: since tests never exercise them otherwise, they get their own tests.
- **API endpoints**: the returned status code and, when there is one, the JSON body.

### Writing

- Tests mirror the `src/` tree: `src/core/{context}/domain/order.py` is tested in
  `tests/core/{context}/domain/test_order.py`.
- Tests of a method are grouped in a `Test<ClassName>` class (`Test<EndpointFunction>` for API endpoints), and named
  `test_<method>_<with|without>_<condition>[_<returns|raises>_<result>]`, e.g.
  `test_add_item_with_quantity_zero_raises_validation_error`, `test_place_order_with_empty_address_returns_422`.
- Dependencies (buses included) are retrieved with `LazyInstance`, or `aget_lazy_instance` when they need an async
  getter (e.g. a repository depending on the `AsyncSession`).
- The context is set up by dispatching the commands that lead to it (`dispatch_sequentially`), kept separate from the
  tested action.
- Only write test implementations (`tests/impl/`) for unpredictable or slow adapters. SQL repositories are kept: tests
  run against the database.
- A test never patches an attribute or a function: needing one means the value should be injectable. Environment
  variables (`monkeypatch.setenv`) are the exception.

### Example: Command Handler Test

```python name=tests/core/ordering/commands/test_cancel_order.py
from cq import CommandBus, dispatch_sequentially
from injection import LazyInstance, aget_lazy_instance

from src.core.ordering.commands.cancel_order import CancelOrderCommand
from src.core.ordering.commands.place_order import PlaceOrderCommand
from src.core.ordering.domain.order import CancelledOrder
from src.core.ordering.ports.repo.order import CancelledOrderRepository
from src.services.uuid.abc import UUIDGenerator


class TestCancelOrderHandler:
    command_bus = LazyInstance(CommandBus[None])
    repo = aget_lazy_instance(CancelledOrderRepository)
    uuid_generator = LazyInstance(UUIDGenerator)

    async def test_handle_with_placed_order(self):
        order_id = self.uuid_generator.next()
        await dispatch_sequentially(
            self.command_bus,
            PlaceOrderCommand(order_id=order_id, shipping_address="..."),
        )

        command = CancelOrderCommand(order_id=order_id)
        await self.command_bus.dispatch(command)

        repo = await self.repo
        order = await repo.get(order_id)
        assert isinstance(order, CancelledOrder)
```

### Structure

```
tests/
├── impl/               # Test implementations (deterministic replacements)
│   ├── services/       # Service test implementations
│   ├── adapters/       # Adapter test implementations
│   └── settings.py     # Test settings (reads .env.test)
├── core/               # Domain and application tests
├── infra/              # Infrastructure tests
└── services/           # Service tests
```

### Example: Deterministic Hasher

Test implementations should be placed in `tests/impl/`. They replace production services during tests, making tests
predictable and fast. Production uses `Argon2Hasher`, which is slow and non-deterministic. For tests, we use a simple
`SHA256Hasher`:

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

The `@test_injectable(on=Hasher)` decorator registers this implementation only during test execution, replacing the
production `Argon2Hasher`.

### Example: API Test

```python name=tests/infra/api/routes/test_user.py
from fastapi import status
from httpx2 import AsyncClient


class TestGetMe:
    async def test_get_me_without_token_returns_401(self, test_client: AsyncClient):
        response = await test_client.get("/users/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
```

---

## Commands

```bash
# Installation
make install              # Install dependencies
make update               # Upgrade dependencies (lock + sync)

# Development
make dev                  # Start granian server in reload mode

# Database
make create-db            # Create the database
make drop-db              # Drop the database
make init-db              # Drop + Create + Migrate
make migrate              # Apply migrations
make makemigrations       # Generate a new migration

# Code quality
make lint                 # Ruff format + check (with fixes)
make type-check           # ty type checking
make pytest               # Run tests
make                      # Same as `make before-commit`: lint + type-check + pytest
```

The CI (`.github/workflows/ci-checks.yml`) runs the same checks, plus `alembic check` to detect missing migrations.

---

## Architecture Rules

### Do

1. **Inherit from the seedwork** - Use `Entity`, `AggregateRoot`, `ValueObject`, `DTO`, `Command`, `Query`, `Event`
2. **Use Protocols** - Define interfaces in `ports/` (or `services/{service}/abc.py`) for dependency inversion
3. **Commands for writes** - All state modifications go through a Command
4. **Queries for reads** - All reads go through a Query, returning a View
5. **Events between contexts** - Bounded contexts communicate only through events
6. **Dependency injection** - Use `@injectable(on=Protocol)` for implementations, inject anything unpredictable
7. **Register routers and apps** - Always add new routers and CLI apps in `main.py`

### Don't

1. **No outward imports in the domain** - `src/core/{context}/domain/` only imports the standard library, Pydantic,
   `src/seedwork/` and its own context's domain
2. **No infra imports in core** - The application layer never imports `src/infra/`, and from `src/services/` only
   imports the ports (`abc.py`)
3. **No cross-context imports** - A context only imports another context's events, never its domain, commands or
   queries (the infrastructure is the exception)
4. **No SQLAlchemy in core** - Tables are only in `src/infra/db/tables.py`
5. **No business logic in routes** - Routes only dispatch Commands/Queries
6. **No messages from handlers** - Only command handlers emit events (`RelatedEvents`); no handler dispatches a
   command or query
7. **No manual commit** - The session is committed at the end of the request
