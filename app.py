import streamlit as st
import os
import json
from parser import extract_text
from renderer import render_resume
from extractor import extract_all
from streamlit.components.v1 import html as st_html

# ============================================================
# 部署开关：上线时改成 False 即可删除测试功能
# ============================================================
TEST_MODE = True


def run_upload_flow(uploaded_file):
    """处理单个 PDF 文件，显示提取结果"""
    save_path = os.path.join("uploads", uploaded_file.name)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success(f"✅ 上传成功：{uploaded_file.name}")

    with st.spinner("正在解析 PDF..."):
        try:
            text = extract_text(save_path)
        except Exception as e:
            st.error(f"PDF 解析失败：{e}")
            return

    with st.expander("📖 查看 PDF 解析原文", expanded=False):
        st.text_area("解析结果", text, height=400)
        st.caption(f"字符数：{len(text)}")

    with st.spinner("正在提取结构化信息..."):
        try:
            data = extract_all(text)
        except Exception as e:
            st.error(f"信息提取失败：{e}")
            return

    display_results(data, text)


def display_results(data, raw_text=None):
    """展示提取结果：基本信息 + 教育 + 经历 + 技能 + 预览"""
    # ---- 基本信息 ----
    st.subheader("👤 基本信息")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("姓名", data["name"] if data["name"] else "（未识别）")
    with col2:
        st.metric("邮箱", data["email"] if data["email"] else "（未识别）")
    with col3:
        st.metric("电话", data["phone"] if data["phone"] else "（未识别）")

    # ---- 教育经历 ----
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

    # ---- 经历 ----
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

    # ---- 技能 ----
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

    # ---- 保存 JSON ----
    json.dump(data, open("resume.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    # ---- 在线简历预览 ----
    st.subheader("🏠 在线简历预览")
    resume_html = render_resume(data)
    st_html(resume_html, height=900, scrolling=True)

    st.download_button(
        label="📥 下载简历 HTML",
        data=resume_html,
        file_name=f"{data.get('name', 'resume')}.html",
        mime="text/html",
    )


# ============================================================
# 测试模式：自动加载 test/ 下的所有 PDF
# ============================================================
if TEST_MODE:
    test_dir = os.path.join(os.path.dirname(__file__), "test")
    test_files = sorted([
        f for f in os.listdir(test_dir) if f.lower().endswith(".pdf")
    ])

    if not test_files:
        st.warning("⚠️ test/ 文件夹中未找到 PDF 测试文件")
        st.stop()

    # 初始化 Session State
    if "test_idx" not in st.session_state:
        st.session_state.test_idx = 0
    if "test_data" not in st.session_state:
        st.session_state.test_data = {}

    # 翻页器（顶部）
    n = len(test_files)
    col_prev, col_info, col_next = st.columns([1, 4, 1])
    with col_prev:
        if st.button("◀ 上一个", use_container_width=True,
                     disabled=(st.session_state.test_idx == 0)):
            st.session_state.test_idx = max(0, st.session_state.test_idx - 1)
            st.rerun()
    with col_info:
        idx = st.session_state.test_idx
        filename = test_files[idx]
        st.markdown(
            f"<div style='text-align:center;padding:6px 0'>"
            f"<strong>测试用例 {idx+1}/{n}</strong><br>"
            f"<code style='font-size:0.9em'>{filename}</code>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with col_next:
        if st.button("下一个 ▶", use_container_width=True,
                     disabled=(st.session_state.test_idx == n - 1)):
            st.session_state.test_idx = min(n - 1, st.session_state.test_idx + 1)
            st.rerun()

    st.divider()

    # 当前测试用例的处理和结果
    idx = st.session_state.test_idx
    filename = test_files[idx]

    # 缓存解析结果避免重复解析
    cache_key = filename
    if cache_key not in st.session_state.test_data:
        filepath = os.path.join(test_dir, filename)
        with st.spinner(f"正在解析 {filename}..."):
            text = extract_text(filepath)
            data = extract_all(text)
        st.session_state.test_data[cache_key] = {"text": text, "data": data}
    else:
        text = st.session_state.test_data[cache_key]["text"]
        data = st.session_state.test_data[cache_key]["data"]

    # 显示提取统计摘要
    summ = st.columns(4)
    with summ[0]:
        st.metric("📛 姓名", data["name"] or "×")
    with summ[1]:
        st.metric("📧 邮箱", data["email"] or "×")
    with summ[2]:
        st.metric("📱 电话", data["phone"] or "×")
    with summ[3]:
        st.metric("🏫 教育", f"{len(data['education'])} 条")

    # 展开查看完整结果
    with st.expander("📋 查看完整提取结果", expanded=True):
        display_results(data, text)

    # 底部翻页器
    st.divider()
    col_prev2, col_info2, col_next2 = st.columns([1, 4, 1])
    with col_prev2:
        if st.button("◀ 上一个", key="prev_bottom", use_container_width=True,
                     disabled=(st.session_state.test_idx == 0)):
            st.session_state.test_idx = max(0, st.session_state.test_idx - 1)
            st.rerun()
    with col_info2:
        st.markdown(
            f"<div style='text-align:center;padding:6px 0;color:#888'>"
            f"测试 {idx+1}/{n} · {filename}</div>",
            unsafe_allow_html=True,
        )
    with col_next2:
        if st.button("下一个 ▶", key="next_bottom", use_container_width=True,
                     disabled=(st.session_state.test_idx == n - 1)):
            st.session_state.test_idx = min(n - 1, st.session_state.test_idx + 1)
            st.rerun()

else:
    # ============================================================
    # 线上模式：正常上传
    # ============================================================
    st.title("📄 Resume2Web — 在线简历识别与生成")

    uploaded_file = st.file_uploader(
        "上传 PDF 简历",
        type=["pdf"],
        help="支持 PDF 格式的简历文件",
    )

    if uploaded_file:
        run_upload_flow(uploaded_file)
