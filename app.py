import streamlit as st
import yfinance as yf
import pandas as pd
import google.generativeai as genai

# --- 1. 配置 Gemini API ---
# 解决 404 错误的关键：使用多种备选模型名称
def init_gemini():
    try:
        # 从 Streamlit Secrets 获取 Key
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            st.error("❌ 未找到 API Key。请在 Streamlit Cloud 的 Settings -> Secrets 中配置 GEMINI_API_KEY。")
            return None
        
        genai.configure(api_key=api_key)
        
        # 尝试使用最兼容的名称：gemini-1.5-flash-latest
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        return model
    except Exception as e:
        st.error(f"API 配置异常: {e}")
        return None

model = init_gemini()

# --- 2. 页面设置 ---
st.set_page_config(page_title="石油宏观智能分析", layout="wide")
st.title("🛢️ 石油价格、CPI 与宏观政策联动分析")

# --- 3. 数据抓取 (处理多级索引问题) ---
@st.cache_data(ttl=3600)
def get_data():
    # 抓取原油 (CL=F)、能源股 (XLE)、美元指数 (DX-Y.NYB)
    tickers = ["CL=F", "XLE", "DX-Y.NYB"]
    df = yf.download(tickers, period="1mo", interval="1d", group_by='ticker')
    return df

try:
    raw_data = get_data()
    # 提取 WTI 价格数据
    wti_close = raw_data["CL=F"]['Close'].dropna()
    current_price = float(wti_close.iloc[-1])
    last_price = float(wti_close.iloc[-2])
    avg_5d = float(wti_close.tail(5).mean())
    
    # 提取能源股 XLE 数据
    xle_close = raw_data["XLE"]['Close'].dropna()
    current_xle = float(xle_close.iloc[-1])
except Exception as e:
    st.error(f"数据加载失败: {e}")
    st.stop()

# --- 4. 核心逻辑：95-100美元区间判断 ---
is_high_risk = 95.0 <= current_price <= 100.0

# --- 5. UI 布局 ---
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("📈 市场走势图")
    st.line_chart(wti_close)
    
    m1, m2, m3 = st.columns(3)
    m1.metric("WTI 当前价", f"${current_price:.2f}", f"{current_price - last_price:.2f}")
    m2.metric("5日均价", f"${avg_5d:.2f}")
    
    # 状态显示
    if is_high_risk:
        st.warning("⚠️ 当前油价处于 95-100 美元区间，通胀风险极高！")
    else:
        st.success("🟢 当前价格波动处于常规区间。")

with col_right:
    st.subheader("🤖 Gemini 宏观决策分析")
    
    # 编写 Prompt
    prompt = f"""
    分析背景：2026年宏观经济环境。
    当前数据：
    1. WTI原油价格：${current_price:.2f}（5日均价：${avg_5d:.2f}）。
    2. 石油股 XLE 价格：${current_xle:.2f}。
    3. 特殊警报：{"【重要】油价已进入95-100美元高位区间，直接威胁CPI目标。" if is_high_risk else "油价目前波动尚在可控范围。"}
    
    请输出以下分析内容：
    - 【CPI 影响预测】：预测此油价对下月美国 CPI 数值的贡献度。
    - 【加息/降息概率】：基于油价引起的通胀预期，推演美联储下一次会议的加息或降息概率变化。
    - 【股价情绪建议】：明确给出“买入高涨”、“观望”或“减持”的标签，并解释原因。
    - 【企业收益】：高油价对能源企业营收和利润率的传导逻辑。
    """
    
    if st.button("生成 AI 深度分析报告"):
        if model:
            with st.spinner("AI 正在根据全球宏观模型计算..."):
                try:
                    response = model.generate_content(prompt)
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"AI 生成失败: {e}")
        else:
            st.warning("请先配置有效的 API Key。")

# --- 6. 逻辑传导参考表 ---
st.divider()
st.subheader("📊 宏观指标传导逻辑参考")
ref_df = pd.DataFrame({
    "油价水平": ["<$75", "$80-$90", "$95-$100", ">$110"],
    "CPI 预测": ["回落", "稳定", "显著上升", "极度通胀"],
    "政策预期": ["降息概率大", "维持利率", "暂停降息/加息", "激进加息"],
    "能源股情绪": ["中性/减持", "中性", "买入高涨", "高位获利结清"]
})
st.table(ref_df)
