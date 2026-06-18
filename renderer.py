def render_resume(data: dict) -> str:
    """
    将提取的简历数据渲染为可用的 HTML 页面。
    支持 education / skill_section / experience 三个结构化字段。
    """
    name = data.get("name", "") or "（未识别）"
    email = data.get("email", "") or ""
    phone = data.get("phone", "") or ""
    education = data.get("education", []) or []
    skill_text = data.get("skill_section", "") or ""
    experience = data.get("experience", []) or []

    # --- 教育经历 HTML ---
    edu_html = ""
    for edu in education:
        school = edu.get("school", "")
        degree = edu.get("degree", "")
        major = edu.get("major", "")
        period = edu.get("period", "")

        details = []
        if degree:
            details.append(degree)
        if major:
            details.append(major)
        detail_str = f" · {', '.join(details)}" if details else ""
        period_str = f'<span class="period">{period}</span>' if period else ""

        edu_html += f"""
    <div class="edu-item">
      <div class="edu-header">
        <span class="school">{school}</span>{period_str}
      </div>
      <div class="edu-detail">{detail_str}</div>
    </div>"""

    if not edu_html:
        edu_html = """<div class="empty">暂未识别到教育经历</div>"""

    # --- 技能 HTML（简化：直接按行渲染，避免冒号拆分 bug） ---
    skill_html = ""
    if skill_text:
        for line in skill_text.split("\n"):
            line = line.strip()
            if not line:
                continue
            # 冒号前作为分类标签加粗
            for sep in ("：", ": "):
                if sep in line:
                    parts = line.split(sep, 1)
                    skill_html += (
                        f'<div class="skill-line">'
                        f'<strong>{parts[0]}</strong>{sep}{parts[1]}'
                        f'</div>'
                    )
                    break
            else:
                skill_html += f'<div class="skill-line">{line}</div>'
    if not skill_html:
        skill_html = """<div class="empty">暂未识别到技能</div>"""

    # --- 经历 HTML ---
    exp_html = ""
    for exp in experience:
        title = exp.get("title", "")
        period = exp.get("period", "")
        desc = exp.get("description", "")

        exp_html += """<div class="exp-item">"""
        exp_html += f"""
      <div class="exp-header">
        <span class="exp-title">{title}</span>
        {f'<span class="period">{period}</span>' if period else ''}
      </div>"""
        if desc:
            desc_lines = desc.split("\n")
            desc_html = ""
            for dl in desc_lines:
                dl = dl.strip()
                if not dl:
                    continue
                if dl.startswith("•") or dl.startswith("●") or dl.startswith(""):
                    desc_html += f'<li>{dl.lstrip("•● ")}</li>'
                elif dl.startswith("-"):
                    desc_html += f'<li>{dl.lstrip("- ")}</li>'
                else:
                    desc_html += f'<div class="desc-line">{dl}</div>'
            if "<li>" in desc_html:
                exp_html += f'<ul class="desc-list">{desc_html}</ul>'
            else:
                exp_html += f'<div class="desc-text">{desc_html}</div>'
        exp_html += """</div>"""

    if not exp_html and experience:
        exp_html = """<div class="empty">暂未识别到经历详情</div>"""

    # --- 联系方式 ---
    contact_parts = []
    if email:
        contact_parts.append(f'📧 {email}')
    if phone:
        contact_parts.append(f'📱 {phone}')
    contact_str = "&nbsp;&nbsp;|&nbsp;&nbsp;".join(contact_parts)

    has_experience = any(e.get("title") or e.get("period") for e in experience)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
                 "Microsoft YaHei", Roboto, Helvetica, Arial, sans-serif;
    color: #1a1a2e;
    background: #f5f6fa;
    line-height: 1.6;
  }}
  .resume {{
    max-width: 860px;
    margin: 40px auto;
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.08);
    overflow: hidden;
  }}
  .header {{
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    color: #fff;
    padding: 40px 48px 32px;
  }}
  .header h1 {{
    font-size: 32px;
    font-weight: 700;
    letter-spacing: 2px;
    margin-bottom: 8px;
  }}
  .contact {{
    font-size: 14px;
    color: rgba(255,255,255,0.8);
  }}
  .body {{ padding: 32px 48px 48px; }}
  .section {{ margin-bottom: 32px; }}
  .section:last-child {{ margin-bottom: 0; }}
  .section-title {{
    font-size: 18px;
    font-weight: 600;
    color: #1a1a2e;
    border-bottom: 2px solid #e8e8ef;
    padding-bottom: 8px;
    margin-bottom: 16px;
  }}
  .section-title::before {{
    content: "";
    display: inline-block;
    width: 4px;
    height: 18px;
    background: #1a1a2e;
    border-radius: 2px;
    margin-right: 10px;
    vertical-align: -2px;
  }}
  .edu-item {{ margin-bottom: 16px; }}
  .edu-item:last-child {{ margin-bottom: 0; }}
  .edu-header {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    flex-wrap: wrap;
    gap: 8px;
  }}
  .school {{ font-weight: 600; font-size: 16px; color: #1a1a2e; }}
  .period {{ font-size: 13px; color: #888; white-space: nowrap; }}
  .edu-detail {{ font-size: 14px; color: #555; margin-top: 2px; }}

  .exp-item {{ margin-bottom: 20px; }}
  .exp-item:last-child {{ margin-bottom: 0; }}
  .exp-header {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    flex-wrap: wrap;
    gap: 8px;
  }}
  .exp-title {{ font-weight: 600; font-size: 15px; color: #1a1a2e; }}
  .desc-list {{ margin: 6px 0 0 18px; list-style: disc; font-size: 14px; color: #444; }}
  .desc-list li {{ margin-bottom: 4px; }}
  .desc-text {{ margin-top: 6px; font-size: 14px; color: #444; }}
  .desc-line {{ margin-bottom: 4px; }}

  .skill-line {{
    font-size: 14px;
    color: #444;
    padding: 4px 0;
    border-bottom: 1px solid #f0f0f5;
  }}
  .skill-line:last-child {{ border-bottom: none; }}
  .skill-line strong {{ color: #1a1a2e; }}

  .empty {{
    font-size: 14px;
    color: #aaa;
    font-style: italic;
  }}

  @media (max-width: 640px) {{
    .resume {{ margin: 16px; border-radius: 8px; }}
    .header {{ padding: 24px 20px; }}
    .header h1 {{ font-size: 26px; }}
    .body {{ padding: 24px 20px; }}
    .edu-header, .exp-header {{
      flex-direction: column;
      align-items: flex-start;
    }}
  }}
</style>
</head>
<body>
<div class="resume">
  <div class="header">
    <h1>{name}</h1>
    <div class="contact">{contact_str}</div>
  </div>
  <div class="body">
    <div class="section">
      <div class="section-title">教育经历</div>
      {edu_html}
    </div>
    {f'''
    <div class="section">
      <div class="section-title">经历</div>
      {exp_html}
    </div>''' if has_experience else ''}
    <div class="section">
      <div class="section-title">专业能力</div>
      {skill_html}
    </div>
  </div>
</div>
</body>
</html>"""
