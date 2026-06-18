import re
from typing import List, Dict


# ============================================================
# 常量定义
# ============================================================

EDU_HEADERS = [
    "教育经历", "教育背景", "教育",
    "Education", "EDUCATION",
]

SKILL_HEADERS = [
    "专业技能", "专业能力", "技术能力", "技术技能", "编程技能",
    "办公能力", "外语能力", "语言能力", "技能证书",
    "Technical Skills", "Skills", "TECHNICAL SKILLS", "SKILLS",
    "个人技能",
]

EXP_HEADERS = [
    "工作经历", "实习经历", "项目经历", "工作经验", "项目经验",
    "校内实践", "社会实践", "社会活动",
    "论文发表", "论文在投", "英方学位毕业课题", "毕业课题",
    "科研项目",
    "Work Experience", "EXPERIENCE", "Experience",
    "Internship", "INTERNSHIP",
    "Project", "PROJECT",
]

STOP_KEYWORDS = [
    "项目经历", "实习经历", "工作经历", "校园经历",
    "专业技能", "专业能力", "技术能力", "技术技能", "编程技能",
    "办公能力", "外语能力", "语言能力", "技能证书",
    "荣誉奖项", "获奖经历", "证书",
    "自我评价", "个人评价",
    "项目经验", "工作经验",
    "校内实践", "社会实践", "社会活动",
    "个人技能",
    "论文发表", "论文在投", "英方学位", "毕业课题",
    "科研项目",
    "Project", "Projects", "EXPERIENCE", "Experience",
    "Internship", "SKILLS", "Skills",
    "Self-evaluation", "Honors", "Awards", "Certificates",
]

SCHOOL_KEYWORDS = [
    "大学", "学院", "University", "College", "Institute", "School",
    "Academy", "研究生院",
]

DEGREE_KEYWORDS = [
    "本科", "硕士", "博士", "研究生", "学士",
    "本科在读", "硕士在读", "博士在读",
    "Bachelor", "Master", "PhD", "Ph.D", "Doctor",
    "Bachelor of", "Master of", "Doctor of",
    "B.S.", "B.E.", "M.S.", "M.E.", "Ph.D.",
    "学士学位", "硕士学位", "博士学位",
    "大专", "专科", "高中",
]


# ============================================================
# 辅助函数
# ============================================================

