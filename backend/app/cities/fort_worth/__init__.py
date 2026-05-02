"""Fort Worth, TX city-specific module.

Holds Fort-Worth-only literals (eligibility rules, fallback strings)
that must NEVER be invoked when CITY=montgomery.  Importers must gate
on ``city.state == "TX"`` before reaching into this module.
"""
