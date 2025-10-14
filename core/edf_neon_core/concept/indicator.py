"""Neon Indicator"""

from dataclasses import dataclass
from enum import Enum

from edf_fusion.concept import Concept


class IndicatorNature(Enum):
    """Nature of the indicator"""

    ACCOUNT = 'account'
    COMMAND = 'command'
    CUSTOM = 'custom'
    DOMAIN = 'domain'
    EMAIL = 'email'
    FQDN = 'fqdn'
    FILESYSTEM = 'filesystem'
    IPV4 = 'ipv4'
    IPV6 = 'ipv6'
    MD5 = 'md5'
    REGISTRY = 'registry'
    SHA1 = 'sha1'
    SHA256 = 'sha256'
    SHA512 = 'sha512'
    URL = 'url'
    USER_AGENT = 'user_agent'


@dataclass(kw_only=True)
class Indicator(Concept):
    """Indicator"""

    value: str
    nature: IndicatorNature

    @classmethod
    def from_dict(cls, dct):
        return cls(
            value=dct['value'],
            nature=IndicatorNature(dct['nature']),
        )

    def to_dict(self):
        return {
            'value': self.value,
            'nature': self.nature.value,
        }

    def update(self, dct: dict):
        self.value = dct.get('value', self.value)
        self.nature = IndicatorNature(dct.get('nature', self.nature))
