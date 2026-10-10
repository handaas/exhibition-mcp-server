"""真实 MCP 进程/传输回归测试，上游 HTTP 使用固定模拟数据。"""

import asyncio
from datetime import timedelta
import json
import logging
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client

from test_mcp_server import TEST_ENV, TOOL_NAME


SERVER_PATH = Path(__file__).resolve().parents[1] / "server" / "mcp_server.py"
EXPECTED = {"total": 1, "resultList": [{"name": "模拟参展企业", "nameId": "test-company"}]}
# 执行真实 __main__，只替换上游请求和测试端口，不发送真实 API 请求。
CHILD_CODE = """
import runpy
import sys
from unittest.mock import Mock, patch
from mcp.server.fastmcp import FastMCP

path, transport, port = sys.argv[1:]
original_run = FastMCP.run
def run_mcp(self, transport):
    self.settings.port = int(port)
    return original_run(self, transport=transport)

response = Mock(status_code=200)
response.json.return_value = {"data": {"total": 1, "resultList": [
    {"name": "模拟参展企业", "nameId": "test-company"}
]}}
sys.argv = [path, transport]
with patch("dotenv.load_dotenv"), patch("requests.post", return_value=response), patch.object(FastMCP, "run", run_mcp):
    runpy.run_path(path, run_name="__main__")
"""


class TransportTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # 测试结果不输出临时会话标识或客户端逐请求日志。
        self.logger_levels = {}
        for name in ("mcp.client.streamable_http", "httpx", "asyncio"):
            logger = logging.getLogger(name)
            self.logger_levels[name] = logger.level
            logger.setLevel(logging.WARNING)

    def tearDown(self):
        for name, level in self.logger_levels.items():
            logging.getLogger(name).setLevel(level)

    async def check_session(self, session):
        await session.initialize()
        tools = await session.list_tools()
        self.assertEqual(len(tools.tools), 6)
        self.assertIn(TOOL_NAME, {tool.name for tool in tools.tools})
        result = await session.call_tool(TOOL_NAME, {"matchKeyword": "test-fair"})
        self.assertFalse(result.isError)
        self.assertEqual(json.loads(result.content[0].text), EXPECTED)
        for arguments in ({"matchKeyword": " "}, {"matchKeyword": "test-fair", "pageIndex": 0}, {"matchKeyword": "test-fair", "pageSize": 51}):
            result = await session.call_tool(TOOL_NAME, arguments)
            self.assertIn("error", json.loads(result.content[0].text))
        missing = await session.call_tool(TOOL_NAME, {})
        self.assertTrue(missing.isError)

    async def test_stdio_process(self):
        parameters = StdioServerParameters(
            command=sys.executable,
            args=["-c", CHILD_CODE, str(SERVER_PATH), "stdio", "8000"],
            env=TEST_ENV,
            cwd=str(SERVER_PATH.parents[1]),
        )
        with tempfile.TemporaryFile(mode="w+") as logs:
            async with stdio_client(parameters, errlog=logs) as (read, write):
                async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=10)) as session:
                    await self.check_session(session)

    async def test_streamable_http_process(self):
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        with tempfile.TemporaryFile(mode="w+") as logs:
            process = subprocess.Popen(
                [sys.executable, "-c", CHILD_CODE, str(SERVER_PATH), "streamable-http", str(port)],
                cwd=SERVER_PATH.parents[1],
                env={**os.environ, **TEST_ENV},
                stdout=subprocess.DEVNULL,
                stderr=logs,
            )
            try:
                for _ in range(100):
                    if process.poll() is not None:
                        logs.seek(0)
                        self.fail(f"MCP server exited during startup: {logs.read()}")
                    try:
                        _, write = await asyncio.wait_for(asyncio.open_connection("127.0.0.1", port), timeout=0.2)
                        write.close()
                        await write.wait_closed()
                        break
                    except (OSError, asyncio.TimeoutError):
                        await asyncio.sleep(0.1)
                else:
                    self.fail("MCP HTTP server did not start within 10 seconds")
                async with streamablehttp_client(f"http://127.0.0.1:{port}/mcp", timeout=10, sse_read_timeout=10) as (read, write, _):
                    async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=10)) as session:
                        await self.check_session(session)
            finally:
                process.terminate()
                try:
                    await asyncio.to_thread(process.wait, timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    await asyncio.to_thread(process.wait, timeout=5)


if __name__ == "__main__":
    unittest.main()
