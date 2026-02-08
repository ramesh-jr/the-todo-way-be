# The Todo Way - Backend Low-Level Design

> **Version**: v1 | **Created**: 2026-02-07 | **Last Updated**: 2026-02-07
> **Scope**: Backend-specific implementation details. For full project LLD see the FE repo.

---

## 1. Database Schema

### 1.1 Models Overview

| Table | Description |
|-------|-------------|
| `users` | Single user account (simple auth) |
| `todos` | Core todo items with all fields |
| `sections` | Top-level grouping (like Todoist Projects) |
| `subsections` | Nested within sections |
| `labels` | Color-coded tags |
| `todo_labels` | Many-to-many join table |
| `reminders` | Reminder entries (stored, not delivered in MVP) |

### 1.2 SQLAlchemy Models

```python
# app/db/base.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import func
from datetime import datetime

class Base(DeclarativeBase):
    pass

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())
```

```python
# app/models/user.py
class User(Base, TimestampMixin):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    todos: Mapped[list["Todo"]] = relationship(back_populates="user")
    sections: Mapped[list["Section"]] = relationship(back_populates="user")
    labels: Mapped[list["Label"]] = relationship(back_populates="user")
```

```python
# app/models/todo.py
class Todo(Base, TimestampMixin):
    __tablename__ = "todos"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    scheduled_date: Mapped[datetime | None] = mapped_column(index=True)
    deadline_date: Mapped[datetime | None] = mapped_column(index=True)
    duration_minutes: Mapped[int | None]
    priority: Mapped[str] = mapped_column(String(2), default="p4")
    location: Mapped[str | None] = mapped_column(String(500))
    is_completed: Mapped[bool] = mapped_column(default=False, index=True)
    completed_at: Mapped[datetime | None]
    section_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("sections.id"), index=True)
    subsection_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("subsections.id"))

    user: Mapped["User"] = relationship(back_populates="todos")
    section: Mapped["Section | None"] = relationship(back_populates="todos")
    subsection: Mapped["Subsection | None"] = relationship(back_populates="todos")
    labels: Mapped[list["Label"]] = relationship(secondary="todo_labels", back_populates="todos")
    reminders: Mapped[list["Reminder"]] = relationship(back_populates="todo", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_todos_user_completed", "user_id", "is_completed"),
        Index("ix_todos_user_section", "user_id", "section_id"),
        Index("ix_todos_user_scheduled", "user_id", "scheduled_date"),
    )
```

```python
# app/models/section.py
class Section(Base, TimestampMixin):
    __tablename__ = "sections"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    sort_order: Mapped[int] = mapped_column(default=0)
    user: Mapped["User"] = relationship(back_populates="sections")
    subsections: Mapped[list["Subsection"]] = relationship(back_populates="section", cascade="all, delete-orphan")
    todos: Mapped[list["Todo"]] = relationship(back_populates="section")

class Subsection(Base):
    __tablename__ = "subsections"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    section_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sections.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    sort_order: Mapped[int] = mapped_column(default=0)
    section: Mapped["Section"] = relationship(back_populates="subsections")
    todos: Mapped[list["Todo"]] = relationship(back_populates="subsection")
```

```python
# app/models/label.py
class Label(Base):
    __tablename__ = "labels"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    color: Mapped[str] = mapped_column(String(7))  # hex color
    user: Mapped["User"] = relationship(back_populates="labels")
    todos: Mapped[list["Todo"]] = relationship(secondary="todo_labels", back_populates="labels")

todo_labels = Table(
    "todo_labels", Base.metadata,
    Column("todo_id", ForeignKey("todos.id", ondelete="CASCADE"), primary_key=True),
    Column("label_id", ForeignKey("labels.id", ondelete="CASCADE"), primary_key=True),
)
```

```python
# app/models/reminder.py
class Reminder(Base):
    __tablename__ = "reminders"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    todo_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("todos.id"), index=True)
    remind_at: Mapped[datetime]
    type: Mapped[str] = mapped_column(String(20))  # before_5min, before_15min, etc.
    todo: Mapped["Todo"] = relationship(back_populates="reminders")
```

