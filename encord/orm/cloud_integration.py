from dataclasses import dataclass


@dataclass(frozen=True)
class CloudIntegration:
    id: str
    title: str
