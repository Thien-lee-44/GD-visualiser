"""
Defines mathematical and geometric entities for the 3D scene.
Exposes high-level scene constructs and base 3D models for the rendering pipeline.
"""
from .math_surface import MathSurface
from .optimizer_entity import OptimizerEntity
from .models import LineMesh, CylinderMesh, ConeMesh, WireframeSphere, TexturedMeshObj, FootballMesh

__all__ = [
    "MathSurface", 
    "OptimizerEntity", 
    "LineMesh", 
    "CylinderMesh", 
    "ConeMesh", 
    "WireframeSphere", 
    "TexturedMeshObj",
    "FootballMesh"
]