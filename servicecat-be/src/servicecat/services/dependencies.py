"""Service dependency graph: declare/remove edges (cycle-checked) and traverse."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from typing import TYPE_CHECKING

from servicecat.errors import ConflictError, DomainValidationError, NotFoundError
from servicecat.models import DependencyCriticality, DependencyDirection, ServiceDependency
from servicecat.repositories.service_dependencies import ServiceDependencyRepository
from servicecat.repositories.services import ServiceRepository

if TYPE_CHECKING:
    import uuid
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class DependencyEdge:
    """A dependency edge annotated with its hop distance from the root service."""

    dependency: ServiceDependency
    depth: int


class ServiceDependencyService:
    """Manages the workspace's service dependency graph."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._deps = ServiceDependencyRepository(db)
        self._services = ServiceRepository(db)

    async def add(
        self,
        *,
        workspace_id: uuid.UUID,
        service_id: uuid.UUID,
        depends_on_service_id: uuid.UUID,
        criticality: DependencyCriticality,
        direction: DependencyDirection,
    ) -> ServiceDependency:
        if service_id == depends_on_service_id:
            raise DomainValidationError("A service cannot depend on itself")
        if await self._services.get(service_id) is None:
            raise NotFoundError("Service not found")
        if await self._services.get(depends_on_service_id) is None:
            raise DomainValidationError("Target dependency service not found")

        edges = await self._deps.all_edges()
        if any(
            edge.service_id == service_id and edge.depends_on_service_id == depends_on_service_id
            for edge in edges
        ):
            raise ConflictError("Dependency already exists")
        if _would_create_cycle(edges, source=service_id, target=depends_on_service_id):
            raise DomainValidationError("Dependency would create a cycle")

        dependency = ServiceDependency(
            workspace_id=workspace_id,
            service_id=service_id,
            depends_on_service_id=depends_on_service_id,
            criticality=criticality,
            direction=direction,
        )
        await self._deps.add(dependency)
        return dependency

    async def remove(self, service_id: uuid.UUID, dependency_id: uuid.UUID) -> None:
        dependency = await self._deps.get(dependency_id)
        if dependency is None or dependency.service_id != service_id:
            raise NotFoundError("Dependency not found")
        await self._deps.delete(dependency)

    async def list_dependencies(
        self,
        service_id: uuid.UUID,
        *,
        depth: int,
    ) -> list[DependencyEdge]:
        if await self._services.get(service_id) is None:
            raise NotFoundError("Service not found")
        edges = await self._deps.all_edges()
        return _bfs(edges, root=service_id, max_depth=depth)


def _adjacency(
    edges: Sequence[ServiceDependency],
) -> defaultdict[uuid.UUID, list[ServiceDependency]]:
    by_source: defaultdict[uuid.UUID, list[ServiceDependency]] = defaultdict(list)
    for edge in edges:
        by_source[edge.service_id].append(edge)
    return by_source


def _would_create_cycle(
    edges: Sequence[ServiceDependency],
    *,
    source: uuid.UUID,
    target: uuid.UUID,
) -> bool:
    """Adding source->target cycles iff target can already reach source."""
    by_source = _adjacency(edges)
    seen: set[uuid.UUID] = set()
    stack = [target]
    while stack:
        node = stack.pop()
        if node == source:
            return True
        if node in seen:
            continue
        seen.add(node)
        stack.extend(edge.depends_on_service_id for edge in by_source[node])
    return False


def _bfs(
    edges: Sequence[ServiceDependency],
    *,
    root: uuid.UUID,
    max_depth: int,
) -> list[DependencyEdge]:
    by_source = _adjacency(edges)
    level: dict[uuid.UUID, int] = {root: 0}
    queue: deque[uuid.UUID] = deque([root])
    result: list[DependencyEdge] = []
    while queue:
        node = queue.popleft()
        node_depth = level[node]
        if node_depth >= max_depth:
            continue
        for edge in by_source[node]:
            result.append(DependencyEdge(dependency=edge, depth=node_depth + 1))
            if edge.depends_on_service_id not in level:
                level[edge.depends_on_service_id] = node_depth + 1
                queue.append(edge.depends_on_service_id)
    return result