def _normalize_pdf_text(text: str) -> str:
    text = re.sub(r'([\u4e00-\u9fa5])\n([\u4e00-\u9fa5][：:])', r'\1\2', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text


def _first_n_lines(text: str, n: int = 20) -> List[str]:
    lines = []
    for line in text.strip().split("\n"):
        s = line.strip()
        if s:
            lines.append(s)
        if len(lines) >= n:
            break
    return lines


def _header_categories(start_keywords: List[str]) -> str:
    for kw in start_keywords:
        if kw in EDU_HEADERS:
            return "edu"
        if kw in SKILL_HEADERS:
            return "skill"
        if kw in EXP_HEADERS:
            return "exp"
    return "other"


def _get_other_headers(category: str) -> List[str]:
    others = []
    if category != "edu":
        others.extend(EDU_HEADERS)
    if category != "skill":
        others.extend(SKILL_HEADERS)
    if category != "exp":
        others.extend(EXP_HEADERS)
    return others


def _find_section(lines: List[str], start_keywords: List[str],
                  stop_keywords: List[str], start_from: int = 0) -> tuple:
    start_idx = -1
    for i in range(start_from, len(lines)):
        s = lines[i].strip().lower()
        if any(kw.lower() in s for kw in start_keywords):
            start_idx = i
            break
    if start_idx == -1:
        return (-1, -1)

    category = _header_categories(start_keywords)
    other_headers = [kw.lower() for kw in _get_other_headers(category)]

    end_idx = len(lines)
    for i in range(start_idx + 1, len(lines)):
        s = lines[i].strip()
        if not s:
            continue
        sl = s.lower()

        if any(kw in sl for kw in other_headers):
            # 跳过疑似两栏侧边标签：行很短 ≤6 字且在节起始 3 行内
            is_sidebar = (len(s) <= 6 and i - start_idx <= 3
                          and not any(c.isdigit() for c in s))
            if not is_sidebar:
                end_idx = i
                break
            continue

        if any(sk.lower() in sl for sk in stop_keywords):
            if len(s) < 20:
                end_idx = i
                break

    return (start_idx, end_idx)


# ============================================================
# 姓名提取
# ============================================================

def extract_name(text: str) -> str:
    text = _normalize_pdf_text(text)
    non_empty = _first_n_lines(text, 15)

    # 策略 1：前缀检测
    name_prefix = re.compile(r'(?:姓名|Name|name)\s*[:：]\s*(\S+)')
    for line in non_empty:
        m = name_prefix.search(line)
        if m:
            candidate = m.group(1).strip().rstrip(",.，。")
            if candidate:
                return candidate

    # 跳过模式 —— 节标题 + 个人属性
    skip_re = re.compile(
        r'^(?:(?:性\s*别|生\s*日|籍\s*贯|出生|民\s*族|政\s*治|电\s*话|'
        r'手\s*机|邮\s*箱|学\s*历|求职|期望|个人|简\s*历'
        r'|RESUME|CV|Curriculum Vitae'
        r'|联系电话|电子邮箱|性 别|生 日|籍 贯|电 话|邮 箱|学 历|'
        r'年龄|身高|体重|婚\s*姻|健\s*康'
        r')[:：].*'
        r'|科研经历|教育背景|教育经历|竞赛经历|项目经历|实习经历|'
        r'工作经历|校园经历|社会实践|校内实践|专业技能|自我评价'
        r')$',
        re.IGNORECASE
    )

    for line in non_empty:
        parts = [p.strip() for p in line.split("|") if p.strip()]
        line_clean = parts[0]

        stripped = (line_clean.replace("-", "").replace(" ", "")
                    .replace("(", "").replace(")", ""))
        if re.search(r'\d{8,}', stripped) or '@' in line_clean:
            continue

        if skip_re.match(line_clean):
            continue

        # 中文姓名：2~4 个汉字
        # 优先取行首的 2-4 字（解决"关文欣 南昌大学"）
        m2 = re.match(r'^([\u4e00-\u9fa5]{2,4})\s', line_clean)
        if m2:
            candidate = m2.group(1)
            # 过滤"科研经历"等节标题
            if candidate not in ("科研经历", "教育背景", "教育经历",
                                  "竞赛经历", "项目经历", "实习经历",
                                  "工作经历", "专业技能", "自我评价",
                                  "校园经历", "社会实践", "校内实践"):
                return candidate

        chinese = re.findall(r'[\u4e00-\u9fa5]', line_clean)
        if 2 <= len(chinese) <= 4:
            non_alpha = len(re.sub(r'[\u4e00-\u9fa5\s]', '', line_clean))
            if non_alpha <= 2:
                cand = line_clean.strip()
                if cand not in ("科研经历", "教育背景", "教育经历",
                                 "竞赛经历", "项目经历", "实习经历",
                                 "工作经历", "专业技能", "自我评价",
                                 "校园经历", "社会实践", "校内实践"):
                    return cand

        # 英文姓名：2+ 个首字母大写的词
        words = [w for w in line_clean.split() if w.isalpha()]
        if len(words) >= 2 and all(w.istitle() for w in words):
            skip_words = {'resume', 'cv', 'curriculum', 'vitae',
                          'education', 'experience', 'skills',
                          'phone', 'email', 'address', 'contact'}
            if not any(w.lower() in skip_words for w in words):
                return " ".join(words)

    # 策略 3：兜底 —— 第一行纯汉字 2~4 字（跳过已知节标题）
    for line in non_empty:
        stripped = line.strip()
        if 2 <= len(stripped) <= 4 and re.fullmatch(r'[\u4e00-\u9fa5]+',
                                                     stripped):
            if stripped not in ("科研经历", "教育背景", "教育经历",
                                "竞赛经历", "项目经历", "实习经历",
                                "工作经历", "专业技能", "自我评价",
                                "校园经历", "社会实践", "校内实践"):
                return stripped

    return ""


# ============================================================
# 邮箱提取
# ============================================================

def extract_email(text: str) -> str:
    emails = re.findall(
        r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}',
        text
    )
    return emails[0] if emails else ""


