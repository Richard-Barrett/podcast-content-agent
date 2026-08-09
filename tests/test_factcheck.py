from pathlib import Path

from app.factcheck import LocalKnowledgeBase
from app.models import Claim


def test_kb_verifies_fda_claim():
    kb = LocalKnowledgeBase(Path("kb/facts.json"))
    result = kb.verify(
        Claim("The FDA reviews AI healthcare systems carefully.", "01:15", "Alex")
    )
    assert result.status == "✅ Verified true"
    assert result.confidence >= 0.7


def test_unknown_claim_is_unverifiable():
    kb = LocalKnowledgeBase(Path("kb/facts.json"))
    result = kb.verify(
        Claim("A fictional company doubled sales on Mars.", "00:00", "Guest")
    )
    assert result.status == "❓ Unverifiable"
