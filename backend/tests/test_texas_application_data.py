"""Tests for Texas/Fort Worth benefit program application data."""

import pytest


def test_all_seven_programs_have_data():
    """All 7 TX programs must have application data."""
    from app.modules.benefits.texas.application_data import APPLICATION_DATA

    expected = {"SNAP", "TANF", "Medicaid", "CHIP", "Childcare_Subsidy", "Section_8", "CEAP"}
    assert set(APPLICATION_DATA.keys()) == expected


def test_snap_uses_texas_hhsc():
    """SNAP application should point to yourtexasbenefits.com."""
    from app.modules.benefits.texas.application_data import APPLICATION_DATA

    snap = APPLICATION_DATA["SNAP"]
    assert "yourtexasbenefits" in snap.application_url
    assert "Tarrant" in snap.office_name or "HHSC" in snap.office_name


def test_chip_replaces_all_kids():
    """Texas uses CHIP, not ALL Kids."""
    from app.modules.benefits.texas.application_data import APPLICATION_DATA

    assert "CHIP" in APPLICATION_DATA
    assert "ALL_Kids" not in APPLICATION_DATA


def test_ceap_replaces_liheap():
    """Texas uses CEAP, not LIHEAP."""
    from app.modules.benefits.texas.application_data import APPLICATION_DATA

    assert "CEAP" in APPLICATION_DATA
    assert "LIHEAP" not in APPLICATION_DATA


def test_section_8_fort_worth_housing():
    """Section 8 should reference Fort Worth Housing Solutions."""
    from app.modules.benefits.texas.application_data import APPLICATION_DATA

    sec8 = APPLICATION_DATA["Section_8"]
    assert "Fort Worth" in sec8.office_name or "fort worth" in sec8.office_name.lower()


def test_all_entries_have_required_fields():
    """Every program must have URL, office, address, phone, steps, docs."""
    from app.modules.benefits.texas.application_data import APPLICATION_DATA

    for name, info in APPLICATION_DATA.items():
        assert info.application_url, f"{name} missing URL"
        assert info.office_name, f"{name} missing office name"
        assert info.office_address, f"{name} missing address"
        assert info.office_phone, f"{name} missing phone"
        assert len(info.application_steps) >= 2, f"{name} needs >= 2 steps"
        assert len(info.required_documents) >= 2, f"{name} needs >= 2 docs"


def test_get_application_info_returns_data():
    """get_application_info returns data for known program."""
    from app.modules.benefits.texas.application_data import get_application_info

    result = get_application_info("SNAP")
    assert result is not None
    assert result.office_name


def test_get_application_info_returns_none_for_unknown():
    """get_application_info returns None for unknown program."""
    from app.modules.benefits.texas.application_data import get_application_info

    assert get_application_info("FAKE_PROGRAM") is None
