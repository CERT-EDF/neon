"""Neon Sample"""

from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID, uuid4

from edf_fusion.concept import Concept
from edf_fusion.helper.datetime import (
    datetime,
    from_iso,
    from_iso_or_none,
    to_iso,
    to_iso_or_none,
    utcnow,
)

from .digests import Digests
from .indicator import Indicator


class RulesetNature(Enum):
    """Nature of the ruleset"""

    YARA = 'yara'
    CAPA = 'capa'


class OperatingSystem(Enum):
    """Operating system"""

    ANY = 'any'
    IOS = 'ios'
    LINUX = 'linux'
    DARWIN = 'darwin'
    ANDROID = 'android'
    WINDOWS = 'windows'
    UNDEFINED = 'undefined'


Tags = set[str]
Symbols = dict[int, str]
Rulesets = dict[RulesetNature, str]


def _default_rulesets() -> Rulesets:
    return {nature: '' for nature in RulesetNature}


@dataclass(kw_only=True)
class Sample(Concept):
    """Sample metadata"""

    guid: UUID = field(default_factory=uuid4)
    created: datetime = field(default_factory=utcnow)
    updated: datetime | None = None
    name: str
    size: int
    tags: Tags = field(default_factory=set)
    report: str = ''
    digests: Digests
    symbols: Symbols = field(default_factory=dict)
    rulesets: Rulesets = field(default_factory=_default_rulesets)
    opsystem: OperatingSystem = OperatingSystem.UNDEFINED
    indicators: list[Indicator] = field(default_factory=list)

    @property
    def primary_digest(self) -> str:
        """Digest used as unique identifier"""
        return self.digests.primary_digest

    @classmethod
    def from_dict(cls, dct):
        return cls(
            guid=UUID(dct['guid']),
            created=from_iso(dct['created']),
            updated=from_iso_or_none(dct['updated']),
            name=dct['name'],
            size=dct['size'],
            tags=set(dct['tags']),
            report=dct['report'],
            digests=Digests.from_dict(dct['digests']),
            symbols={
                int(address): label
                for address, label in dct['symbols'].items()
            },
            rulesets={
                RulesetNature(nature): data
                for nature, data in dct['rulesets'].items()
            },
            opsystem=OperatingSystem(dct['opsystem']),
            indicators=[
                Indicator.from_dict(item) for item in dct['indicators']
            ],
        )

    def to_dict(self):
        return {
            'guid': str(self.guid),
            'created': to_iso(self.created),
            'updated': to_iso_or_none(self.updated),
            'name': self.name,
            'size': self.size,
            'tags': list(sorted(self.tags)),
            'report': self.report,
            'digests': self.digests.to_dict(),
            'symbols': self.symbols,
            'rulesets': {
                nature.value: data for nature, data in self.rulesets.items()
            },
            'opsystem': self.opsystem.value,
            'indicators': [
                indicator.to_dict() for indicator in self.indicators
            ],
        }

    def update(self, dct: dict):
        # guid cannot be updated
        # created cannot be updated
        self.updated = utcnow()
        self.name = dct.get('name', self.name)
        # size cannot be updated
        self.tags = set(dct.get('tags', self.tags))
        self.report = dct.get('report', self.report)
        # digests cannot be updated
        self.symbols = dct.get('symbols', self.symbols)
        self.rulesets.update(
            {
                RulesetNature(nature): data
                for nature, data in dct.get('rulesets', {}).items()
            }
        )
        self.opsystem = OperatingSystem(dct.get('opsystem', self.opsystem))
        indicators = dct.get('indicators', [])
        if indicators:
            self.indicators = [
                Indicator.from_dict(item) for item in indicators
            ]
