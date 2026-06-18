import streamlit as st
import os
import json
from parser import extract_text
from renderer import render_resume
from extractor import extract_all
from streamlit.components.v1 import html as st_html

st.set_page_config(
    page_title="Resume2Web",
    page_icon="📄",
    layout="wide",
)

st.title("📄 Resume2Web — 在线简历识别与生成")

uploaded_file = st.file_uploader(
    "上传 PDF 简历",
    type=["pdf"],
    help="支持 PDF 格式的简历文件",
)

if uploaded_file:
    # ---------- 保存 ----------
    save_path = os.path.join("uploads", uploaded_file.name)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success(f"✅ 上传成功：{uploaded_file.name}")

    # ---------- 解析 PDF ----------
    with st.spinner("正在解析 PDF..."):
        try:
            text = extract_text(save_path)
        except Exception as e:
            st.error(f"PDF 解析失败：{e}")
            st.stop()

    # 显示原始文本（可折叠）
    with st.expander("📖 查看 PDF 解析原文", expanded=False):
        st.text_area("解析结果", text, height=400)
        st.caption(f"字符数：{len(text)}")

    # ---------- 信息提取 ----------
    with st.spinner("正在提取结构化信息..."):
        try:
            data = extract_all(text)
        except Exception as e:
            st.error(f"信息提取失败：{e}")
            st.stop()

    # ========== 展示结果 ==========

    # 基本信息
    st.subheader("👤 基本信息")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("姓名", data["name"] if data["name"] else "（未识别）")
    with col2:
        st.metric("邮箱", data["email"] if data["email"] else "（未识别）")
    with col3:
        st.metric("电话", data["phone"] if data["phone"] else "（未识别）")

    # 教育经历
    st.subheader("🎓 教育经历")
    if data["education"]:
        for i, edu in enumerate(data["education"], 1):
            with st.container():
                cols = st.columns([3, 1, 2])
                with cols[0]:
                    st.markdown(f"**{edu.get('school', '')}**")
                    if edu.get("major"):
                        st.caption(f"专业：{edu['major']}")
                with cols[1]:
                    if edu.get("degree"):
                        st.markdown(f"*{edu['degree']}*")
                with cols[2]:
                    if edu.get("period"):
                        st.markdown(f"📅 {edu['period']}")
                if i < len(data["education"]):
                    st.divider()
    else:
        st.info("暂未识别到教育经历")

    # 工作/实习/项目经历
    if data.get("experience"):
        st.subheader("💼 经历")
        for i, exp in enumerate(data["experience"], 1):
            with st.expander(
                f"{exp.get('title', '（未命名）')}　"
                f"{'　' + exp.get('period', '') if exp.get('period') else ''}",
                expanded=(i == 1),
            ):
                if exp.get("description"):
                    st.markdown(exp["description"])
                else:
                    st.caption("暂无详细描述")
    else:
        st.subheader("💼 经历")
        st.info("暂未识别到工作/实习/项目经历")

    # 技能
    st.subheader("🛠️ 技能")
    if data.get("skill_section"):
        st.text_area(
            "技能内容",
            data["skill_section"],
            height=200,
            label_visibility="collapsed",
        )
    else:
        st.info("暂未识别到技能信息")

    # ---------- 保存 JSON ----------
    resume_path = "resume.json"
    with open(resume_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # ---------- 在线简历预览 ----------
    st.subheader("🏠 在线简历预览")
    resume_html = render_resume(data)

    # 使用 components.html 以保留完整的 CSS 样式
    st_html(
        resume_html,
        height=900,
        scrolling=True,
    )

    # 额外提供一个下载按钮
    st.download_button(
        label="📥 下载简历 HTML",
        data=resume_html,
        file_name=f"{data.get('name', 'resume')}.html",
        mime="text/html",
    )
