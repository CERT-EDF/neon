"""Neon Case"""

from dataclasses import dataclass

from edf_fusion.concept import Case as FusionCase


@dataclass(kw_only=True)
class Case(FusionCase):
    """Neon Case"""

    report: str | None = None

    @classmethod
    def from_dict(cls, dct):
        metadata = super().from_dict(dct)
        metadata.report = dct.get('report')
        return metadata

    def to_dict(self):
        dct = super().to_dict()
        dct.update({'report': self.report})
        return dct

    def update(self, dct):
        """Update case with dct"""
        super().update(dct)
        self.report = dct.get('report', self.report)
