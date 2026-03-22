import streamlit as st
from openai import OpenAI
import yfinance as yf
import pandas as pd

# --- 页面配置 ---
st.set_page_config(page_title="石油风险监控", layout="wide")
st.title("🛢️ 石油宏观风险研判 (Qwen 3.5 Plus)")

# --- 1. 配置 (建议在 Secrets 中设置以跳过手动输入) ---
api_key_input = st.sidebar.text_input("Aliyun API Key", type="password")
BASE_URL = "https://coding.dashscope.aliyuncs.com/v1" #

# --- 2. 增强型行情提取 ---
def get_clean_price():
    try:
        # 抓取原油数据
        df = yf.download("CL=F", period="5d", interval="1d", progress=False)
        if df.empty: return None
        
        # 针对新版 Pandas/yfinance 的多重兼容提取
        last_close = df['Close'].iloc[-1]
        
        # 尝试提取标量
        if hasattr(last_close, 'values'):
            return float(last_close.values[0])
        elif isinstance(last_close, (pd.Series, pd.DataFrame)):
            return float(last_close.iloc[0])
        else:
            return float(last_close)
    except Exception as e:
        st.sidebar.error(f"行情抓取失败: {e}")
        return None

# --- 3. 界面逻辑 ---
price = get_clean_price()

if price:
    st.sidebar.metric("WTI 现价", f"${price:.2f}")
    
    if st.button("🚀 执行 Qwen 3.5 Plus 深度研判"):
        if not api_key_input:
            st.error("请先在侧边栏填入 API Key")
        else:
            with st.spinner("正在分析宏观逻辑..."):
                try:
                    client = OpenAI(api_key=api_key_input, base_url=BASE_URL)
                    # 使用你指定的 qwen3.5-plus
                    response = client.chat.completions.create(
                        model="qwen3.5-plus", 
                        messages=[
                            {"role": "system", "content": "你是一位专注于全球流动性与大宗商品风险管理的专家。"},
                            {"role": "user", "content": f"当前WTI原油价格为 ${price:.2f}。请分析价格若维持在95-100美元对CPI的影响，并判断石油股情绪。"}
                        ]
                    )
                    st.success("研判完成")
                    st.markdown("### 💡 宏观分析报告")
                    st.info(response.choices[0].message.content)
                except Exception as e:
                    st.error(f"AI 调用出错: {e}")
else:
    st.warning("正在加载实时行情，请检查网络...")

# 底部说明
st.markdown("---")
st.caption("注：本系统使用阿里云百炼包月套餐专属通道。")
