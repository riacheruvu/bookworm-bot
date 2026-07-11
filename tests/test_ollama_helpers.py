from bookworm.agents.student import _strip_answer_fencing


def test_strip_answer_prefix():
    assert _strip_answer_fencing("Answer: newton") == "newton"
    assert _strip_answer_fencing("Final answer: 5") == "5"


def test_strip_code_fence():
    assert _strip_answer_fencing("```\nF=ma\n```") == "F=ma"
