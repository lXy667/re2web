import re
from typing import List, Dict


# ============================================================
# 常量定义
# ============================================================

# 教育经历节标题
EDU_HEADERS = [
    "教育经历", "教育背景", "教育",
    "Education", "EDUCATION",
]

# 技能节标题
SKILL_HEADERS = [
    "专业技能", "专业能力", "技术能力", "技术技能", "编程技能",
    "办公能力", "外语能力", "语言能力", "技能证书",
    "Technical Skills", "Skills", "TECHNICAL SKILLS", "SKILLS",
    "个人技能",
]

# 工作/实习/项目经历节标题
EXP_HEADERS = [
    "工作经历", "实习经历", "项目经历", "工作经验", "项目经验",
    "校内实践", "社会实践", "社会活动",
    "Work Experience", "EXPERIENCE", "Experience",
    "Internship", "INTERNSHIP",
    "Project", "PROJECT",
]

# 通用停止关键词（节边界检测）
STOP_KEYWORDS = [
    "项目经历", "实习经历", "工作经历", "校园经历",
    "专业技能", "专业能力", "技术能力", "技术技能", "编程技能",
    "办公能力", "外语能力", "语言能力", "技能证书",
    "荣誉奖项", "获奖经历", "证书",
    "自我评价", "个人评价",
    "项目经验", "工作经验",
    "校内实践", "社会实践", "社会活动",
    "个人技能",
    "Project", "Projects", "EXPERIENCE", "Experience",
    "Internship", "SKILLS", "Skills",
    "Self-evaluation", "Honors", "Awards", "Certificates",
]

# 学校关键词
SCHOOL_KEYWORDS = [
    "大学", "学院", "University", "College", "Institute", "School",
    "Academy", "研究生院",
]

# 学历关键词
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
    """
    修复 PDF 提取的常见问题：
    - 断字： "性\n别：男" → "性别：男"
    - 只合并第二个中文字后紧接 ：或 : 的情况，避免误合并正常换行。
    """
    # 只修复 PDF 特有的单字分行 + 分隔符模式
    text = re.sub(r'([\u4e00-\u9fa5])\n([\u4e00-\u9fa5][：:])', r'\1\2', text)
    # 压缩多余空格
    text = re.sub(r'[ \t]+', ' ', text)
    return text


def _first_n_lines(text: str, n: int = 20) -> List[str]:
    """获取前 n 个非空行"""
    lines = []
    for line in text.strip().split("\n"):
        s = line.strip()
        if s:
            lines.append(s)
        if len(lines) >= n:
            break
    return lines


def _header_categories(start_keywords: List[str]) -> str:
    """判断一组 start_keywords 属于哪个节分类（edu / skill / exp / other）"""
    for kw in start_keywords:
        if kw in EDU_HEADERS:
            return "edu"
        if kw in SKILL_HEADERS:
            return "skill"
        if kw in EXP_HEADERS:
            return "exp"
    return "other"


def _get_other_headers(category: str) -> List[str]:
    """返回除了 cat 以外的所有节标题"""
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
    """
    在 lines 中定位一个节。
    返回 (节起始行号, 节结束行号)，未找到返回 (-1, -1)。
    只有不同类别的节标题才会触发节终止。
    """
    # 定位起始
    start_idx = -1
    for i in range(start_from, len(lines)):
        s = lines[i].strip().lower()
        if any(kw.lower() in s for kw in start_keywords):
            start_idx = i
            break
    if start_idx == -1:
        return (-1, -1)

    # 确定当前节的分类，只将其他类的标题视为终止条件
    category = _header_categories(start_keywords)
    other_headers = [kw.lower() for kw in _get_other_headers(category)]

    end_idx = len(lines)
    for i in range(start_idx + 1, len(lines)):
        s = lines[i].strip()
        if not s:
            continue
        sl = s.lower()

        # 遇到其他类的节标题 → 终止
        if any(kw in sl for kw in other_headers):
            end_idx = i
            break

        # 遇到停止关键词且行较短 → 终止
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

    # 跳过模式
    skip_re = re.compile(
        r'^(?:(?:性\s*别|生\s*日|籍\s*贯|出生|民\s*族|政\s*治|电\s*话|'
        r'手\s*机|邮\s*箱|学\s*历|求职|期望|个人|简\s*历'
        r'|RESUME|CV|Curriculum Vitae'
        r'|联系电话|电子邮箱|性 别|生 日|籍 贯|电 话|邮 箱|学 历|'
        r'年龄|身高|体重|婚\s*姻|健\s*康'
        r')[:：].*)$',
        re.IGNORECASE
    )

    for line in non_empty:
        parts = [p.strip() for p in line.split("|") if p.strip()]
        line_clean = parts[0]

        # 跳过含长数字或邮箱的行
        stripped = (line_clean.replace("-", "").replace(" ", "")
                    .replace("(", "").replace(")", ""))
        if re.search(r'\d{8,}', stripped) or '@' in line_clean:
            continue

        if skip_re.match(line_clean):
            continue

        # 中文姓名：2~4 个汉字，非汉字字符不超过 2 个
        chinese = re.findall(r'[\u4e00-\u9fa5]', line_clean)
        if 2 <= len(chinese) <= 4:
            non_alpha = len(re.sub(r'[\u4e00-\u9fa5\s]', '', line_clean))
            if non_alpha <= 2:
                return line_clean.strip()

        # 英文姓名：2+ 个首字母大写的词
        words = [w for w in line_clean.split() if w.isalpha()]
        if len(words) >= 2 and all(w.istitle() for w in words):
            skip_words = {'resume', 'cv', 'curriculum', 'vitae',
                          'education', 'experience', 'skills',
                          'phone', 'email', 'address', 'contact'}
            if not any(w.lower() in skip_words for w in words):
                return " ".join(words)

    # 策略 3：兜底 —— 第一行纯汉字 2~4 字
    for line in non_empty:
        stripped = line.strip()
        if 2 <= len(stripped) <= 4 and re.fullmatch(r'[\u4e00-\u9fa5]+',
                                                     stripped):
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
# 电话号码提取
# ============================================================

