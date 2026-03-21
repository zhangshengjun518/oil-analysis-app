import streamlit as st
import yfinance as yf
import pandas as pd
import google.generativeai as genai
from datetime import datetime

# --- 1. 安全配置 API Key ---
# 建议通过 Streamlit Secrets 配置 GEMINI_API_KEY
# 如果你一定要直接写死在代码里（风险自担），请取消下面一行的注释并填入：
# API_KEY_VALUE = "你的_API_KEY" 
try:
    # 优先尝试从 Streamlit Secrets 获取
    api_key = st.secrets.get("GEMINI_API_KEY", "这里填入你的API_KEY(如果不走Secrets)")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
except Exception as e:
    st.error(f"❌ API 配置失败: {e}")

# --- 2. 页面美化设置 ---
st.set_page_config(page_title="石油-CPI宏观决策系统", layout="wide")
st.title("📊 石油价格与美国宏观经济分析系统")
st.markdown("---")

# --- 3. 数据抓取模块 ---
@st.cache_data(ttl=3600)
def fetch_financial_data():
    # 抓取 WTI原油 (CL=F), 能源ETF (XLE), 美元指数 (DX-Y.NYB)
    symbols = ["CL=F", "XLE", "DX-Y.NYB"]
    df = yf.download(symbols, period="1mo", interval="1d", group_by='ticker')
    return df

try:
    data_raw = fetch_financial_data()
    
    # 提取 WTI 价格
    wti_df = data_raw["CL=F"]['Close'].dropna()
    current_oil = float(wti_df.iloc[-1])
    prev_oil = float(wti_df.iloc[-2])
    avg_5d = float(wti_df.tail(5).mean())
    
    # 提取 XLE (石油股)
    xle_df = data_raw["XLE"]['Close'].dropna()
    current_xle = float(xle_df.iloc[-1])
    
except Exception as e:
    st.error(f"数据获取异常: {e}")
    st.stop()

# --- 4. 核心逻辑判断 (95-100美元区间) ---
is_alert_zone = 95.0 <= current_oil <= 100.0
price_status = "⚠️ 处于通胀敏感区间(95-100)" if is_alert_zone else "✅ 处于常规波动区间"

# --- 5. UI 布局 ---
col_l, col_r = st.columns([2, 1])

with col_l:
    st.subheader("📈 市场行情走势")
    st.line_chart(wti_df, y_label="WTI 原油价格 ($)")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("WTI 当前价", f"${current_oil:.2f}", f"{current_oil - prev_oil:.2f}")
    c2.metric("5日均价", f"${avg_5d:.2f}")
    c3.metric("状态", "通胀高警" if is_alert_zone else "正常", delta_color="inverse")

with col_r:
    st.subheader("🤖 Gemini 宏观策略分析")
    
    # 构建精准的 Prompt
    analysis_prompt = f"""
    你是资深宏观策略师。请根据以下2026年最新数据进行分析：
    1. 当前 WTI 原油价格: ${current_oil:.2f} (5日均价: ${avg_5d:.2f})。
    2. 石油公司(XLE)当前价: ${current_xle:.2f}。
    3. 特殊逻辑：{"当前油价已进入95-100美元的高危区间！" if is_alert_zone else "当前油价尚平稳。"}
    
    请输出以下分析报告：
    - 【CPI 影响预测】：油价此水平对下月美国CPI的直接贡献及通胀压力。
    - 【加息/降息概率】：基于油价引起的通胀预期，分析对美联储利率决策（加息还是降息）的影响概率。
    - 【股价情绪建议】：显示“买入高涨”、“观望”或“减持”，并说明理由。
    - 【石油企业收入】：高油价对能源企业财报的影响。
    """
    
    if st.button("生成 AI 深度分析报告"):
        with st.spinner("AI 正在解析宏观数据关联..."):
            try:
                response = model.generate_content(analysis_prompt)
                st.markdown(f"### 策略报告\n{response.text}")
            except Exception as e:
                st.error(f"AI 生成失败，请检查 Key 有效性: {e}")

# --- 6. 静态知识库（底部参考） ---
st.markdown("---")
with st.expander("📝 查看宏观指标传导逻辑参考"):
    st.table(pd.DataFrame({
        "指标": ["WTI > $95", "CPI 上涨", "美元加息", "美元降息"],
        "对石油股影响": ["买入高涨 (利润空间大)", "利空 (成本上升)", "利空 (分母效应)", "利好 (估值回升)"],
        "对宏观经济影响": ["推高通胀", "购买力下降", "抑制经济", "刺激增长"]
    }))
