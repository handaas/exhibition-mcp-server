"""展会工具的离线回归测试；不读取真实凭据或访问上游 API。"""

import asyncio
import importlib.util
import json
import os
from hashlib import md5
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch

import requests


SERVER_PATH = Path(__file__).resolve().parents[1] / "server" / "mcp_server.py"
TOOL_NAME = "exhibition_bigdata_exhibition_exhibitors"
PRODUCT_ID = "66a2684651cde0f1e3aeff5a"
TEST_ENV = {
    "INTEGRATOR_ID": "test-integrator",
    "SECRET_ID": "test-secret-id",
    "SECRET_KEY": "test-secret-key",
}


def load_server():
    spec = importlib.util.spec_from_file_location("exhibition_test_server", SERVER_PATH)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(os.environ, TEST_ENV), patch("dotenv.load_dotenv"):
        spec.loader.exec_module(module)
    return module


server = load_server()


class ExhibitorsToolTests(unittest.TestCase):
    def call_tool(self, **arguments):
        return getattr(server, TOOL_NAME)(**arguments)

    def test_defaults_match_document(self):
        expected = {"total": 1, "resultList": [{"name": "测试参展企业", "nameId": "test-company"}]}
        with patch.object(server, "call_api", return_value=expected) as api:
            result = self.call_tool(matchKeyword="test-fair")
        api.assert_called_once_with(PRODUCT_ID, {
            "matchKeyword": "test-fair", "pageIndex": 1, "pageSize": 50,
        })
        self.assertIs(result, expected)

    def test_explicit_pagination_and_whitespace(self):
        with patch.object(server, "call_api", return_value={}) as api:
            self.call_tool(matchKeyword="  test-fair  ", pageIndex=3, pageSize=20)
        api.assert_called_once_with(PRODUCT_ID, {
            "matchKeyword": "test-fair", "pageIndex": 3, "pageSize": 20,
        })

    def test_pagination_boundaries(self):
        for page_size in (1, 50):
            with self.subTest(page_size=page_size), patch.object(server, "call_api", return_value={}):
                self.assertEqual(self.call_tool(matchKeyword="test-fair", pageIndex=1, pageSize=page_size), {})

    def test_invalid_id_never_calls_api(self):
        for keyword in ("", " \t\n ", None, 123, True):
            with self.subTest(keyword=keyword), patch.object(server, "call_api") as api:
                result = self.call_tool(matchKeyword=keyword)
                self.assertIn("error", result)
                api.assert_not_called()

    def test_invalid_page_index_never_calls_api(self):
        for page_index in (0, -1, 1.5, "1", None, True):
            with self.subTest(page_index=page_index), patch.object(server, "call_api") as api:
                result = self.call_tool(matchKeyword="test-fair", pageIndex=page_index)
                self.assertIn("error", result)
                api.assert_not_called()

    def test_invalid_page_size_never_calls_api(self):
        for page_size in (0, -1, 51, 1.5, "10", None, True):
            with self.subTest(page_size=page_size), patch.object(server, "call_api") as api:
                result = self.call_tool(matchKeyword="test-fair", pageSize=page_size)
                self.assertIn("error", result)
                api.assert_not_called()

    def test_empty_and_error_results_are_preserved(self):
        for expected in ({"total": 0, "resultList": []}, {"error": "无查询权限"}):
            with self.subTest(expected=expected), patch.object(server, "call_api", return_value=expected):
                self.assertIs(self.call_tool(matchKeyword="test-fair"), expected)

    def test_legacy_error_text_is_normalized_for_new_tool_only(self):
        with patch.object(server, "call_api", return_value="无查询权限"):
            self.assertEqual(self.call_tool(matchKeyword="test-fair"), {"error": "无查询权限"})

    def test_all_tools_and_schema(self):
        tools = asyncio.run(server.mcp.list_tools())
        self.assertEqual({tool.name for tool in tools}, {
            "exhibition_bigdata_fuzzy_search",
            "exhibition_bigdata_exhibition_participation",
            "exhibition_bigdata_exhibition_venue_search",
            "exhibition_bigdata_exhibition_search",
            "exhibition_bigdata_exhibitor_search",
            TOOL_NAME,
        })
        tool = next(tool for tool in tools if tool.name == TOOL_NAME)
        self.assertEqual(tool.inputSchema["required"], ["matchKeyword"])
        properties = tool.inputSchema["properties"]
        self.assertEqual(set(properties), {"matchKeyword", "pageIndex", "pageSize"})
        self.assertEqual(properties["matchKeyword"]["type"], "string")
        self.assertEqual(properties["pageIndex"]["type"], "integer")
        self.assertEqual(properties["pageSize"]["type"], "integer")
        self.assertEqual(properties["pageIndex"]["default"], 1)
        self.assertEqual(properties["pageSize"]["default"], 50)

    def test_mcp_invocation_returns_json(self):
        expected = {"total": 1, "resultList": [{"name": "测试企业", "nameId": "test-company"}]}
        with patch.object(server, "call_api", return_value=expected):
            result = asyncio.run(server.mcp.call_tool(TOOL_NAME, {"matchKeyword": "test-fair"}))
        # SDK 新版还返回 structuredContent；旧版只有文本 content。
        content = result[0] if isinstance(result, tuple) else result
        self.assertEqual(json.loads(content[0].text), expected)

    def test_mcp_upstream_error_keeps_dictionary_contract(self):
        response = Mock(status_code=403)
        with patch.object(server.requests, "post", return_value=response):
            result = asyncio.run(server.mcp.call_tool(TOOL_NAME, {"matchKeyword": "test-fair"}))
        content = result[0] if isinstance(result, tuple) else result
        self.assertIn("error", json.loads(content[0].text))


