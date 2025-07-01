"""
Test the VariationSelectionType enum functionality
"""
import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy import Column, Enum as SAEnum

from app.models import VariationSelectionType, VariationGroup, VariationOption

def test_variation_selection_type_values():
    """Test that VariationSelectionType enum has the correct values"""
    assert VariationSelectionType.SINGLE_SELECT == "SINGLE_SELECT"
    assert VariationSelectionType.MULTI_SELECT == "MULTI_SELECT"
    
    # Test string enum behavior
    assert isinstance(VariationSelectionType.SINGLE_SELECT, str)
    assert isinstance(VariationSelectionType.MULTI_SELECT, str)

def test_variation_group_default():
    """Test that VariationGroup has the correct default value"""
    group = VariationGroup(name="Test Group", product_id=1)
    assert group.selection_type == VariationSelectionType.SINGLE_SELECT
    
def test_variation_group_explicit_values():
    """Test that VariationGroup accepts both enum values"""
    group1 = VariationGroup(name="Single Select Group", product_id=1, 
                           selection_type=VariationSelectionType.SINGLE_SELECT)
    group2 = VariationGroup(name="Multi Select Group", product_id=1, 
                           selection_type=VariationSelectionType.MULTI_SELECT)
    
    assert group1.selection_type == VariationSelectionType.SINGLE_SELECT
    assert group2.selection_type == VariationSelectionType.MULTI_SELECT

def test_variation_group_serialization():
    """Test that VariationGroup serializes correctly"""
    group = VariationGroup(name="Test Group", product_id=1)
    serialized = group.model_dump()
    assert serialized["selection_type"] == "SINGLE_SELECT"
