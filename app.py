import streamlit as st
from openai import OpenAI
import yfinance as yf
import pandas as pd
import os

# --- 1. 页面配置 ---
st.set_page_config(page_title="石油宏观分析助手", layout="wide")
st.title("🛢️ 石油价格与美国宏观经济影响分析")

# --- 2. 这里的 Key 改从 Streamlit 后台获取，不要在代码里写明文 ---
# 在 Streamlit Cloud 后台设置：DASHSCOPE_API_KEY = "你的sk-..."
api_key = st.secrets.get("DASHSCOPE_API_KEY")
base_url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

if not api_key:
    st.error("请先在 Streamlit Cloud 的 Secrets 中配置 DASHSCOPE_API_KEY")
    st.stop()

client = OpenAI(api_key=api_key, base_url=base_url)

# --- 3. 数据抓取逻辑 ---
@st.cache_data(ttl=3600) # 缓存1小时，避免频繁刷新被封IP
def get_oil_data():
    oil = yf.download("CL=F", period="1mo", interval="1d")
    # 修正：处理多级索引或Series的情况
    current_price = float(oil['Close'].iloc[-1])
    avg_5d = float(oil['Close'].tail(5).mean())
    return current_price, avg_5d, oil

# --- 4. 界面展示 ---
price, avg_5d, history = get_oil_data()

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📊 实时市场数据")
    st.metric("WTI原油最新价", f"${price:.2f}", f"5日均值: ${avg_5d:.2f}")
    st.line_chart(history['Close'])

with col2:
    st.subheader("🤖 AI 深度分析报告")
    
    prompt = f"""
    分析任务：石油价格对美国宏观经济的影响。
    当前数据：WTI原油最新价 ${price:.2f}，5日均价 ${avg_5d:.2f}。
    要求分析：
    1. 如果价格维持在95-100美元，对美国下期CPI的具体上行压力。
    2. 结合失业率和议息背景，分析对美联储加息/降息概率的传导（用百分比概率表达）。
    3. 给出石油股（如XLE）的情绪判断（买入/持有/卖出）。
    4. 预测美元走势。
    """

    if st.button("开始生成 AI 分析"):
        try:
            with st.spinner("正在调用阿里云模型进行深度分析..."):
                completion = client.chat.completions.create(
                    model="qwen-plus",
                    messages=[
                        {"role": "system", "content": "你是一位专业的全球宏观经济与大宗商品策略师。"},
                        {"role": "user", "content": prompt}
                    ]
                )
                st.success("分析完成！")
                st.markdown(completion.choices[0].message.content)
        except Exception as e:
            st.error(f"❌ 运行出错: {e}")

# --- 5. 补充说明 ---
st.divider()
st.caption("数据来源：Yahoo Finance | 模型驱动：阿里云百炼 (Qwen-Plus)")