# ============================================================
# 电话提取
# ============================================================

def _clean_phone(phone: str) -> str:
    """清理电话号码中的空格、括号、短横线"""
    return re.sub(r'[\s\-\(\)\（\）]', '', phone)


def extract_phone(text: str) -> str:
    text = _normalize_pdf_text(text)

    # 1. 中国大陆手机（纯 11 位）
    phones = re.findall(r'1[3-9]\d{9}', text)
    if phones:
        return phones[0]

    # 2. 带 +86 前缀
    phones = re.findall(r'(?:\+?86[-. ]?)?1[3-9]\d{9}', text)
    if phones:
        return _clean_phone(phones[0])

    # 3. (xxx) xxx-xxxx 或 xxx-xxx-xxxx 或 xxx xxxx xxxx
    phones = re.findall(r'\(?\d{3}\)?[-.\s]?\d{3,4}[-.\s]?\d{4}', text)
    if phones:
        return _clean_phone(phones[0])

    # 4. 国际格式 +XX ...
    phones = re.findall(r'\+\d{1,3}[-.\s]?\d{4,14}', text)
    if phones:
        return _clean_phone(phones[0])

    # 5. 中国大陆固话
    phones = re.findall(r'0\d{2,3}[-.\s]?\d{7,8}', text)
    if phones:
        return _clean_phone(phones[0])

    return ""


# ============================================================
# 教育经历提取
# ============================================================

_DATE_PATTERNS = [
    # 中文年-月到年-月  "2022 年1 月 – 2026 年5 月"
    r'(?:20|19)\d{2}\s*年\s*\d{1,2}\s*月\s*(?:[–\-—~]|至|到|to)\s*'
    r'(?:20|19)\d{2}\s*年\s*\d{1,2}\s*月',
    # 中文年-月到今  "2022 年9 月 – 今"
    r'(?:20|19)\d{2}\s*年\s*\d{1,2}\s*月\s*(?:[–\-—~]|至|到)\s*(?:今|至今)',
    # 点号格式区间 "2022.09-2026.06"
    r'(?:20|19)\d{2}\.\d{1,2}\s*(?:[–\-—~]|至|到)\s*'
    r'(?:20|19)\d{2}\.\d{1,2}',
    # 点号格式到今 "2022.09-今"
    r'(?:20|19)\d{2}\.\d{1,2}\s*(?:[–\-—~]|至|到)\s*(?:今|至今|Present|Now)',
    # 点号到英文 "2022.09 - Present"
    r'(?:20|19)\d{2}\.\d{1,2}\s*(?:[–\-—~]|至|到)\s*(?:Present|Now)',
    # 斜杠格式
    r'(?:20|19)\d{2}/\d{1,2}\s*(?:[–\-—~]|至|到)\s*'
    r'(?:20|19)\d{2}/\d{1,2}',
    # 纯年份区间
    r'(?:20|19)\d{2}\s*(?:[–\-—~]|至|到)\s*(?:20|19)\d{2}',
    # 英文月份格式
    r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*'
    r'\s+(?:20|19)\d{2}\s*(?:[–\-—~]|至|到)\s*'
    r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*'
    r'\s+(?:20|19)\d{2}',
    # 单端点号 "2022.09"
    r'(?:20|19)\d{2}\.\d{1,2}',
]
_DATE_RE = re.compile('|'.join(f'(?:{p})' for p in _DATE_PATTERNS))

_SCHOOL_RE = re.compile(
    '|'.join(re.escape(kw) for kw in SCHOOL_KEYWORDS),
    re.IGNORECASE
)
_DEGREE_RE = re.compile(
    '|'.join(re.escape(kw) for kw in DEGREE_KEYWORDS),
    re.IGNORECASE
)

