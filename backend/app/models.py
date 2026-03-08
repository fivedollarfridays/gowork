"""SQLAlchemy ORM models for barrier graph tables."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship


class Barrier:
    """Barrier node model - represents a specific life challenge."""
    
    __tablename__ = "barriers"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    description = Column(Text)
    playbook = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    source_relationships = relationship(
        "BarrierRelationship",
        foreign_keys="BarrierRelationship.source_barrier_id",
        back_populates="source_barrier"
    )
    target_relationships = relationship(
        "BarrierRelationship", 
        foreign_keys="BarrierRelationship.target_barrier_id",
        back_populates="target_barrier"
    )
    barrier_resources = relationship("BarrierResource", back_populates="barrier")


class BarrierRelationship:
    """Relationship between two barriers (directed graph edge)."""
    
    __tablename__ = "barrier_relationships"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_barrier_id = Column(String, ForeignKey("barriers.id"), nullable=False)
    target_barrier_id = Column(String, ForeignKey("barriers.id"), nullable=False)
    relationship_type = Column(String, nullable=False)
    weight = Column(Float, default=1.0)
    
    # Relationships
    source_barrier = relationship("Barrier", foreign_keys=[source_barrier_id], back_populates="source_relationships")
    target_barrier = relationship("Barrier", foreign_keys=[target_barrier_id], back_populates="target_relationships")


class BarrierResource:
    """Link between a barrier and a resource that can help address it."""
    
    __tablename__ = "barrier_resources"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    barrier_id = Column(String, ForeignKey("barriers.id"), nullable=False)
    resource_id = Column(Integer, nullable=False)
    impact_strength = Column(Float, nullable=False)
    notes = Column(Text)
    
    # Relationships
    barrier = relationship("Barrier", back_populates="barrier_resources")
