from src.clients.groq_llm_client import GroqLLMClient


def test_extract_nested_decision_object():
    client = GroqLLMClient()
    data = client._extract_json_payload('{"decision":{"action":"restart","confidence":0.82,"reasoning":"ok","safe_to_auto":true}}')
    assert data["action"] == "restart"


def test_normalize_string_boolean_and_confidence():
    client = GroqLLMClient()
    decision = client._normalize_decision({
        "action": "restart",
        "confidence": "0.82",
        "reasoning": "service unstable",
        "safe_to_auto": "true",
    })
    assert decision.action.value == "restart"
    assert decision.confidence == 0.82
    assert decision.safe_to_auto is True