_EDU_FILTER_KEYWORDS = [
    "电话", "手机", "邮箱", "Email", "email",
    "性别", "生日", "籍贯", "民族", "出生", "政治面貌",
]

# 教育节内不应当作学校/学位行处理的排除关键词
_EDU_SKIP_LINE_KEYWORDS = [
    "荣誉奖项", "主修课程", "主要课程", "相关课程", "GPA",
    "获奖经历", "排名", "英语水平", "CET",
]


def extract_education(text: str) -> List[Dict[str, str]]:
    text = _normalize_pdf_text(text)
    lines = text.split("\n")

    start_idx, end_idx = _find_section(lines, EDU_HEADERS, STOP_KEYWORDS)
    if start_idx == -1:
        return []

    # 收集教育节内容，跳过个人属性行和教育无关行
    edu_lines = []
    for line in lines[start_idx + 1:end_idx]:
        s = line.strip()
        if not s:
            continue
        if any(kw in s for kw in _EDU_FILTER_KEYWORDS):
            continue
        if any(kw in s for kw in _EDU_SKIP_LINE_KEYWORDS):
            continue
        # 排除纯符号行
        if re.search(r'^[\s•●⚫\-–—*★☆]+$', s):
            continue
        # 排除"姓名 学校"这种行（如"关文欣 南昌大学"）
        if re.match(r'^[\u4e00-\u9fa5]{2,4}\s+', s):
            name_part = re.match(r'^([\u4e00-\u9fa5]{2,4})', s).group(1)
            if name_part not in ("科研经历", "教育背景", "教育经历",
                                  "竞赛经历", "项目经历", "实习经历",
                                  "工作经历", "专业技能", "自我评价",
                                  "校园经历", "社会实践", "校内实践"):
                # 如果不是学校名（如"东北大学"），则跳过这个人名行
                if not any(kw in name_part for kw in SCHOOL_KEYWORDS):
                    continue
        edu_lines.append(s)

    if not edu_lines:
        return []

    # 对每行分类
    classified = []
    for line in edu_lines:
        info = {"raw": line, "type": "other"}
        dm = _DATE_RE.search(line)
        has_school = bool(_SCHOOL_RE.search(line))
        has_degree = bool(_DEGREE_RE.search(line))

        if dm:
            info["date_raw"] = dm.group(0)
            info["type"] = "date"
        if has_school:
            info["type"] = "school" if info["type"] == "other" else "mixed"
        if has_degree:
            info["type"] = "degree" if info["type"] == "other" else "mixed"

        classified.append(info)

    # 分组条目
    entries_raw = []
    current = []
    for cinfo in classified:
        if cinfo["type"] in ("date", "school", "mixed") and current:
            has_school_in_current = any(
                c.get("type") in ("school", "mixed") for c in current
            )
            if cinfo["type"] == "school" and has_school_in_current:
                entries_raw.append(current)
                current = [cinfo]
            elif cinfo["type"] == "mixed" and has_school_in_current:
                entries_raw.append(current)
                current = [cinfo]
            else:
                current.append(cinfo)
        else:
            current.append(cinfo)
    if current:
        entries_raw.append(current)

    # 提取字段
    result = []
    for entry in entries_raw:
        edu = {"school": "", "degree": "", "major": "", "period": ""}

        for cinfo in entry:
            raw = cinfo["raw"]
            if cinfo["type"] == "date" and not edu["period"]:
                edu["period"] = cinfo.get("date_raw", raw)
            elif cinfo["type"] == "school" and not edu["school"]:
                edu["school"] = raw
            elif cinfo["type"] == "degree" and not edu["degree"]:
                edu["degree"] = raw
            elif cinfo["type"] == "mixed":
                raw = cinfo["raw"]
                if not edu["school"] and _SCHOOL_RE.search(raw):
                    # 从混合行中剥离日期部分，只取学校内容
                    date_part = cinfo.get("date_raw", "")
                    if date_part:
                        school_candidate = raw.replace(date_part, "", 1).strip().lstrip("-\u2013\u2014\u2010 ")
                    else:
                        school_candidate = raw
                    edu["school"] = school_candidate
                if not edu["degree"] and _DEGREE_RE.search(raw):
                    edu["degree"] = raw
                if not edu["period"] and cinfo.get("date_raw"):
                    edu["period"] = cinfo["date_raw"]
            elif cinfo["type"] == "other":
                if any(kw in raw for kw in
                       ["主修课程", "主要课程", "GPA", "相关课程"]):
                    continue
                if re.search(r'^[\s•●⚫\-–—*★☆]+$', raw):
                    continue
                if not edu["major"] and edu["school"]:
                    edu["major"] = raw

        if edu["school"]:
            result.append(edu)

    return result