---

## 2. Pydantic Schemas

### 2.1 Response Wrapper

```python
# app/schemas/response.py
from typing import TypeVar, Generic
T = TypeVar("T")

class PaginationMeta(BaseModel):
    total: int
    page: int
    per_page: int
    total_pages: int

class ApiResponse(BaseModel, Generic[T]):
    data: T
    error: str | None = None
    meta: PaginationMeta | None = None
```

### 2.2 Todo Schemas

```python
# app/schemas/todo.py
class TodoBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    scheduled_date: datetime | None = None
    deadline_date: datetime | None = None
    duration_minutes: int | None = Field(None, ge=5, le=480)
    priority: Literal["p1", "p2", "p3", "p4"] = "p4"
    location: str | None = Field(None, max_length=500)
    section_id: uuid.UUID | None = None
    subsection_id: uuid.UUID | None = None
    label_ids: list[uuid.UUID] = []
    reminders: list[ReminderCreate] = []

class TodoCreate(TodoBase):
    pass

class TodoUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    scheduled_date: datetime | None = None
    deadline_date: datetime | None = None
    duration_minutes: int | None = Field(None, ge=5, le=480)
    priority: Literal["p1", "p2", "p3", "p4"] | None = None
    location: str | None = None
    section_id: uuid.UUID | None = None
    subsection_id: uuid.UUID | None = None
    label_ids: list[uuid.UUID] | None = None

class TodoSchedule(BaseModel):
    scheduled_date: datetime
    duration_minutes: int = Field(default=30, ge=5, le=480)

class TodoResponse(TodoBase):
    id: uuid.UUID
    is_completed: bool
    completed_at: datetime | None
    labels: list[LabelResponse]
    reminders: list[ReminderResponse]
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
```

### 2.3 Section Schemas

```python
class SectionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)

class SubsectionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)

class SubsectionResponse(BaseModel):
    id: uuid.UUID
    name: str
    sort_order: int
    section_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

class SectionResponse(BaseModel):
    id: uuid.UUID
    name: str
    sort_order: int
    subsections: list[SubsectionResponse]
    model_config = ConfigDict(from_attributes=True)
```

### 2.4 Label Schemas

```python
class LabelCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    color: str = Field(..., pattern=r"^#[0-9a-fA-F]{6}$")

class LabelResponse(BaseModel):
    id: uuid.UUID
    name: str
    color: str
    model_config = ConfigDict(from_attributes=True)
```

### 2.5 Auth Schemas

```python
class AuthSetup(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)

class AuthLogin(BaseModel):
    username: str
    password: str

class AuthToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
```

---

## 3. API Endpoints (Full Contract)

### 3.1 Auth

| Method | Path | Request Body | Response | Status |
|--------|------|-------------|----------|--------|
| `POST` | `/api/v1/auth/setup` | `AuthSetup` | `ApiResponse[AuthToken]` | 201 / 409 |
| `POST` | `/api/v1/auth/login` | `AuthLogin` | `ApiResponse[AuthToken]` | 200 / 401 |

- `setup`: Only works if no user exists. Creates user + returns JWT. Returns 409 if user already exists.
- `login`: Verifies credentials, returns JWT. Returns 401 if invalid.

### 3.2 Todos