class ApiTests(unittest.TestCase):
    def test_signed_form_and_timeout(self):
        params = {"matchKeyword": "测试展会", "pageIndex": 1, "pageSize": 50}
        expected = {"total": 0, "resultList": []}
        response = Mock(status_code=200)
        response.json.return_value = {"data": expected}
        with patch.object(server.requests, "post", return_value=response) as post:
            self.assertIs(server.call_api(PRODUCT_ID, params), expected)
        form = {
            "product_id": PRODUCT_ID,
            "secret_id": TEST_ENV["SECRET_ID"],
            "params": json.dumps(params, ensure_ascii=False),
        }
        sign_source = "".join(str(form[key]) for key in sorted(form)) + TEST_ENV["SECRET_KEY"]
        form["signature"] = md5(sign_source.encode("utf-8")).hexdigest()
        post.assert_called_once_with(
            "https://console.handaas.com/api/v1/integrator/call_api/test-integrator",
            data=form, timeout=30,
        )

    def test_missing_credentials_skip_http(self):
        for name in TEST_ENV:
            with self.subTest(name=name), patch.object(server, name, None), patch.object(server.requests, "post") as post:
                self.assertIn("error", server.call_api(PRODUCT_ID, {}))
                post.assert_not_called()

    def test_missing_product_skips_http(self):
        with patch.object(server.requests, "post") as post:
            self.assertIn("error", server.call_api("", {}))
            post.assert_not_called()

    def test_http_error(self):
        for status in (400, 403, 500):
            with self.subTest(status=status), patch.object(server.requests, "post", return_value=Mock(status_code=status)):
                self.assertEqual(server.call_api(PRODUCT_ID, {}), f"接口调用失败，状态码：{status}")

    def test_business_error(self):
        response = Mock(status_code=200)
        response.json.return_value = {"msgCN": "无查询权限"}
        with patch.object(server.requests, "post", return_value=response):
            self.assertEqual(server.call_api(PRODUCT_ID, {}), "无查询权限")

    def test_timeout_and_connection_error_do_not_expose_details(self):
        for error in (requests.Timeout("sensitive request"), requests.ConnectionError("sensitive URL")):
            with self.subTest(error=type(error).__name__), patch.object(server.requests, "post", side_effect=error):
                self.assertEqual(server.call_api(PRODUCT_ID, {}), "查询失败")

    def test_non_json_response(self):
        response = Mock(status_code=200)
        response.json.side_effect = ValueError("invalid JSON")
        with patch.object(server.requests, "post", return_value=response):
            self.assertEqual(server.call_api(PRODUCT_ID, {}), "查询失败")

    def test_unwrapped_response_is_preserved(self):
        response = Mock(status_code=200)
        expected = {"code": "test-status"}
        response.json.return_value = expected
        with patch.object(server.requests, "post", return_value=response):
            self.assertIs(server.call_api(PRODUCT_ID, {}), expected)

    def test_legacy_list_data_is_preserved(self):
        response = Mock(status_code=200)
        expected = [{"name": "测试企业"}]
        response.json.return_value = {"data": expected}
        with patch.object(server.requests, "post", return_value=response):
            self.assertIs(server.call_api(PRODUCT_ID, {}), expected)