# ============================================================
# 技能提取
# ============================================================

def extract_skill_section(text: str) -> str:
    text = _normalize_pdf_text(text)
    lines = text.split("\n")

    sidx, eidx = _find_section(lines, SKILL_HEADERS, STOP_KEYWORDS)
    if sidx == -1:
        return _extract_skill_fallback(text)

    skill_lines = []
    for line in lines[sidx + 1:eidx]:
        s = line.strip()
        if s and not re.search(r'^[\s•●⚫\-–—*★☆]+$', s):
            skill_lines.append(s)
    return "\n".join(skill_lines) if skill_lines else ""


def _extract_skill_fallback(text: str) -> str:
    lines = text.split("\n")
    in_section = False
    skill_lines = []

    for line in lines:
        s = line.strip()
        if not s:
            continue
        if not in_section:
            if any(h.lower() in s.lower() for h in SKILL_HEADERS):
                in_section = True
                skill_lines.append(s)
            continue
        other_headers = [kw.lower() for kw in EDU_HEADERS + EXP_HEADERS]
        if any(h in s.lower() for h in other_headers):
            break
        skill_lines.append(s)

    return "\n".join(skill_lines)


# ============================================================
# 工作/实习/项目经历提取
# ============================================================

def extract_experience(text: str) -> List[Dict[str, str]]:
    text = _normalize_pdf_text(text)
    lines = text.split("\n")

    sidx, eidx = _find_section(lines, EXP_HEADERS, STOP_KEYWORDS)
    if sidx == -1:
        return []

    exp_lines = []
    for line in lines[sidx + 1:eidx]:
        s = line.strip()
        if s:
            exp_lines.append(s)

    if not exp_lines:
        return []

    # 多格式日期（含中文"年"、"月"、"日"）
    exp_date_re = re.compile(
        r'(?:(?:20|19)\d{2}(?:\.\d{1,2})?\s*'
        r'(?:[–\-—~]|至|到)\s*'
        r'(?:20|19)\d{2}(?:\.\d{1,2})?'
        r')|'
        r'(?:20|19)\d{2}\.\d{1,2}'
    )

    entries_raw = []
    current = []
    for line in exp_lines:
        if re.match(r'(?:20|19)\d{2}\.\d{1,2}(?:\s*(?:[–\-—~]|至|到)\s*(?:20|19)\d{2})?(?:\.\d{1,2})?', line):
            if current:
                entries_raw.append(current)
            current = [line]
        else:
            current.append(line)
    if current:
        entries_raw.append(current)

    result = []
    for entry in entries_raw:
        item = {"period": "", "title": "", "description": ""}
        desc_parts = []
        for line in entry:
            if not item["period"]:
                m = exp_date_re.search(line)
                if m:
                    item["period"] = m.group(0)
                    rest = exp_date_re.sub("", line).strip().lstrip("|—–- ")
                    if rest and not item["title"]:
                        item["title"] = rest
                    continue
            if not item["title"] and len(line) < 40:
                item["title"] = line
            else:
                desc_parts.append(line)

        item["description"] = "\n".join(desc_parts).strip()
        if item["period"] or item["title"]:
            result.append(item)

    return result


# ============================================================
# 统一提取入口
# ============================================================

def extract_all(text: str) -> dict:
    return {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "education": extract_education(text),
        "skill_section": extract_skill_section(text),
        "experience": extract_experience(text),
    }
