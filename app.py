# -*- coding: utf-8 -*-
"""交易哨兵 — Streamlit 前端（升级版）。
增加了示例对话、Agent 流程可视化、更精致的 UI 样式。
"""
import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from core import analyze, load_kb, load_kb_vectors

# ---------- 页面配置 ----------
st.set_page_config(page_title="交易哨兵", page_icon="🛡️", layout="wide")

# ---------- 自定义 CSS ----------
st.markdown(
    """
    <style>
    header[data-testid="stHeader"] { background: transparent; }
    #MainMenu, footer { visibility: hidden; }
    html, body, [class*="css"] {
        font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
    }
    .stButton > button {
        border-radius: 10px;
        background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
        color: #ffffff;
        font-weight: 600;
        padding: 10px 24px;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);
        color: #ffffff;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    }
    .risk-card {
        border-radius: 16px;
        padding: 28px 22px;
        text-align: center;
        color: #ffffff;
        font-size: 32px;
        font-weight: 700;
        margin: 8px 0 6px 0;
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
        letter-spacing: 2px;
    }
    .risk-sub {
        text-align: center;
        color: #475569;
        margin-bottom: 18px;
        font-size: 15px;
        line-height: 1.6;
    }
    .example-btn {
        display: inline-block;
        padding: 6px 14px;
        margin: 4px 6px 4px 0;
        background: #f1f5f9;
        color: #334155;
        border-radius: 20px;
        font-size: 13px;
        cursor: pointer;
        transition: all 0.2s;
        border: 1px solid #e2e8f0;
    }
    .example-btn:hover {
        background: #e2e8f0;
        border-color: #cbd5e1;
    }
    .evidence-card {
        background: #f8fafc;
        border-left: 4px solid #0f172a;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        margin: 8px 0;
    }
    .strategy-card {
        border-radius: 12px;
        padding: 16px;
        margin: 4px 0;
    }
    .top-action {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border-radius: 12px;
        padding: 16px 20px;
        margin: 16px 0;
        border-left: 4px solid #f59e0b;
    }
    .agent-step {
        display: flex;
        align-items: center;
        padding: 8px 0;
    }
    .agent-icon {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        margin-right: 12px;
        flex-shrink: 0;
    }
    .hero-section {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0f172a 100%);
        border-radius: 16px;
        padding: 32px 28px;
        color: white;
        margin-bottom: 24px;
    }
    .hero-title {
        font-size: 36px;
        font-weight: 800;
        margin-bottom: 8px;
        background: linear-gradient(90deg, #ffffff 0%, #93c5fd 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .hero-sub {
        font-size: 15px;
        color: #94a3b8;
        line-height: 1.6;
    }
    .stat-box {
        background: rgba(255,255,255,0.08);
        border-radius: 10px;
        padding: 14px 18px;
        text-align: center;
        backdrop-filter: blur(10px);
    }
    .stat-number {
        font-size: 24px;
        font-weight: 700;
        color: #fbbf24;
    }
    .stat-label {
        font-size: 12px;
        color: #94a3b8;
        margin-top: 4px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

RISK_COLOR = {
    "安全": "#22c55e",
    "低危": "#84cc16",
    "中危": "#eab308",
    "高危": "#f97316",
    "确认诈骗": "#ef4444",
}

# 兼容 Streamlit Cloud 的 Secrets（本地用 .env）
try:
    if "DEEPSEEK_API_KEY" in st.secrets:
        os.environ["DEEPSEEK_API_KEY"] = st.secrets["DEEPSEEK_API_KEY"]
except Exception:
    pass

# ---------- 加载数据 ----------
kb = load_kb()
idf, kb_vectors = load_kb_vectors()

# 统计知识库信息
high_risk_count = sum(1 for p in kb if p.get("risk_level") == "高危")
medium_risk_count = sum(1 for p in kb if "中" in p.get("risk_level", ""))

# ---------- 示例对话 ----------
EXAMPLES = {
    "⚠️ 保证金诈骗": (
        "A: 你好，这款手机还在吗？\n"
        "B: 在的，走平台担保交易。\n"
        "A: 好的，我拍了。\n"
        "B: 等一下，这个是特惠价，需要先交200元保证金，确认收货后退还。\n"
        "A: 为什么要交保证金？\n"
        "B: 平台规定的，防止恶意退款，交易完成后自动退给你，放心。"
    ),
    "💬 加微信脱离平台": (
        "A: 这件衣服多少钱？\n"
        "B: 150不包邮。\n"
        "A: 能便宜点吗？\n"
        "B: 加微信聊吧，这里发消息太慢了，微信上给你优惠价，微信号xxxxx。\n"
        "A: 不能在这说吗？\n"
        "B: 平台限制多，微信上方便，还能发更多图片给你看。"
    ),
    "👑 假客服解冻": (
        "A: 你好，我是平台客服，检测到你的账户有异常交易，需要冻结处理。\n"
        "B: 啊？什么异常？我没干什么啊。\n"
        "A: 你需要配合我们做风控验证，点击这个链接完成解冻，不然账户会被永久封禁。\n"
        "B: 可是我没收到官方通知啊。\n"
        "A: 这是内部风控系统，用户端看不到的，赶紧处理，超时就解冻不了了。"
    ),
    "💰 低价引流+紧迫感": (
        "A: 这台iPad多少钱？\n"
        "B: 原价5000的，现在急出2500，白菜价了。\n"
        "A: 这么便宜？不会有问题吧？\n"
        "B: 急用钱没办法，今天不买明天就没了，已经有三个人问了。\n"
        "A: 能验机吗？\n"
        "B: 没问题的，我是学生，不骗人的，你要的话赶紧拍，不然被别人抢了。"
    ),
    "✅ 正常交易（负样本）": (
        "A: 你好，这本书还在吗？\n"
        "B: 在的，25块包邮。\n"
        "A: 书的品相怎么样？有没有笔记？\n"
        "B: 九成新，只有少量笔记，不影响使用。\n"
        "A: 好的，我拍了。\n"
        "B: 好的，明天给你发货，注意查收。"
    ),
}

# ---------- 顶部 Hero 区 ----------
st.markdown(
    f"""
    <div class="hero-section">
        <div class="hero-title">🛡️ 交易哨兵</div>
        <div class="hero-sub">
            二手交易反诈智能分析系统 · 基于多 Agent 协作架构<br>
            粘贴对话，AI 帮你识别诈骗信号，守护你的每一笔交易
        </div>
        <div style="display: flex; gap: 12px; margin-top: 20px;">
            <div class="stat-box">
                <div class="stat-number">{len(kb)}</div>
                <div class="stat-label">骗局套路</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{high_risk_count}</div>
                <div class="stat-label">高危类型</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">5</div>
                <div class="stat-label">AI Agent</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">30+</div>
                <div class="stat-label">测试用例</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- 侧边栏 ----------
with st.sidebar:
    st.markdown("## 🛡️ 交易哨兵")
    st.caption("二手交易反诈 · 多Agent智能分析系统")
    st.divider()

    st.markdown("### 📊 系统概览")
    st.markdown(f"- **骗局套路库**：{len(kb)} 条")
    st.markdown(f"-  &nbsp;&nbsp;高危类型：{high_risk_count} 条")
    st.markdown(f"-  &nbsp;&nbsp;中危类型：{medium_risk_count} 条")
    if kb_vectors:
        st.markdown(f"- **检索引擎**：混合检索 ✓")
        st.caption(f"词典大小：{len(idf)} 词 · 余弦相似度匹配")
    else:
        st.markdown(f"- **检索引擎**：关键词匹配")
        st.caption("运行 build_vectors.py 升级语义检索")
    st.markdown(f"- **AI Agent**：5 个协作分析")

    st.divider()
    st.markdown("### 🤖 五 Agent 架构")
    agents = [
        ("📋", "编排Agent", "解析对话结构"),
        ("🎯", "话术识别Agent", "匹配诈骗套路"),
        ("⚖️", "交易合理性Agent", "判断交易合理性"),
        ("📜", "平台规则Agent", "检查是否违规"),
        ("👨‍⚖️", "仲裁Agent", "综合判定风险等级"),
    ]
    for icon, name, desc in agents:
        st.markdown(
            f'<div class="agent-step">'
            f'<div class="agent-icon" style="background: #e0e7ff; color: #4338ca;">{icon}</div>'
            f'<div><div style="font-weight: 600; font-size: 14px;">{name}</div>'
            f'<div style="font-size: 12px; color: #64748b;">{desc}</div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.divider()
    with st.expander("🔒 隐私说明"):
        st.write(
            "本工具不存储任何对话数据，分析完成后即丢弃，"
            "仅用于个人交易安全自查。分析过程中对话文本会发送至 AI 接口进行处理。"
        )

# ---------- 主内容区 ----------

# 示例对话快捷按钮
st.markdown("#### 💡 试试这些示例")
example_cols = st.columns(len(EXAMPLES))
for i, (label, text) in enumerate(EXAMPLES.items()):
    with example_cols[i]:
        if st.button(label, key=f"example_{i}", use_container_width=True):
            st.session_state["conversation_input"] = text

# 输入框
default_text = st.session_state.get("conversation_input", "")
conversation = st.text_area(
    "📝 粘贴交易对话",
    height=180,
    value=default_text,
    placeholder="A: 亲，这款还在吗\nB: 在的，走担保交易……\n\n把你和卖家/买家的聊天记录粘贴到这里，AI 会帮你分析是否存在诈骗风险。",
)

# 分析按钮
if st.button("🔍 开始智能分析", type="primary", use_container_width=True):
    if not conversation.strip():
        st.error("请先粘贴或选择一段交易对话。")
    else:
        with st.status("🤖 AI 正在分析，请稍候...", expanded=True) as status:
            try:
                st.write("📋 步骤 1/5：编排 Agent 解析对话结构...")
                # 直接调用 analyze，整个过程会串行执行
                result = analyze(conversation, kb, idf, kb_vectors)
                final = result["final"]
                status.update(label="✅ 分析完成！", state="complete", expanded=False)
            except Exception as e:
                status.update(label="❌ 分析失败", state="error", expanded=True)
                st.error(f"分析失败，请检查 API Key 或网络连接。（{e}）")
                st.stop()

        # ---- 风险判定 ----
        level = final.get("risk_level", "未知")
        color = RISK_COLOR.get(level, "#64748b")
        confidence = final.get("confidence", "?")

        st.markdown("### 🎯 风险判定")
        st.markdown(
            f'<div class="risk-card" style="background: linear-gradient(135deg, {color} 0%, {color}dd 100%);">'
            f'{level} · 置信度 {confidence}%</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="risk-sub">{final.get("reasoning", "")}</div>',
            unsafe_allow_html=True,
        )

        # ---- 第一建议 ----
        if final.get("top_action"):
            st.markdown(
                f'<div class="top-action">'
                f'<div style="font-weight: 700; color: #92400e; margin-bottom: 4px;">🎯 最重要的第一条建议</div>'
                f'<div style="color: #78350f; font-size: 15px;">{final["top_action"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # ---- 关键证据 ----
        st.markdown("### 📌 关键证据")
        key_evidence = final.get("key_evidence", [])
        if key_evidence:
            for ev in key_evidence:
                source = ev.get("source", "")
                text = ev.get("text", "")
                source_color = {
                    "话术": "#3b82f6",
                    "合理性": "#8b5cf6",
                    "平台规则": "#ef4444",
                }.get(source, "#64748b")
                st.markdown(
                    f'<div class="evidence-card" style="border-left-color: {source_color};">'
                    f'<div style="font-weight: 600; color: {source_color}; margin-bottom: 4px;">[{source}]</div>'
                    f'<div style="color: #1e293b; font-size: 14px; line-height: 1.6;">{text}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("暂无关键证据")

        # ---- 应对方案 ----
        st.markdown("### 🛠️ 应对方案")
        strategies = final.get("strategies", {}) or {}
        c1, c2, c3 = st.columns(3)

        with c1:
            safe = strategies.get("safe", {})
            st.markdown(
                f'<div class="strategy-card" style="background: #f0fdf4; border: 1px solid #bbf7d0;">'
                f'<div style="font-weight: 700; color: #166534; margin-bottom: 8px;">✅ 安全方案</div>'
                f'<div style="font-size: 13px; color: #15803d; line-height: 1.6;">'
                f'<b>该做：</b>{safe.get("do", "")}<br>'
                f'<b>别说：</b>{safe.get("say", "")}<br>'
                f'<b>不要做：</b>{safe.get("avoid", "")}'
                f'</div></div>',
                unsafe_allow_html=True,
            )

        with c2:
            probe = strategies.get("probe", {})
            st.markdown(
                f'<div class="strategy-card" style="background: #fffbeb; border: 1px solid #fde68a;">'
                f'<div style="font-weight: 700; color: #92400e; margin-bottom: 8px;">🔍 试探方案</div>'
                f'<div style="font-size: 13px; color: #b45309; line-height: 1.6;">'
                f'<b>该做：</b>{probe.get("do", "")}<br>'
                f'<b>可以说：</b>{probe.get("say", "")}<br>'
                f'<b>不要做：</b>{probe.get("avoid", "")}'
                f'</div></div>',
                unsafe_allow_html=True,
            )

        with c3:
            stop = strategies.get("stop", {})
            st.markdown(
                f'<div class="strategy-card" style="background: #fef2f2; border: 1px solid #fecaca;">'
                f'<div style="font-weight: 700; color: #991b1b; margin-bottom: 8px;">🛑 止损方案</div>'
                f'<div style="font-size: 13px; color: #b91c1c; line-height: 1.6;">'
                f'<b>该做：</b>{stop.get("do", "")}<br>'
                f'<b>该说：</b>{stop.get("say", "")}<br>'
                f'<b>绝对不要：</b>{stop.get("avoid", "")}'
                f'</div></div>',
                unsafe_allow_html=True,
            )

        # ---- Agent 详细分析 ----
        with st.expander("🔬 查看各 Agent 详细分析过程"):
            tab1, tab2, tab3, tab4 = st.tabs(
                ["📋 编排Agent", "🎯 话术识别Agent", "⚖️ 交易合理性Agent", "📜 平台规则Agent"]
            )
            with tab1:
                orch = result.get("orchestrator", {})
                st.markdown(f"**用户角色**：{orch.get('user_role', '未知')}")
                st.markdown(f"**对方角色**：{orch.get('counterparty_role', '未知')}")
                st.markdown(f"**交易摘要**：{orch.get('summary', '')}")
                ctx = orch.get("transaction_context", {})
                st.markdown(
                    f"**商品**：{ctx.get('product', '未知')} ｜ "
                    f"**价格**：{ctx.get('price', '未知')} ｜ "
                    f"**平台**：{ctx.get('platform', '未知')}"
                )
            with tab2:
                st.json(result.get("script", {}))
            with tab3:
                st.json(result.get("rationality", {}))
            with tab4:
                st.json(result.get("rule", {}))

# ---------- 底部说明 ----------
st.divider()
st.caption(
    "💡 提示：交易哨兵仅供参考，不能替代专业判断。"
    "遇到可疑交易请保持警惕，涉及财产损失请及时报警。"
)
