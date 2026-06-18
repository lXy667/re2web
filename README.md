# Resume2Web 📄

PDF 简历解析与在线简历生成器。上传 PDF 简历，自动提取姓名、电话、邮箱、教育经历、技能、工作/项目经历等结构化信息，并生成带样式的在线简历页面。

## 功能

| 字段 | 支持格式 |
|------|---------|
| 姓名 | 中文 2-4 字 / 英文姓名 |
| 电话 | 大陆手机 / `(xxx) xxx-xxxx` / `+86` 国际格式 / 固话 |
| 邮箱 | 标准 email 格式 |
| 教育经历 | 多条目、顺序无关（先学校后时间或先时间后学校均可）、支持 `2022.09-今` |
| 技能 | 从"专业技能/技术技能/技能证书/语言能力"等节提取 |
| 工作/实习/项目 | 论文发表、科研项目、竞赛、课外实践等节 |

## 快速开始

```bash
git clone https://github.com/lXy667/re2web.git
cd re2web

# 创建虚拟环境（可选）
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

浏览器打开 `http://localhost:8501`，上传 PDF 简历即可。

## 项目结构

```
resume2web/
├── app.py              # Streamlit 入口（含测试模式开关）
├── parser.py           # PDF 文本提取（PyMuPDF）
├── extractor.py        # 结构化信息提取（姓名/电话/邮箱/教育/技能/经历）
├── renderer.py         # HTML 简历渲染
├── test/               # 测试用例 PDF
├── uploads/            # 上传文件暂存
├── resume.json         # 提取结果的 JSON 缓存
├── requirements.txt    # Python 依赖
└── README.md
```

## 提取器说明

`extractor.py` 采用基于关键词和正则的规则引擎，不需要训练模型：

- **姓名**：前缀检测 → 行首 2-4 汉字 → 英文首字母大写词 → 兜底纯汉字
- **电话**：多格式正则匹配，自动清理空格/括号
- **教育**：定位节标题（教育经历/教育背景）→ 多格式日期匹配（含"今"）→ 学校/学历/专业字段提取 → 顺序无关配对
- **技能**：定位节标题（专业技能/技术技能/技能证书等）→ 逐行采集至下一节
- **经历**：定位节标题（工作经历/实习经历/项目经历/论文发表/科研项目等）→ 日期行分组 → 提取标题/时间/描述

## 测试模式

默认开启，自动加载 `test/` 下的所有 PDF：

```python
# app.py 第 7 行
TEST_MODE = True   # 测试模式
TEST_MODE = False  # 线上模式（去掉翻页器和自动加载）
```

测试模式会用翻页器浏览所有测试用例的提取结果，方便调试。


