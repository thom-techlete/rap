# Seizoenen

Een seizoen loopt van 1 augustus tot en met 31 juli. De ondergrens is
inclusief en de bovengrens exclusief: `2025-08-01 00:00:00` tot
`2026-08-01 00:00:00`, gevolgd door `2026-08-01 00:00:00` tot
`2027-08-01 00:00:00`.

De eerste migratie maakt `2024–2025`, `2025–2026` en `2026–2027` aan. Het
seizoen `2026–2027` wordt actief. Bestaande evenementen worden op hun datum
ingedeeld. Evenementen uit mei–juli 2025 horen daarom bij het inactieve seizoen
`2024–2025`; ze worden niet stilzwijgend naar `2025–2026` verplaatst.

Alle bestaande evenementen, aanwezigheidsregels en wedstrijdstatistieken
blijven behouden. Aanwezigheid en statistieken krijgen hun seizoenscontext via
het evenement.

## Volgende rollover

Maak vóór 1 augustus het volgende seizoen aan met een aaneengesloten periode
van één jaar. Controleer de evenementenverdeling. Zet in één database-transactie
eerst het huidige seizoen uit en daarna het nieuwe seizoen aan (of gebruik een
beheeractie die dit atomair doet); zo is er nooit een tweede actief seizoen. Er mag
maar één actief seizoen zijn. Via de keuzelijst **Seizoen** kunnen beheerders
en spelers een gearchiveerd seizoen bekijken.
