# 展会大数据 MCP 服务

[HandaaS 展会大数据 MCP 服务](https://www.handaas.com/)提供企业、参展记录、场馆、展会及参展商查询。目前本地源码提供 6 个工具。

## 查询能力

| 查询目标 | 工具 | 关键输入 |
| --- | --- | --- |
| 用模糊关键词定位企业 | `exhibition_bigdata_fuzzy_search` | 企业、人名、品牌、产品、岗位等关键词 |
| 查询某家企业参加过的展会 | `exhibition_bigdata_exhibition_participation` | 企业名称、企业 ID、注册号或统一社会信用代码 |
| 搜索展会场馆 | `exhibition_bigdata_exhibition_venue_search` | 省市地区，可附加场馆关键词 |
| 搜索展会并取得展会 ID | `exhibition_bigdata_exhibition_search` | 展会名称或展品范围关键词 |
| 按地区、行业、时间等条件筛选参展商 | `exhibition_bigdata_exhibitor_search` | 一个或多个筛选条件 |
| 查询指定展会的参展企业 | `exhibition_bigdata_exhibition_exhibitors` | **展会 ID** |

> 三类企业/展会关系查询不要混用：`exhibition_participation` 是“企业 → 参展历史”，`exhibitor_search` 是“筛选条件 → 参展商”，`exhibition_exhibitors` 是“展会 ID → 参展企业”。

## 环境要求

- Python 3.10+
- HandaaS 平台提供的 `INTEGRATOR_ID`、`SECRET_ID`、`SECRET_KEY`
- Python 依赖以 [`requirements.txt`](requirements.txt) 为准，使用 [`constraints.txt`](constraints.txt) 中已验证的 SDK 兼容组合

## 本地安装

```bash
git clone https://github.com/handaas/exhibition-mcp-server
cd exhibition-mcp-server
python -m venv mcp_env
source mcp_env/bin/activate
python -m pip install -r requirements.txt -c constraints.txt
cp .env.example .env
```

编辑 `.env`：

```env
INTEGRATOR_ID=your_integrator_id
SECRET_ID=your_secret_id
SECRET_KEY=your_secret_key
```

请勿提交包含真实凭证的 `.env`。

已验证的 SDK 组合为 MCP `1.19.0`、Pydantic `2.12.3`、pydantic-settings `2.11.0`。不要单独升级 Pydantic：测试发现 MCP `1.19.0` 与 Pydantic `2.14.0` 组合会在导入时失败。已有环境也可用上面的安装命令对齐版本。

## 启动与客户端配置

### Streamable HTTP

在服务目录运行：

```bash
source mcp_env/bin/activate
python server/mcp_server.py streamable-http
```

也可以使用启动脚本：

```bash
./start_mcp_server.sh streamable-http
```

脚本会从自身所在目录定位 `mcp_env/bin/python`，使用该解释器按 `requirements.txt` 和 `constraints.txt` 检查依赖，然后启动指定传输方式。省略参数时默认为 STDIO：

```bash
./start_mcp_server.sh
```

默认 MCP 地址为 `http://127.0.0.1:8000/mcp`。客户端配置字段会因客户端而异；以下示例适用于接受 `streamableHttp` 类型的客户端：

```json
{
  "mcpServers": {
    "exhibition-mcp-server": {
      "type": "streamableHttp",
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

### STDIO

STDIO 客户端应直接使用虚拟环境中的 Python 和脚本的绝对路径，不要依赖客户端展开 `$PATH`：

```json
{
  "mcpServers": {
    "exhibition-mcp-server": {
      "command": "/absolute/path/to/exhibition-mcp-server/mcp_env/bin/python",
      "args": [
        "/absolute/path/to/exhibition-mcp-server/server/mcp_server.py",
        "stdio"
      ]
    }
  }
}
```

使用前，将 `/absolute/path/to/exhibition-mcp-server` 替换为本机实际的服务绝对路径。

STDIO 启动提示写入标准错误流，不会混入标准输出中的 MCP 协议消息。

### 官方 Remote 服务

已有官方 Remote 服务可按原方式配置：

```json
{
  "mcpServers": {
    "exhibition-mcp-server": {
      "type": "streamableHttp",
      "url": "https://mcp.handaas.com/exhibition/exhibition_bigdata?token={token}"
    }
  }
}
```

`integrator_id`、`secret_id`、`secret_key` 和 `token` 需要登录 [HandaaS](https://www.handaas.com/) 注册开通后获取。本次新增工具仅表示本地源码已更新；官方 Remote 服务是否包含该工具取决于其独立发布进度。

## 请求超时与错误返回

- 调用 HandaaS 上游接口的 HTTP 请求超时时间为 30 秒。
- 新增参展企业工具遇到本地参数校验失败、缺少凭证、上游业务错误文本、HTTP 状态异常或请求异常时，返回 `{"error": "错误说明"}`。
- 为保持兼容，原有 5 个工具的成功数据及错误格式均不变；部分旧工具错误仍为文本，不要把错误文本当作查询结果。
- 错误详情用于定位配置、输入或上游服务问题；它不代表远程服务或真实业务联调已经通过。

若返回“对接器已停用”，需要平台管理员启用对应对接器，或在本服务 `.env` 中配置已启用的对接器；更新凭证后重启服务。不要在日志、聊天或版本库中公开密钥。新增工具返回 `error` 时应先处理错误，不应继续按 `total` 翻页。

## 可用工具

### 1. `exhibition_bigdata_fuzzy_search`

按企业名称、人名、品牌、产品、岗位等关键词模糊搜索企业。

| 参数 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `matchKeyword` | 是 | — | 匹配关键词 |
| `pageIndex` | 否 | `1` | 页码，从 1 开始 |

返回 `total` 和企业列表；企业信息可包含 `name`、`nameId`、注册地址、成立时间、经营状态、法定代表人及命中原因等字段。该工具不接受 `pageSize`。

### 2. `exhibition_bigdata_exhibition_participation`

查询指定企业的参展历史。

| 参数 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `matchKeyword` | 是 | — | 企业名称、企业 ID、注册号或统一社会信用代码 |
| `pageIndex` | 否 | `1` | 页码，从 1 开始 |
| `pageSize` | 否 | `10` | 每页数量，最多 50 条 |
| `keywordType` | 否 | — | `name`、`nameId`、`regNumber` 或 `socialCreditCode` |

返回 `total` 和参展记录。记录可包含 `fairName`、`fairBeginTime`、`fairEndTime`、`fairPavilion`、`fairDesc`、`fairLogo`、`isOpen` 等字段。

若只有企业简称，可先调用 `exhibition_bigdata_fuzzy_search` 取得企业全称或 `nameId`。

### 3. `exhibition_bigdata_exhibition_venue_search`

按地区和可选关键词搜索展会场馆。

| 参数 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `pavilionRegion` | 是 | — | 场馆所在省市，不可多选，例如 `福建省,厦门市`；直辖市可传 `北京` |
| `matchKeyword` | 否 | — | 场馆名称或简介关键词 |
| `pageIndex` | 否 | `1` | 页码，从 1 开始 |

返回 `total` 和场馆列表。场馆信息可包含 `_id`、`pavilionName`、`pavilionAddress`、`pavilionScale`、`pavilionHomepage`、`pavilionContact`、`fairCount` 等字段。联系方式类型：`1` 为固定电话，`2` 为邮箱，`5` 为传真。该工具不接受 `pageSize`。

### 4. `exhibition_bigdata_exhibition_search`

按展会名称或展品范围关键词搜索展会，也用于取得下一步查询参展企业所需的展会 `_id`。

| 参数 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `matchKeyword` | 否 | — | 展会名称或展品范围关键词 |
| `pageIndex` | 否 | `1` | 页码，从 1 开始 |

返回 `total` 和展会列表。展会信息可包含 `_id`、`fairName`、`fairBeginTime`、`fairEndTime`、`fairPavilion`、`fairDesc`、`fairLogo` 等字段。该工具不接受 `pageSize`。

### 5. `exhibition_bigdata_exhibitor_search`

按企业关键词、地区、展会行业、参展时间或参展次数筛选参展商。

| 参数 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `fairRegion` | 否 | — | 展商所在省市，不可多选，例如 `福建省,厦门市` |
| `matchKeyword` | 否 | — | 企业名称关键词 |
| `fairIndustries` | 否 | — | 单个展会专题，例如 `教育/职业培训/商业` |
| `fairBeginTimes` | 否 | — | 参展开始时间，格式 `yyyy-mm-dd` |
| `fairEndTimes` | 否 | — | 参展结束时间，格式 `yyyy-mm-dd` |
| `pageIndex` | 否 | `1` | 页码，从 1 开始 |
| `fairFilter` | 否 | — | 参展次数枚举，见下方 |

`fairFilter` 只能取以下一个值：

- `5场以下`
- `5-10场`
- `10-20场`
- `20-50场`
- `50-100场`
- `100场以上`

返回 `total` 和参展商信息。结果可包含 `name`、`nameId`、企业状态、规模、地址、行业、`fairCount`、`latestFair`、`latestFairBeginTime` 等字段。该工具不接受 `pageSize`。

### 6. `exhibition_bigdata_exhibition_exhibitors`

通过**展会 ID**查询该展会的参展企业。`matchKeyword` 必须传展会 ID，不能传展会名称。

| 参数 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `matchKeyword` | 是 | — | 展会 ID；不能为空白字符串 |
| `pageIndex` | 否 | `1` | 页码，从 1 开始 |
| `pageSize` | 否 | `50` | 每页数量，范围 `1`～`50` |

工具直接返回上游 `data` 字典的内容，不包含外层的 `code`、`msgCN`、`reqInfo` 和 `data` 包装。主要字段为：

- `total` (`int`)：参展企业总数
- `resultList` (`list[dict]`)：参展企业列表
  - `name` (`string`)：企业名称
  - `nameId` (`string`)：企业 ID

本地工具会拒绝空白展会 ID、`pageIndex < 1`，以及不在 `1`～`50` 范围内的 `pageSize`。

## 按展会名称查询参展企业

第一步，搜索展会。工具调用参数：

```json
{
  "matchKeyword": "中国国际进口博览会",
  "pageIndex": 1
}
```

从 `exhibition_bigdata_exhibition_search` 返回的展会列表中确认目标展会，并读取其 `_id`。不要直接把展会名称传给下一步。

第二步，将该 `_id` 作为 `matchKeyword` 调用 `exhibition_bigdata_exhibition_exhibitors`：

```json
{
  "matchKeyword": "<上一步返回的展会_id>",
  "pageIndex": 1,
  "pageSize": 50
}
```

如 `total` 大于当前已取得的数量，依次请求 `pageIndex` 为 `2`、`3`……的页面。每页最多 50 条；同一轮翻页请固定 `pageSize`，推荐保持默认的 `50`。当累计数量达到 `total`，或 `resultList` 为空时停止翻页。

真实联调发现，不同 `pageSize` 请求中返回企业的位置可能有差异，不应把不同页大小的结果按相同列表位置拼接或比较。若需要完整名单，请按 `nameId` 检查重复，并核对去重后的数量是否达到 `total`。本工具每次只查询一页，不会自动抓取全部企业。

## 本地验证

在 `exhibition-mcp-server` 目录执行：

```bash
source mcp_env/bin/activate
python -m py_compile server/mcp_server.py
python -m unittest discover -s tests -v
```

测试覆盖参数、分页边界、签名、上游异常和 MCP 工具注册；同时会启动真实 STDIO/HTTP MCP 子进程并检查调用结果。测试中的上游 HTTP 请求均使用模拟数据，不读取真实凭证或查询真实业务数据。

`unittest` 属于 Python 标准库，不需要新增测试依赖。需要联调 HTTP MCP 服务时，再启动：

```bash
python server/mcp_server.py streamable-http
```

联调调用真实 HandaaS 接口需要 `.env` 中存在有效凭证。
