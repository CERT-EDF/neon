"""Neon Constant"""

from dataclasses import dataclass, field

from edf_fusion.concept import Concept
from edf_fusion.concept import Constant as FusionConstant
from edf_fusion.concept import Status

from .indicator import IndicatorNature
from .sample import OperatingSystem


@dataclass(kw_only=True)
class GlobSecret(Concept):
    """Glob Secret"""

    glob: str
    secret: str

    @classmethod
    def from_dict(cls, dct):
        return cls(glob=dct['glob'], secret=dct['secret'])

    def to_dict(self):
        return {'glob': self.glob, 'secret': self.secret}

    def update(self, dct):
        raise RuntimeError("GlobSecret.update shall not be called!")


def _enums() -> dict[str, list[str]]:
    return {
        'status': [status.value for status in Status],
        'opsystem': [opsystem.value for opsystem in OperatingSystem],
        'indicator_nature': [nature.value for nature in IndicatorNature],
    }


@dataclass(kw_only=True)
class Constant(FusionConstant):
    """Neon Constant"""

    tags: set[str] = field(default_factory=set)
    globs: list[GlobSecret] = field(default_factory=list)
    enums: dict[str, list[str]] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, dct):
        constant = super().from_dict(dct)
        constant.tags = set(dct.get('tags', []))
        constant.globs = [
            GlobSecret.from_dict(glob) for glob in dct.get('globs', [])
        ]
        constant.enums = _enums()
        return constant

    def to_dict(self):
        dct = super().to_dict()
        dct.update(
            {
                'tags': list(self.tags),
                'globs': [glob.to_dict() for glob in self.globs],
                'enums': self.enums,
            }
        )
        return dct
