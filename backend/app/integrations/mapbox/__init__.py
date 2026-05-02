"""Mapbox integrations.

Currently exposes only :mod:`geocoder` — server-side forward
geocoding for the GoWork distance-from-ZIP scoring path.
"""
from app.integrations.mapbox.geocoder import geocode_address

__all__ = ["geocode_address"]
