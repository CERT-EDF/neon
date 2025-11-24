"""Neon Digest Match"""

from dataclasses import dataclass, field

from edf_fusion.concept import Concept

from .case import Case
from .sample import Sample


@dataclass(kw_only=True)
class CaseHit(Concept):
    """Neon Case Hit"""

    case: Case
    sample: Sample

    @classmethod
    def from_dict(cls, dct):
        return cls(
            case=Case.from_dict(dct['case']),
            sample=Case.from_dict(dct['sample']),
        )

    def to_dict(self):
        return {
            'case': self.case.to_dict(),
            'sample': self.sample.to_dict(),
        }

    def update(self, dct):
        """Update case with dct"""
        raise RuntimeError("CaseHit.update shall not be called!")


@dataclass(kw_only=True)
class DigestHits(Concept):
    """Neon Digest Hits"""

    total: int = 0
    hits: list[CaseHit] = field(default_factory=list)

    @classmethod
    def from_dict(cls, dct):
        return cls(
            total=dct['total'],
            hits=[CaseHit.from_dict(hit) for hit in dct['hits']],
        )

    def to_dict(self):
        return {
            'total': self.total,
            'hits': [hit.to_dict() for hit in self.hits],
        }

    def update(self, dct):
        """Update case with dct"""
        raise RuntimeError("DigestHits.update shall not be called!")
