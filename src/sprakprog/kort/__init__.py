"""Kortlagret — inlärardatabasen och kortbeståndet.

Skilt från språkdatabasen på fil, av skälet i GENERATOR.md: en ombyggd
sprak.db ska kunna mötas av en orörd inlärardatabas.
"""

from .befolka import befolka, sammanfattning
from .db import anslut_kort, skapa_kortdatabas

__all__ = ["anslut_kort", "befolka", "sammanfattning", "skapa_kortdatabas"]
