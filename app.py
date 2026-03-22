import streamlit as st
from openai import OpenAI
import yfinance as yf
import pandas as pd

# --- 页面配置 ---
st.set_page_config(page_title="石油宏观风险监控", layout="wide")
st.title("🛢️ 石油宏观风险策略研判 (Qwen 3.5)")

# --- 1. 核心配置 (建议在 Streamlit Cloud 的 Secrets 中设置) ---
# 为了安全，建议在 GitHub 部署后，在 Streamlit 后台设置环境变量
# 如果先测试，可以直接填入你的 Key
API_KEY = st.sidebar.text_input("输入阿里百炼 API Key", type="password")
BASE_URL = "https://coding.dashscope.aliyuncs.com/v1"

# --- 2. 数据抓取逻辑 ---
def get_oil_data():
    try:
        # 获取 WTI 原油数据 (CL=F)
        oil = yf.download("CL=F", period="1mo", interval="1d", progress=False)
        if oil.empty:
            return None, None
        
        # 【修复 Series 报错】：确保提取的是纯数值
        last_close = oil['Close'].iloc[-1]
        if isinstance(last_close, pd.Series):
            current_price = float(last_close.iloc[0])
        else:
            current_price = float(last_close)
            
        avg_5d = oil['Close'].tail(5).mean()
        if isinstance(avg_5d, pd.Series):
            avg_5d = float(avg_5d.iloc[0])
        else:
            avg_5d = float(avg_5d)
            
        return current_price, avg_5d
    except Exception as e:
        st.error(f"行情抓取失败: {e}")
        return None, None

# --- 3. 页面布局与逻辑 ---
if API_KEY:
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    
    col1, col2 = st.columns(2)
    price, avg_5d = get_oil_data()
    
    if price:
        with col1:
            st.metric("WTI 原油现价", f"${price:.2f}")
        with col2:
            st.metric("5日移动平均价", f"${avg_5d:.2f}")

        if st.button("生成深度研判报告"):
            with st.spinner("🚀 正在通过 Qwen 3.5 Plus 联机研判..."):
                try:
                    # 使用你指定的 qwen3.5-plus 模型
                    completion = client.chat.completions.create(
                        model="qwen3.5-plus",
                        messages=[
                            {"role": "system", "content": "你是一位专注于全球资本流向与风险管理的宏观策略师。"},
                            {"role": "user", "content": f"当前WTI原油价格为 ${price:.2f}。请分析价格若维持在95-100美元对CPI的影响，并判断石油股情绪（输出‘买入高涨’或‘谨慎观望’）。"}
                        ]
                    )
                    st.markdown("### 💡 宏观分析结论")
                    st.write(completion.choices[0].message.content)
                except Exception as e:
                    st.error(f"AI 调用失败: {e}")
    else:
        st.warning("未能获取到实时行情，请检查网络连接。")
else:
    st.info("请在左侧侧边栏输入你的阿里云百炼 API Key 以启动分析。")
