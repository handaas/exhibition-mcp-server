# 展会行业情报

[该MCP服务提供企业关键词模糊搜索、企业参展记录、展会场馆、展会搜索、参展商筛选及展会参展企业等展会大数据查询功能。](https://www.handaas.com/)


## 主要功能

- 🔍 企业关键词模糊搜索
- 📋 企业参展记录查询
- 🏟️ 展会场馆搜索
- 🎪 展会搜索
- 🏢 参展商筛选
- 📊 展会参展企业查询

## 环境要求

- Python 3.10+
- 依赖包：python-dotenv, requests, mcp

## 本地快速启动

### 1. 克隆项目
```bash
git clone https://github.com/handaas/exhibition-mcp-server
cd exhibition-mcp-server
```

### 2. 创建虚拟环境&安装依赖

```bash
python -m venv mcp_env && source mcp_env/bin/activate
pip install -r requirements.txt -c constraints.txt
```

### 3. 环境配置

复制环境变量模板并配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置以下环境变量：

```env
INTEGRATOR_ID=your_integrator_id
SECRET_ID=your_secret_id
SECRET_KEY=your_secret_key
```

### 4. streamable-http启动服务

```bash
python server/mcp_server.py streamable-http
```

服务将在 `http://localhost:8000` 启动。

#### 支持启动方式 stdio 或 sse 或 streamable-http

### 5. Cursor / Cherry Studio MCP配置

```json
{
  "mcpServers": {
    "handaas-exhibition-mcp-server": {
      "type": "streamableHttp",
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

## STDIO版安装部署

### 设置Cursor / Cherry Studio MCP配置

```json
{
  "mcpServers": {
    "exhibition-mcp-server": {
      "command": "uv",
      "args": ["run", "mcp", "run", "{workdir}/server/mcp_server.py"],
      "env": {
        "PATH": "{workdir}/mcp_env/bin:$PATH",
        "PYTHONPATH": "{workdir}/mcp_env",
        "INTEGRATOR_ID": "your_integrator_id",
        "SECRET_ID": "your_secret_id",
        "SECRET_KEY": "your_secret_key"
      }
    }
  }
}
```

## 使用官方Remote服务

### 1. 直接设置Cursor / Cherry Studio MCP配置

```json
{
  "mcpServers": {
    "exhibition-mcp-server":{
      "type": "streamableHttp",
      "url": "https://mcp.handaas.com/exhibition/exhibition_bigdata?token={token}"
      }
  }
}
```

### 注意：integrator_id、secret_id、secret_key及token需要登录 https://www.handaas.com/ 进行注册开通平台获取


## 可用工具

### 1. exhibition_bigdata_fuzzy_search
**功能**: 企业关键词模糊查询

根据提供的企业名称、人名、品牌、产品、岗位等关键词模糊查询相关企业列表。

**参数**:
- `matchKeyword` (必需): 匹配关键词 - 查询各类信息包含匹配关键词的企业
- `pageIndex` (可选): 分页开始位置 - 默认从1开始
- `pageSize` (可选): 每页数量 - 默认50条，最多50条

**返回值**:
- `total`: 总数
- `resultList`: 企业列表
  - `name`: 企业名称
  - `nameId`: 企业ID
  - `address`: 注册地址
  - `foundTime`: 成立时间
  - `enterpriseType`: 企业主体类型
  - `legalRepresentative`: 法定代表人
  - `operStatus`: 经营状态
  - `regCapitalCoinType`: 注册资本币种
  - `regCapitalValue`: 注册资本金额
  - `homepage`: 企业官网
  - `catchReason`: 命中原因

### 2. exhibition_bigdata_exhibition_participation
**功能**: 查询企业参展记录

通过输入企业的标识信息（如企业名称、统一社会信用代码、企业ID或注册号），返回该企业参加展会的详细信息。

**参数**:
- `matchKeyword` (必需): 企业名称/注册号/统一社会信用代码/企业ID
- `pageIndex` (可选): 页码 - 默认从1开始
- `pageSize` (可选): 分页大小 - 一页最多获取50条数据，默认10条
- `keywordType` (可选): 主体类型 - 枚举值：`name`（企业名称）、`nameId`（企业ID）、`regNumber`（注册号）、`socialCreditCode`（统一社会信用代码）

**返回值**:
- `total`: 总数
- `resultList`: 参展记录列表
  - `fairName`: 展会名称
  - `fairBeginTime`: 开展时间
  - `fairEndTime`: 闭展时间
  - `fairPavilion`: 展馆名称
  - `fairDesc`: 展会描述
  - `fairLogo`: 展会Logo
  - `isOpen`: 是否开展

### 3. exhibition_bigdata_exhibition_venue_search
**功能**: 搜索展会场馆

按省市地区和可选关键词搜索展会场馆信息。

**参数**:
- `pavilionRegion` (必需): 场馆所在省市 - 不可多选，例如 `福建省,厦门市`；直辖市可传 `北京`
- `matchKeyword` (可选): 场馆名称或简介关键词
- `pageIndex` (可选): 页码 - 默认从1开始
- `pageSize` (可选): 每页数量 - 默认10条，最多50条

**返回值**:
- `total`: 总数
- `resultList`: 场馆列表
  - `_id`: 场馆ID
  - `pavilionName`: 场馆名称
  - `pavilionAddress`: 场馆地址
  - `pavilionScale`: 展览面积
  - `pavilionHomepage`: 官网链接
  - `pavilionContact`: 联系方式（contactType: 1=固定电话，2=邮箱，5=传真）
  - `fairCount`: 展会数

### 4. exhibition_bigdata_exhibition_search
**功能**: 搜索展会

按展会名称或展品范围关键词搜索展会，也用于取得下一步查询参展企业所需的展会ID。

**参数**:
- `matchKeyword` (可选): 展会名称或展品范围关键词
- `pageIndex` (可选): 页码 - 默认从1开始
- `pageSize` (可选): 每页数量 - 默认50条，最多50条

**返回值**:
- `total`: 总数
- `resultList`: 展会列表
  - `_id`: 展会ID
  - `fairName`: 展会名称
  - `fairBeginTime`: 开展时间
  - `fairEndTime`: 闭展时间
  - `fairPavilion`: 展馆地址
  - `fairDesc`: 展会描述
  - `fairLogo`: 展会Logo

### 5. exhibition_bigdata_exhibitor_search
**功能**: 筛选参展商

按企业关键词、地区、展会行业、参展时间或参展次数筛选参展商。

**参数**:
- `matchKeyword` (可选): 企业名称关键词
- `fairRegion` (可选): 展商所在省市 - 不可多选，例如 `福建省,厦门市`
- `fairIndustries` (可选): 单个展会专题 - 例如 `教育/职业培训/商业`
- `fairBeginTimes` (可选): 参展开始时间 - 格式 `yyyy-mm-dd`
- `fairEndTimes` (可选): 参展结束时间 - 格式 `yyyy-mm-dd`
- `fairFilter` (可选): 参展次数枚举 - `5场以下`、`5-10场`、`10-20场`、`20-50场`、`50-100场`、`100场以上`
- `pageIndex` (可选): 页码 - 默认从1开始
- `pageSize` (可选): 每页数量 - 默认10条，最多50条

**返回值**:
- `total`: 总数
- `resultList`: 参展商列表
  - `name`: 企业名称
  - `nameId`: 企业ID
  - `enterpriseInfo`: 企业信息（含经营状态、规模、地址、行业、注册资本等）
  - `fairCount`: 参展记录数
  - `latestFair`: 最新参展展会信息
  - `latestFairBeginTime`: 最新参展时间

### 6. exhibition_bigdata_exhibition_exhibitors
**功能**: 查询展会参展企业

通过展会ID查询该展会的参展企业列表。需要先调用展会搜索获取展会ID。

**参数**:
- `matchKeyword` (必需): 展会ID - 不能为空白字符串
- `pageIndex` (可选): 页码 - 默认从1开始
- `pageSize` (可选): 每页数量 - 范围1~50，默认50

**返回值**:
- `total`: 参展企业总数
- `resultList`: 参展企业列表
  - `name`: 企业名称
  - `nameId`: 企业ID

## 使用注意事项

1. **企业全称要求**: 在调用需要企业全称的接口时，需要先调用关键词模糊查询企业接口进行补全后，再调用该接口。
2. **展会ID获取**: 查询展会参展企业需要先通过展会搜索获取展会`_id`，不能直接传展会名称。
3. **分页参数**: 各分页工具均支持`pageSize`，并将其传递给查询接口。企业关键词模糊查询、展会搜索和参展企业查询默认每页50条；参展记录、场馆搜索和参展商搜索默认每页10条，一页最多50条。连续翻页时请保持每页数量一致。
4. **错误处理**: 所有接口都包含错误处理，查询失败时会返回相应的错误信息；调用HandaaS上游接口的HTTP请求超时时间为30秒。

## 使用提问示例

### exhibition_bigdata_fuzzy_search (企业关键词模糊搜索)
1. 帮我查找包含"华为"关键词的参展企业信息
2. 搜索与"医疗器械"相关的企业列表
3. 查询名称中包含"广交会"的参展公司

### exhibition_bigdata_exhibition_participation (企业参展记录查询)
1. 华为参加过哪些展会？
2. 查询腾讯科技有限公司的参展历史
3. 字节跳动参加过什么展会？

### exhibition_bigdata_exhibition_venue_search (展会场馆搜索)
1. 上海有哪些展会场馆？
2. 查询广州的展会场馆信息
3. 北京国家会议中心附近有哪些场馆？

### exhibition_bigdata_exhibition_search (展会搜索)
1. 搜索"进博会"相关的展会
2. 有哪些关于人工智能的展会？
3. 查询2025年上海的展会

### exhibition_bigdata_exhibitor_search (参展商筛选)
1. 深圳有哪些教育行业的参展商？
2. 查询2025年参展次数在10场以上的企业
3. 筛选广州地区医疗器械行业的参展商

### exhibition_bigdata_exhibition_exhibitors (展会参展企业查询)
1. 进博会有哪些企业参展？
2. 查询CES 2025的参展企业名单
3. 广交会的参展企业有哪些？

## 测试验证

```bash
python -m py_compile server/mcp_server.py
python -m unittest discover -s tests -v
```

测试覆盖参数校验、分页边界、签名、上游异常和MCP工具注册；测试中的上游HTTP请求均使用模拟数据，不读取真实凭证。
