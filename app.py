import streamlit as st
import yfinance as yf
import pandas as pd
import google.generativeai as genai

# --- 1. 配置 Gemini API (自动兼容方案) ---
def init_gemini():
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            st.error("❌ 请在 Streamlit Secrets 中配置 GEMINI_API_KEY")
            return None
        
        genai.configure(api_key=api_key)
        
        # 依次尝试不同的模型名称，解决 404 问题
        model_names = [
            'gemini-1.5-flash', 
            'gemini-1.5-flash-latest', 
            'gemini-1.5-pro', 
            'gemini-pro'
        ]
        
        for name in model_names:
            try:
                model = genai.GenerativeModel(name)
                # 尝试极简调用，验证模型是否可用
                model.generate_content("test", generation_config={"max_output_tokens": 1})
                return model
            except:
                continue
        
        st.error("❌ 尝试了所有模型名均返回 404，请检查 API Key 权限或地域限制。")
        return None
    except Exception as e:
        st.error(f"API 初始化异常: {e}")
        return None

model = init_gemini()

# --- 2. 页面设置 ---
st.set_page_config(page_title="石油宏观智能分析", layout="wide")
st.title("🛢️ 石油价格、CPI 与宏观政策联动分析")

# --- 3. 数据抓取 (修复 yfinance 多级索引) ---
@st.cache_data(ttl=3600)
def get_data():
    tickers = ["CL=F", "XLE", "DX-Y.NYB"]
    # 强制使用特定版本兼容的下载方式
    df = yf.download(tickers, period="1mo", interval="1d", group_by='ticker', auto_adjust=True)
    return df

try:
    raw_data = get_data()
    # 提取 WTI 价格
    wti_close = raw_data["CL=F"]['Close'].dropna()
    current_price = float(wti_close.iloc[-1])
    last_price = float(wti_close.iloc[-2])
    avg_5d = float(wti_close.tail(5).mean())
    
    # 提取 XLE 石油股
    xle_close = raw_data["XLE"]['Close'].dropna()
    current_xle = float(xle_close.iloc[-1])
except Exception as e:
    st.error(f"数据加载失败 (yfinance): {e}")
    st.stop()

# --- 4. 95-100美元逻辑判断 ---
is_high_risk = 95.0 <= current_price <= 100.0

# --- 5. UI 布局 ---
col_l, col_r = st.columns([2, 1])

with col_l:
    st.subheader("📈 市场走势图 (WTI)")
    st.line_chart(wti_close)
    
    m1, m2, m3 = st.columns(3)
    m1.metric("WTI 当前价", f"${current_price:.2f}", f"{current_price - last_price:.2f}")
    m2.metric("5日均价", f"${avg_5d:.2f}")
    
    if is_high_risk:
        st.warning("⚠️ 警报：油价进入 95-100 美元区间，CPI 压力极大！")
    else:
        st.success("🟢 价格目前处于常规波动区间。")

with col_r:
    st.subheader("🤖 Gemini 宏观策略报告")
    
    prompt = f"""
    分析背景：2026年宏观经济。
    当前数据：
    1. WTI原油：${current_price:.2f} (5日均价：${avg_5d:.2f})。
    2. 石油股 XLE：${current_xle:.2f}。
    3. 特殊逻辑：{"【紧急】油价处于95-100美元，将显著拉升下月CPI预期。" if is_high_risk else "油价波动平稳。"}
    
    请输出：
    - 【CPI影响】：对美国CPI的贡献度分析。
    - 【利率预测】：对美联储加息/降息概率的推演。
    - 【股价情绪】：明确给出“买入高涨”、“观望”或“减持”建议。
    - 【营收传导】：对石油企业收入的影响。
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
            st.warning("API 未就绪，请检查 Secrets 配置。")

# --- 6. 底部参考 ---
st.divider()
st.table(pd.DataFrame({
    "指标": ["WTI > $95", "WTI < $75", "美元加息", "美元降息"],
    "石油股情绪": ["买入高涨", "减持/观望", "利空情绪", "利好情绪"]
}))
