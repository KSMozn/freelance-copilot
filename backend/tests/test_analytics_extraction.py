from app.application.services.analytics_extraction import (
    budget_bucket,
    extract_domain,
    extract_technologies,
    quality_bucket_label,
    score_bucket_label,
    snapshot_job_budget_text,
    snapshot_opportunity_score,
    snapshot_quality_score,
)


def test_score_bucket_labels() -> None:
    assert score_bucket_label(None) is None
    assert score_bucket_label(0) == "0-49"
    assert score_bucket_label(49) == "0-49"
    assert score_bucket_label(50) == "50-64"
    assert score_bucket_label(64) == "50-64"
    assert score_bucket_label(65) == "65-79"
    assert score_bucket_label(79) == "65-79"
    assert score_bucket_label(80) == "80-100"
    assert score_bucket_label(100) == "80-100"
    # outside the valid range
    assert score_bucket_label(120) is None


def test_quality_bucket_labels() -> None:
    assert quality_bucket_label(None) is None
    assert quality_bucket_label(0) == "0-59"
    assert quality_bucket_label(59) == "0-59"
    assert quality_bucket_label(60) == "60-74"
    assert quality_bucket_label(74) == "60-74"
    assert quality_bucket_label(75) == "75-84"
    assert quality_bucket_label(84) == "75-84"
    assert quality_bucket_label(85) == "85-100"
    assert quality_bucket_label(100) == "85-100"


def test_budget_bucket() -> None:
    assert budget_bucket(None) == "unknown"
    assert budget_bucket("") == "unknown"
    assert budget_bucket("fixed USD 75-150") == "under_250"
    assert budget_bucket("USD 250") == "250_500"
    assert budget_bucket("USD 800") == "500_1000"
    assert budget_bucket("fixed USD 2500-3500") == "3000_plus"
    assert budget_bucket("fixed USD 1500") == "1000_3000"


def _snap_with_body(body: str, title: str = "Some job") -> dict:
    return {
        "job": {"title": title, "budget": None},
        "proposal": {"body": body, "title": "Re: …", "short_body": ""},
        "opportunity_score": None,
        "resume": None,
        "portfolio": [],
    }


def test_extract_technologies_from_body() -> None:
    snap = _snap_with_body(
        "Need Python + FastAPI + PostgreSQL with Docker, plus a small RAG layer over OpenAI."
    )
    techs = extract_technologies(snap)
    assert "Python" in techs
    assert "FastAPI" in techs
    assert "PostgreSQL" in techs
    assert "Docker" in techs
    assert "RAG" in techs
    assert "OpenAI" in techs


def test_extract_technologies_respects_word_boundaries() -> None:
    # ".NET" must not match anywhere inside "internet" / "ASPNET"
    snap = _snap_with_body("The internet is fine. We use ASPNET conventions.")
    techs = extract_technologies(snap)
    assert ".NET" not in techs

    # "API" must not match "rapid" or "rapidly"
    snap = _snap_with_body("We move rapidly and ship things.")
    techs = extract_technologies(snap)
    assert "API" not in techs

    # But "C++" should match when surrounded by non-alphanumerics.
    snap = _snap_with_body("We need C++ skills for the inner loop.")
    assert "C++" in extract_technologies(snap)


def test_extract_technologies_prefers_structured_when_present() -> None:
    snap = {
        "job": {"title": "Generic title", "technologies": ["Stripe", "FastAPI"]},
        "proposal": {"body": "nothing identifiable here"},
    }
    techs = extract_technologies(snap)
    assert "Stripe" in techs
    assert "FastAPI" in techs


def test_extract_domain_from_structured_first() -> None:
    snap = {
        "job": {"title": "x", "business_domain": "FinTech"},
        "proposal": {"body": "mentions AI SaaS"},
    }
    assert extract_domain(snap) == "FinTech"


def test_extract_domain_fallback_to_body() -> None:
    snap = _snap_with_body(
        "We are an AI SaaS company building enterprise tooling.",
        title="Some opportunity",
    )
    assert extract_domain(snap) == "AI SaaS"


def test_extract_domain_returns_none_when_nothing_matches() -> None:
    snap = _snap_with_body("nothing relevant", title="empty")
    assert extract_domain(snap) is None


def test_snapshot_readers() -> None:
    snap = {
        "job": {"budget": "USD 3000-5000"},
        "proposal": {"quality_score": 82},
        "opportunity_score": {"score": 81},
    }
    assert snapshot_job_budget_text(snap) == "USD 3000-5000"
    assert snapshot_quality_score(snap) == 82
    assert snapshot_opportunity_score(snap) == 81

    assert snapshot_job_budget_text(None) is None
    assert snapshot_quality_score({}) is None
