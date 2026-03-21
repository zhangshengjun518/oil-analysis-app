import streamlit as st
import yfinance as yf
import pandas as pd
from openai import OpenAI

# --- 1. 配置 阿里云百炼 API ---
def get_alibabacloud_client():
    # 请在 Streamlit Secrets 中配置名为 DASHSCOPE_API_KEY 的变量
    api_key = st.secrets.get("DASHSCOPE_API_KEY")
    if not api_key:
        return None
    
    # 阿里云百炼兼容 OpenAI 协议
    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    return client

# --- 2. 页面与数据逻辑 ---
st.set_page_config(page_title="石油宏观智能分析", layout="wide")
st.title("🛢️ 石油价格与美国宏观经济分析系统")

@st.cache_data(ttl=3600)
def fetch_market_data():
    # 抓取原油 (CL=F) 和 能源股 (XLE)
    data = yf.download(["CL=F", "XLE"], period="1mo", interval="1d", group_by='ticker', auto_adjust=True)
    return data

try:
    market_data = fetch_market_data()
    # 提取最新的数据点
    oil_price = float(market_data["CL=F"]['Close'].iloc[-1])
    oil_5d_avg = float(market_data["CL=F"]['Close'].tail(5).mean())
    xle_price = float(market_data["XLE"]['Close'].iloc[-1])
except Exception as e:
    st.error(f"数据获取失败: {e}")
    st.stop()

# --- 3. UI 展示与 95-100 美元逻辑 ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📈 市场行情走势")
    st.line_chart(market_data["CL=F"]['Close'])
    
    m1, m2, m3 = st.columns(3)
    m1.metric("WTI 当前价", f"${oil_price:.2f}")
    m2.metric("5日均价", f"${oil_5d_avg:.2f}")
    
    # 触发你要求的警报逻辑
    if 95.0 <= oil_price <= 100.0:
        st.error(f"🚨 状态：通胀高警 (当前油价 ${oil_price:.2f} 处于 95-100 敏感区间)")
    else:
        st.success("🟢 状态：波动正常")

with col2:
    st.subheader("🤖 通义千问 宏观策略分析")
    if st.button("生成 AI 深度分析报告"):
        client = get_alibabacloud_client()
        if not client:
            st.error("请先在 Secrets 中配置 DASHSCOPE_API_KEY")
        else:
            with st.spinner("百炼 AI 正在根据 2026 宏观模型推演..."):
                try:
                    # 使用百炼主流的 qwen-plus 或 qwen-max 模型
                    completion = client.chat.completions.create(
                        model="qwen-plus", 
                        messages=[
                            {"role": "system", "content": "你是一名资深宏观经济分析师，擅长通过原油价格推导 CPI 和美联储政策。"},
                            {"role": "user", "content": f"WTI原油当前价: ${oil_price:.2f}，5日均价: ${oil_5d_avg:.2f}，能源股XLE价格: ${xle_price:.2f}。请分析该价格对美国CPI的传导压力，并预测美联储的政策走向。"}
                        ],
                    )
                    st.markdown(completion.choices[0].message.content)
                except Exception as e:
                    st.error(f"分析失败: {e}")