| Method | Path | Query Params | Request Body | Response | Status |
|--------|------|-------------|-------------|----------|--------|
| `GET` | `/api/v1/todos` | `page, per_page, sort_by, sort_order, section_id, priority, show_completed, date_from, date_to, label_ids` | -- | `ApiResponse[list[TodoResponse]]` | 200 |
| `POST` | `/api/v1/todos` | -- | `TodoCreate` | `ApiResponse[TodoResponse]` | 201 |
| `GET` | `/api/v1/todos/{id}` | -- | -- | `ApiResponse[TodoResponse]` | 200 / 404 |
| `PUT` | `/api/v1/todos/{id}` | -- | `TodoUpdate` | `ApiResponse[TodoResponse]` | 200 / 404 |
| `DELETE` | `/api/v1/todos/{id}` | -- | -- | -- | 204 / 404 |
| `PATCH` | `/api/v1/todos/{id}/complete` | -- | -- | `ApiResponse[TodoResponse]` | 200 / 404 |
| `PATCH` | `/api/v1/todos/{id}/schedule` | -- | `TodoSchedule` | `ApiResponse[TodoResponse]` | 200 / 404 |

### 3.3 Sections & Subsections

| Method | Path | Request Body | Response | Status |
|--------|------|-------------|----------|--------|
| `GET` | `/api/v1/sections` | -- | `ApiResponse[list[SectionResponse]]` | 200 |
| `POST` | `/api/v1/sections` | `SectionCreate` | `ApiResponse[SectionResponse]` | 201 |
| `PUT` | `/api/v1/sections/{id}` | `SectionCreate` | `ApiResponse[SectionResponse]` | 200 / 404 |
| `DELETE` | `/api/v1/sections/{id}` | -- | -- | 204 / 404 |
| `POST` | `/api/v1/sections/{id}/subsections` | `SubsectionCreate` | `ApiResponse[SubsectionResponse]` | 201 |
| `PUT` | `/api/v1/subsections/{id}` | `SubsectionCreate` | `ApiResponse[SubsectionResponse]` | 200 / 404 |
| `DELETE` | `/api/v1/subsections/{id}` | -- | -- | 204 / 404 |

### 3.4 Labels

| Method | Path | Request Body | Response | Status |
|--------|------|-------------|----------|--------|
| `GET` | `/api/v1/labels` | -- | `ApiResponse[list[LabelResponse]]` | 200 |
| `POST` | `/api/v1/labels` | `LabelCreate` | `ApiResponse[LabelResponse]` | 201 |
| `PUT` | `/api/v1/labels/{id}` | `LabelCreate` | `ApiResponse[LabelResponse]` | 200 / 404 |
| `DELETE` | `/api/v1/labels/{id}` | -- | -- | 204 / 404 |

---

## 4. Service Layer

### 4.1 TodoService

```python
class TodoService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_todos(self, user_id, page, per_page, sort_by, sort_order,
                         section_id, priority, show_completed, date_from, date_to,
                         label_ids) -> tuple[list[Todo], int]:
        """List todos with filtering, sorting, pagination. Returns (todos, total_count)."""

    async def get_todo(self, user_id, todo_id) -> Todo:
        """Get single todo. Raises NotFoundException if not found."""

    async def create_todo(self, user_id, data: TodoCreate) -> Todo:
        """Create todo, attach labels, create reminders."""

    async def update_todo(self, user_id, todo_id, data: TodoUpdate) -> Todo:
        """Partial update. Re-sync labels if label_ids provided."""

    async def delete_todo(self, user_id, todo_id) -> None:
        """Delete todo. Raises NotFoundException if not found."""

    async def toggle_complete(self, user_id, todo_id) -> Todo:
        """Toggle is_completed. Set/clear completed_at."""

    async def schedule_todo(self, user_id, todo_id, data: TodoSchedule) -> Todo:
        """Update scheduled_date and duration_minutes (drag-and-drop)."""
```

### 4.2 SectionService

```python
class SectionService:
    async def list_sections(self, user_id) -> list[Section]:
        """All sections with subsections, ordered by sort_order."""

    async def create_section(self, user_id, data: SectionCreate) -> Section:
    async def update_section(self, user_id, section_id, data: SectionCreate) -> Section:
    async def delete_section(self, user_id, section_id) -> None:
        """Delete section. Set todos' section_id=None (don't cascade delete todos)."""

    async def create_subsection(self, user_id, section_id, data: SubsectionCreate) -> Subsection:
    async def update_subsection(self, user_id, subsection_id, data: SubsectionCreate) -> Subsection:
    async def delete_subsection(self, user_id, subsection_id) -> None:
```

