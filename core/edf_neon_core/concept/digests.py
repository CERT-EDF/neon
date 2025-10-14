"""Neon Digests"""

from dataclasses import dataclass

from edf_fusion.concept import Concept


@dataclass(kw_only=True)
class Digests(Concept):
    """Neon Digests"""

    md5: str
    sha1: str
    sha256: str
    sha512: str

    @staticmethod
    def algorithms() -> tuple[str]:
        """Digest algorithms"""
        return ('md5', 'sha1', 'sha256', 'sha512')

    @property
    def primary_digest(self) -> str:
        """Digest used as unique identifier"""
        return self.sha256

    @classmethod
    def from_dict(cls, dct):
        return cls(
            md5=dct['md5'],
            sha1=dct['sha1'],
            sha256=dct['sha256'],
            sha512=dct['sha512'],
        )

    def to_dict(self):
        return {
            'md5': self.md5,
            'sha1': self.sha1,
            'sha256': self.sha256,
            'sha512': self.sha512,
        }

    def update(self, dct):
        """Update case with dct"""
        self.md5 = dct.get('md5', self.md5)
        self.sha1 = dct.get('sha1', self.sha1)
        self.sha256 = dct.get('sha256', self.sha256)
        self.sha512 = dct.get('sha512', self.sha512)