class LegacyToolTests(unittest.TestCase):
    CASES: tuple[tuple[str, dict[str, str], str, dict[str, str | int]], ...] = (
        ("exhibition_bigdata_fuzzy_search", {"matchKeyword": "test-company"}, "675cea1f0e009a9ea37edaa1", {"matchKeyword": "test-company", "pageIndex": 1, "pageSize": 50}),
        ("exhibition_bigdata_exhibition_participation", {"matchKeyword": "test-company"}, "66a26918ff3066996ecc6471", {"matchKeyword": "test-company", "pageIndex": 1, "pageSize": 10}),
        ("exhibition_bigdata_exhibition_venue_search", {"pavilionRegion": "北京市"}, "66e2d2ca428a1f4cd69c1083", {"pavilionRegion": "北京", "pageIndex": 1, "pageSize": 10}),
        ("exhibition_bigdata_exhibition_search", {}, "66a0f6ca477cbe5f7605973f", {"pageIndex": 1, "pageSize": 50}),
        ("exhibition_bigdata_exhibitor_search", {"fairFilter": "5场以下"}, "66d5b7e0537c3f61d646c473", {"fairCount": "5场以下", "pageIndex": 1, "pageSize": 10}),
    )

    def test_existing_success_params_and_results_are_unchanged(self):
        expected = {"total": 0, "resultList": []}
        for name, arguments, product_id, params in self.CASES:
            with self.subTest(tool=name), patch.object(server, "call_api", return_value=expected) as api:
                self.assertIs(getattr(server, name)(**arguments), expected)
                api.assert_called_once_with(product_id, params)

    def test_existing_tools_forward_explicit_pagination(self):
        for name, arguments, product_id, params in self.CASES:
            with self.subTest(name=name), patch.object(server, "call_api", return_value={}) as api:
                getattr(server, name)(**{**arguments, "pageIndex": 3, "pageSize": 4})
                api.assert_called_once_with(product_id, {**params, "pageIndex": 3, "pageSize": 4})

    def test_pagination_schema_defaults_match_forwarded_requests(self):
        tools = {tool.name: tool for tool in asyncio.run(server.mcp.list_tools())}
        for name, _, _, params in self.CASES:
            with self.subTest(name=name):
                properties = tools[name].inputSchema["properties"]
                self.assertEqual(properties["pageIndex"]["default"], params["pageIndex"])
                self.assertEqual(properties["pageSize"]["default"], params["pageSize"])

    def test_existing_error_text_is_unchanged_over_mcp(self):
        for name, arguments, _, _ in self.CASES:
            with self.subTest(tool=name), patch.object(server.requests, "post", return_value=Mock(status_code=403)):
                result = asyncio.run(server.mcp.call_tool(name, arguments))
                content = result[0] if isinstance(result, tuple) else result
                self.assertEqual(content[0].text, "接口调用失败，状态码：403")


class StartupTests(unittest.TestCase):
    def test_each_transport_starts_once_without_stdout(self):
        for arguments, transport in (([], "stdio"), (["stdio"], "stdio"), (["sse"], "sse"), (["streamable-http"], "streamable-http")):
            with self.subTest(transport=transport, arguments=arguments):
                with patch.dict(os.environ, TEST_ENV), patch("dotenv.load_dotenv"), patch("sys.argv", [str(SERVER_PATH), *arguments]), patch("mcp.server.fastmcp.FastMCP.run") as run, patch("builtins.print") as output:
                    runpy.run_path(str(SERVER_PATH), run_name="__main__")
                run.assert_called_once_with(transport=transport)
                for call in output.call_args_list:
                    self.assertIs(call.kwargs.get("file"), __import__("sys").stderr)

    def test_unknown_transport_exits_without_running(self):
        with patch.dict(os.environ, TEST_ENV), patch("dotenv.load_dotenv"), patch("sys.argv", [str(SERVER_PATH), "invalid"]), patch("mcp.server.fastmcp.FastMCP.run") as run, patch("builtins.print"):
            with self.assertRaises(SystemExit) as result:
                runpy.run_path(str(SERVER_PATH), run_name="__main__")
        self.assertEqual(result.exception.code, 1)
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
