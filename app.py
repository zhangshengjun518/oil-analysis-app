import streamlit as st
from openai import OpenAI
import yfinance as yf
import pandas as pd
from datetime import datetime

# --- 1. 页面配置 ---
st.set_page_config(
    page_title="石油宏观风险策略监控", 
    page_icon="🛢️",
    layout="wide"
)

st.title("🛢️ 石油宏观风险策略研判系统")
st.caption(f"当前运行环境时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# --- 2. 核心参数配置 ---
# 提示：建议在 Streamlit Cloud 后台 Settings -> Secrets 中配置 api_key 以实现自动登录
# 这里的 Base URL 对应你 Coding Plan 套餐的专属地址
API_KEY = st.sidebar.text_input("输入阿里云百炼 API Key", type="password")
BASE_URL = "https://coding.dashscope.aliyuncs.com/v1" 
TARGET_MODEL = "qwen3.5-plus" # 使用你指定的最新模型

# --- 3. 健壮的数据抓取函数 ---
def get_oil_market_data():
    try:
        # 获取 WTI 原油期货数据 (CL=F)
        oil = yf.download("CL=F", period="1mo", interval="1d", progress=False)
        if oil.empty:
            return None, None
        
        # 【修正点】：解决日志中出现的 FutureWarning
        # 显式使用 .iloc[-1] 并在 Series 情况下提取第一个元素
        last_close_val = oil['Close'].iloc[-1]
        if isinstance(last_close_val, pd.Series):
            current_price = float(last_close_val.iloc[0])
        else:
            current_price = float(last_close_val)
            
        # 计算5日均价，同样处理 Series 转换问题
        avg_5d_raw = oil['Close'].tail(5).mean()
        if isinstance(avg_5d_raw, pd.Series):
            avg_5d = float(avg_5d_raw.iloc[0])
        else:
            avg_5d = float(avg_5d_raw)
            
        return current_price, avg_5d
    except Exception as e:
        st.error(f"行情抓取失败: {e}")
        return None, None

# --- 4. 界面布局与交互 ---
if API_KEY:
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    
    # 侧边栏行情显示
    price, avg_5d = get_oil_market_data()
    
    if price:
        st.sidebar.markdown("### 实时行情 (WTI)")
        st.sidebar.metric("现价", f"${price:.2f}")
        st.sidebar.metric("5日均价", f"${avg_5d:.2f}")
        
        # 主界面分析逻辑
        st.info(f"已连接阿里云百炼专属通道，准备使用模型: {TARGET_MODEL}")
        
        if st.button("🚀 生成 Qwen 3.5 宏观研判报告"):
            with st.spinner("正在分析全球资本流向与通胀压力..."):
                try:
                    # 构建针对宏观风险管理的需求
                    prompt = f"""
                    分析任务：石油价格对美国宏观经济及风险资产的影响。
                    当前数据：WTI原油最新价 ${price:.2f}，5日均价 ${avg_5d:.2f}。
                    请作为首席宏观分析师给出研判：
                    1. 测算油价若维持在$95-$100区间，对下期CPI数据的边际推升作用。
                    2. 给出石油股(XLE)的情绪建议：输出“买入高涨”或“谨慎观望”。
                    3. 预测美元指数(DXY)在当前环境下的走势逻辑。
                    """
                    
                    completion = client.chat.completions.create(
                        model=TARGET_MODEL,
                        messages=[
                            {"role": "system", "content": "你是一位精通全球流动性与大宗商品风险管理的专家。"},
                            {"role": "user", "content": prompt}
                        ]
                    )
                    
                    st.markdown("---")
                    st.markdown("### 💡 宏观风险研判报告")
                    st.markdown(completion.choices[0].message.content)
                    
                except Exception as e:
                    st.error(f"AI 研判生成失败: {e}")
                    st.warning("请检查 API Key 权限或模型名称是否正确。")
    else:
        st.warning("未能获取实时行情，请刷新页面或检查网络。")
else:
    st.warning("🔑 请在左侧侧边栏输入 API Key 以启动系统。")
    st.markdown("""
    ### 使用说明
    1. **Key 获取**：登录阿里云百炼，获取 `sk-sp-` 开头的专属 Key。
    2. **环境要求**：确保你的 GitHub 仓库中包含 `requirements.txt`。
    3. **安全建议**：不要将 API Key 直接写在代码中提交。
    """)
