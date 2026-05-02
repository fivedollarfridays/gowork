"""Montgomery, AL city-specific module.

Holds Montgomery-only literals (career center names, phones, addresses)
that must NEVER be invoked when CITY=fort-worth.  Importers must gate on
``city.state == "AL"`` before reaching into this module.
"""
