import os
import sys
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from ai.analysis_agent import parse_llm_response  # noqa: E402


class ParseLlmResponseTests(unittest.TestCase):
    def test_dict_response_passthrough(self):
        out = parse_llm_response('{"direction":"买入","confidence":0.8}')
        self.assertEqual(out["direction"], "买入")
        self.assertEqual(out["confidence"], 0.8)

    def test_json_array_returns_safe_dict(self):
        out = parse_llm_response("[]")
        self.assertEqual(out["direction"], "观望")
        self.assertIn("非 JSON 对象", out["reasoning"])

    def test_invalid_json_returns_fallback(self):
        out = parse_llm_response("not json at all")
        self.assertEqual(out["direction"], "观望")
        self.assertIn("解析失败", out["reasoning"])


if __name__ == "__main__":
    unittest.main()