def extract_phone(text: str) -> str:
    text = _normalize_pdf_text(text)

    # 1. 中国大陆手机（纯 11 位）
    phones = re.findall(r'1[3-9]\d{9}', text)
    if phones:
        return phones[0]

    # 2. 带 +86 前缀
    phones = re.findall(r'(?:\+?86[-. ]?)?1[3-9]\d{9}', text)
    if phones:
        return phones[0]

    # 3. (xxx) xxx-xxxx 或 xxx-xxx-xxxx
    phones = re.findall(r'\(?\d{3}\)?[-.\s]?\d{3,4}[-.\s]?\d{4}', text)
    if phones:
        return phones[0]

    # 4. 国际格式 +XX ...
    phones = re.findall(r'\+\d{1,3}[-.\s]?\d{4,14}', text)
    if phones:
        return phones[0]

    # 5. 中国大陆固话
    phones = re.findall(r'0\d{2,3}[-.\s]?\d{7,8}', text)
    if phones:
        return phones[0]

    return ""


# ============================================================
# 教育经历提取
# ============================================================

_DATE_PATTERNS = [
    r'(?:20|19)\d{2}\s*年\s*\d{1,2}\s*月\s*(?:[–\-—~]|至|到|to)\s*'
    r'(?:20|19)\d{2}\s*年\s*\d{1,2}\s*月',
    r'(?:20|19)\d{2}\s*年\s*\d{1,2}\s*月',
    r'(?:20|19)\d{2}\.\d{1,2}\s*(?:[–\-—~]|至|到)\s*'
    r'(?:20|19)\d{2}\.\d{1,2}',
    r'(?:20|19)\d{2}\.\d{1,2}',
    r'(?:20|19)\d{2}/\d{1,2}\s*(?:[–\-—~]|至|到)\s*'
    r'(?:20|19)\d{2}/\d{1,2}',
    r'(?:20|19)\d{2}\s*(?:[–\-—~]|至|到)\s*(?:20|19)\d{2}',
    r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*'
    r'\s+(?:20|19)\d{2}\s*(?:[–\-—~]|至|到)\s*'
    r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*'
    r'\s+(?:20|19)\d{2}',
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

# 教育节内部的过滤关键词（个人联系方式等不属于教育的内容）
_EDU_FILTER_KEYWORDS = [
    "电话", "手机", "邮箱", "Email", "email", "学历",
    "性别", "生日", "籍贯", "民族", "出生", "政治面貌",
]


def extract_education(text: str) -> List[Dict[str, str]]:
    text = _normalize_pdf_text(text)
    lines = text.split("\n")

    start_idx, end_idx = _find_section(lines, EDU_HEADERS, STOP_KEYWORDS)
    if start_idx == -1:
        return []

    # 收集教育节内容，跳过个人属性行
    edu_lines = []
    for line in lines[start_idx + 1:end_idx]:
        s = line.strip()
        if not s:
            continue
        # 跳过明显不属于教育的行
        if any(kw in s for kw in _EDU_FILTER_KEYWORDS):
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
            if cinfo["type"] == "date" and not edu["period"]:
                edu["period"] = cinfo.get("date_raw", cinfo["raw"])
            elif cinfo["type"] == "school" and not edu["school"]:
                edu["school"] = cinfo["raw"]
            elif cinfo["type"] == "degree" and not edu["degree"]:
                edu["degree"] = cinfo["raw"]
            elif cinfo["type"] == "mixed":
                raw = cinfo["raw"]
                if not edu["school"] and _SCHOOL_RE.search(raw):
                    edu["school"] = raw
                if not edu["degree"] and _DEGREE_RE.search(raw):
                    edu["degree"] = raw
                if not edu["period"] and cinfo.get("date_raw"):
                    edu["period"] = cinfo["date_raw"]
            elif cinfo["type"] == "other":
                raw_c = cinfo["raw"]
                if any(kw in raw_c for kw in
                       ["主修课程", "主要课程", "GPA", "相关课程", "GPA"]):
                    continue
                # 跳过 "•" "" 等纯符号行
                if re.search(r'^[\s•●\-–—*★☆]+$', raw_c):
                    continue
                if not edu["major"] and edu["school"]:
                    edu["major"] = raw_c

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
        if s and not re.search(r'^[\s•●\-–—*★☆]+$', s):
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

        # 其他类节标题 → 结束
        other_headers = [kw.lower() for kw in
                         EDU_HEADERS + EXP_HEADERS]
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

    exp_date_re = re.compile(
        r'(?:(?:20|19)\d{2}\s*(?:[./]?\d{1,2})?\s*'
        r'(?:[–\-—~]|至|到)\s*'
        r'(?:20|19)\d{2}\s*(?:[./]?\d{1,2})?'
        r')|'
        r'(?:20|19)\d{2}\s*(?:[./]?\d{1,2})?'
    )

    # 按日期开头分组条目
    entries_raw = []
    current = []
    for line in exp_lines:
        if re.match(r'(?:20|19)\d{2}', line):
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

# ============================================================
# (patch) 改进 extract_experience：支持单日期模式
# ============================================================