### 4.3 LabelService

```python
class LabelService:
    async def list_labels(self, user_id) -> list[Label]:
    async def create_label(self, user_id, data: LabelCreate) -> Label:
    async def update_label(self, user_id, label_id, data: LabelCreate) -> Label:
    async def delete_label(self, user_id, label_id) -> None:
        """Delete label. Cascades removal from todo_labels."""
```

### 4.4 AuthService

```python
class AuthService:
    async def setup(self, data: AuthSetup) -> AuthToken:
        """Create first user. Raises ConflictException if user exists."""

    async def login(self, data: AuthLogin) -> AuthToken:
        """Verify credentials. Raises 401 if invalid."""
```

---

## 5. Configuration

```python
# app/core/config.py
class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiry_days: int = 7
    environment: str = "local"  # local | staging | production
    cors_origins: list[str] = ["http://localhost:5173"]
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
```

---

## 6. Error Handling

```python
# app/core/exceptions.py
class AppException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)

class NotFoundException(AppException):
    def __init__(self, resource: str = "Resource"):
        super().__init__(404, f"{resource} not found")

class ConflictException(AppException):
    def __init__(self, detail: str):
        super().__init__(409, detail)

# Global handler (registered in main.py):
@app.exception_handler(AppException)
async def app_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiResponse(data=None, error=exc.detail).model_dump()
    )
```

---

## 7. Database Session

```python
# app/db/session.py
engine = create_async_engine(settings.database_url, echo=settings.environment == "local", pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
```

---

## 8. Auth Flow

```python
# app/core/security.py
# JWT: python-jose, HS256, payload: { sub: str(user_id), exp: datetime }
# Password: passlib[bcrypt]
# Token expiry: settings.jwt_expiry_days (default 7)

def create_access_token(user_id: uuid.UUID) -> str: ...
def verify_token(token: str) -> dict: ...
def hash_password(password: str) -> str: ...
def verify_password(plain: str, hashed: str) -> bool: ...

# Dependency:
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User: ...
```

---

## 9. Soft Delete / Cascade Rules

| Action | Behavior |
|--------|----------|
| Delete a section | Set `todos.section_id = NULL` for affected todos. Delete subsections (cascade). |
| Delete a subsection | Set `todos.subsection_id = NULL` for affected todos. |
| Delete a label | Remove from `todo_labels` join table (cascade). |
| Delete a todo | Delete associated `reminders` (cascade). Remove from `todo_labels` (cascade). |
| Complete a todo | Set `is_completed=True`, `completed_at=now()`. |
| Un-complete a todo | Set `is_completed=False`, `completed_at=None`. |

---

## 10. Build Conversations (BE-1 through BE-6)

- **BE-1**: Implement `app/main.py`, `app/core/config.py`, `app/core/exceptions.py`, `app/db/session.py`, `app/schemas/response.py`, `app/api/v1/__init__.py`. Wire up FastAPI app with CORS, exception handlers. Verify `uvicorn app.main:app` starts.
- **BE-2**: Implement all models in `app/models/` per Section 1.2. Implement `app/db/base.py`. Configure `alembic/env.py`. Generate and run initial migration.
- **BE-3**: Implement `app/core/security.py` and `app/core/dependencies.py` per Section 8. Implement `app/services/auth_service.py` and `app/api/v1/routes/auth.py`. Test setup + login.
- **BE-4**: Implement `app/schemas/todo.py`, `app/services/todo_service.py`, `app/api/v1/routes/todos.py` per Sections 2.2, 3.2, 4.1.
- **BE-5**: Implement schemas, services, routes for sections/subsections and labels per Sections 2.3, 2.4, 3.3, 3.4, 4.2, 4.3.
- **BE-6**: Implement `tests/conftest.py` with test DB + async client. Write tests for all endpoints.
