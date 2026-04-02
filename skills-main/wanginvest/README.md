# wanginvest价值选股打分助手

根据 MR Dang 投资体系，对 A 股上市公司进行**标准化风险筛查 + 多维度打分 + 投资评级**的 Claude Code 技能。

## 功能特点

* 🔄 **自动化数据获取**: 通过 Tushare API 自动获取财务、估值、分红数据
* 🔍 **智能信息搜索**: 使用 Tavily API 搜索公司业务、行业地位、风险信息
* 📊 **标准化评分体系**: 8维度打分，总分100分，自动评级
* 📝 **报告自动保存**: 生成的分析报告自动保存到当前目录

## 核心规则

1. **一票否决**: 股息率＜2% 直接淘汰
2. **及格线**: ≥60 分可进入深度研究
3. **核心逻辑**: 以排除风险为主，不追求完美公司
4. **适用行业**: 银行、资源、化工/制造、公用事业、其他传统行业
5. **风险提示：**一些常见的价值投资财务指标的风险提示

## 安装

### 1\. 复制技能到 Claude Code 技能目录

```bash
cp -r mrdang \~/.claude/skills/
```

### 2\. 安装 Python 依赖

```bash
cd mrdang/scripts
pip install tushare requests pandas
```

或使用 uv:

```bash
uv pip install tushare requests pandas
```

### 3\. 配置环境变量

```bash
# Tushare API Token (必需)
export TUSHARE\_TOKEN="your\_tushare\_token"

# Tavily API Key (必需)
export TAVILY\_API\_KEY="your\_tavily\_api\_key"
```

获取 API 密钥:

* Tushare: https://tushare.pro/register
* Tavily: https://tavily.com/

## 使用方法

### 触发方式

在 Claude Code 中输入以下命令：

```
MR Dang 选股 招商银行
MR Dang 打分 中国神华
帮我用 MR Dang 体系分析 600028
```

### 直接调用 Python 函数

```python
from scripts.data import search\_stock, get\_all\_data
from scripts.search import search\_company\_info
from scripts.report import save\_report

# 搜索股票
result = search\_stock("招商银行")
ts\_code = result.iloc\[0]\["ts\_code"]

# 获取所有数据
data = get\_all\_data(ts\_code)

# 搜索公司信息
search\_results = search\_company\_info("招商银行", "银行")

# 保存报告
filepath = save\_report(
    stock\_name="招商银行",
    ts\_code=ts\_code,
    industry="银行",
    data=data,
    search\_results=search\_results,
    scores={...},
    screening={...},
    checklist={...},
    conclusion="综合结论",
)
```

## 评分体系

### 8维度打分（总分100）

|维度|满分|说明|
|-|-|-|
|生产资料属性|20|资源/银行/重资产得分高|
|股息率|20|≥5%满分，＜2%淘汰|
|估值|15|PE≤10满分|
|资源/成本优势|15|仅资源/制造启用|
|行业竞争位置|10|龙头得分高|
|地域因素|10|仅银行/区域股启用|
|流动性与财务安全|5|市值/负债/现金流|
|逻辑清晰度|5|业务复杂度|

### 评级标准

|分数|评级|建议|
|-|-|-|
|80-100|⭐⭐⭐⭐⭐|重点关注、可建仓|
|60-79|⭐⭐⭐⭐|可分批买入|
|40-59|⭐⭐⭐|谨慎观察|
|20-39|⭐⭐|建议回避|
|0-19|⭐|直接排除|

## 文件结构

```
mrdang/
├── SKILL.md          # Claude Code 技能定义
├── README.md         # 本文档
└── scripts/          # Python 脚本
    ├── \_\_init\_\_.py   # 包导出
    ├── data.py       # Tushare 数据获取
    ├── search.py     # Tavily 网络搜索
    └── report.py     # 报告生成与保存
```

## API 函数

### data.py - 数据获取

|函数|说明|
|-|-|
|`search\_stock(keyword)`|搜索股票代码|
|`get\_stock\_basic(ts\_code)`|获取股票基础信息|
|`get\_daily\_basic(ts\_code)`|获取 PE/PB/市值等|
|`get\_financial\_indicator(ts\_code)`|获取财务指标|
|`get\_dividend\_info(ts\_code)`|获取分红信息|
|`get\_price\_position(ts\_code)`|计算股价位置|
|`get\_all\_data(ts\_code)`|获取所有数据|

### search.py - 网络搜索

|函数|说明|
|-|-|
|`tavily\_search(query)`|Tavily API 搜索|
|`search\_company\_info(name, industry)`|搜索公司全面信息|
|`extract\_search\_content(results)`|提取搜索摘要|

### report.py - 报告生成

|函数|说明|
|-|-|
|`generate\_report(...)`|生成报告内容|
|`save\_report(...)`|保存报告到磁盘|
|`get\_reports\_dir()`|获取报告目录|

## 输出示例

报告自动保存至当前目录 `./招商银行\_600036\_20260328.md`

```markdown
# MR Dang 选股打分报告

【标的】招商银行（600036.SH）
【行业归类】银行
【分析日期】2026-03-28

## 一、基础筛查结果
✅ 全部通过

## 二、核心数据概览
- PE(TTM): 6.62
- PB: 0.93
- 股息率: 5.07%
- ROE: 12.02%

## 三、维度打分明细
\*\*总分：82 / 100\*\*
\*\*评级：⭐⭐⭐⭐⭐ 优秀\*\*

## 四、操作建议
重点关注，可考虑建仓
```

## 风险提示

本工具基于公开数据分析，不构成投资建议。投资有风险，入市需谨慎。

## 更新日志

### v1.0.0 (2026-03-28)

* 初始版本
* 支持 Tushare 数据获取
* 支持 Tavily 网络搜索
* 支持 8 维度评分
* 支持报告自动保存

## 许可证

MIT License

