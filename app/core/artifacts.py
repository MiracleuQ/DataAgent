from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import uuid


def _artifact_id() -> str:
    return f"artifact_{uuid.uuid4().hex[:12]}"


@dataclass
class Artifact:
    kind: str
    title: str
    summary: str
    data: Any = None
    path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=_artifact_id)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "title": self.title,
            "summary": self.summary,
            "data": self.data,
            "path": self.path,
            "metadata": self.metadata,
        }
