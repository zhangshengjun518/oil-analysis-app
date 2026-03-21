import streamlit as st
import yfinance as yf
import pandas as pd
import google.generativeai as genai
from datetime import datetime, timedelta

# --- 配置 Gemini API ---
# 在 Streamlit Cloud 中，请在 Settings -> Secrets 中添加 GEMINI_API_KEY
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=AIzaSyDuSpTdovgIq3EzSFnzmlDFK3EQ1pSAgzs)
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("请先在 Streamlit Secrets 或环境变量中配置 GEMINI_API_KEY")

# --- 页面设置 ---
st.set_page_config(page_title="石油与宏观经济分析助手", layout="wide")
st.title("🛢️ 石油价格、CPI 与宏观政策影响分析")

# --- 1. 数据获取模块 ---
@st.cache_data(ttl=3600)
def get_market_data():
    # 获取 WTI 原油 (CL=F), 标普500能源板块 (XLE), 美元指数 (DX-Y.NYB)
    tickers = {"WTI原油": "CL=F", "石油企业(XLE)": "XLE", "美元指数": "DX-Y.NYB"}
    data = {}
    for name, symbol in tickers.items():
        df = yf.download(symbol, period="1mo", interval="1d")
        data[name] = df
    return data

data = get_market_data()

# --- 2. 宏观逻辑计算 (模拟 CPI & 议息) ---
# 假设逻辑：油价维持在 95-100 美元超过 5 天，CPI 上行压力增加 0.5%
current_oil_price = data["WTI原油"]['Close'].iloc[-1].values[0]
avg_oil_5d = data["WTI原油"]['Close'].tail(5).mean().values[0]

# --- 3. UI 布局与分析 ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("实时行情可视化")
    st.line_chart(data["WTI原油"]['Close'], y_label="WTI Price ($)")
    st.metric("当前 WTI 价格", f"${current_oil_price:.2f}", 
              f"{current_oil_price - data['WTI原油']['Close'].iloc[-2].values[0]:.2f}")

with col2:
    st.subheader("🤖 Gemini 深度情感与宏观分析")
    
    # 构造 Prompt 给 Gemini
    prompt = f"""
    作为一名资深金融分析师，请根据以下数据进行分析：
    1. 当前 WTI 原油价格为 ${current_oil_price:.2f}，过去5天均价为 ${avg_oil_5d:.2f}。
    2. 石油企业 ETF (XLE) 当前走势反映了市场对能源股的情绪。
    3. 结合美国当前 2026 年的宏观背景（假设 CPI 公布在即）：
       - 如果油价持续维持在 $95-$100 左右，对下个月 CPI 数值的具体量化影响。
       - 对美联储加息或降息概率的影响（例如：通胀压力是否会推迟降息）。
       - 对石油公司收入及股价情绪的影响。
    
    请输出结果，包含：
    - 【情绪指标】：（例如：买入高涨 / 观望 / 恐慌）
    - 【详细分析】：石油价格波动对 CPI 和利率路径的传导逻辑。
    - 【投资建议】：针对能源股和美元走势的短期预测。
    """
    
    if st.button("开始 AI 智能分析"):
        with st.spinner("Gemini 正在分析宏观数据..."):
            response = model.generate_content(prompt)
            st.markdown(response.text)

# --- 4. 影响预测详情表 ---
st.divider()
st.subheader("宏观指标关联预测")
impact_df = pd.DataFrame({
    "场景": ["油价 > $95", "油价 $80-$90", "油价 < $75"],
    "CPI 预期影响": ["大幅上涨 (+0.6%)", "温和波动", "通胀回落"],
    "加息/降息概率": ["降息概率降低", "维持现状", "降息概率增加"],
    "石油股情绪": ["看涨 (收入预期增加)", "中性", "看跌 (利润率压缩)"]
})
st.table(impact_df)
