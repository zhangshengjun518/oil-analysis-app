import streamlit as st
import yfinance as yf
import pandas as pd
from openai import OpenAI

# --- 页面基础设置 ---
st.set_page_config(page_title="石油宏观经济看板", layout="wide")
st.title("🛢️ 石油价格、CPI 与宏观政策影响分析")

# --- 1. 核心配置：使用你提供的标准路径和模型名 ---
try:
    # 这里的 api_key 对应 Streamlit Cloud 里的 Secrets 变量名
    client = OpenAI(
        api_key=st.secrets["DASHSCOPE_API_KEY"],
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1" 
    )
    model_name = "qwen-plus" # 如果运行报错 404，可在此处临时改为 "qwen-turbo"
except Exception as e:
    st.error(f"初始化失败，请检查 Secrets 配置: {e}")
    st.stop()

# --- 2. 自动化获取金融数据 ---
@st.cache_data(ttl=3600)
def get_market_data():
    # 抓取原油期货(CL=F)和石油企业ETF(XLE)
    tickers = {"WTI原油": "CL=F", "石油企业(XLE)": "XLE"}
    data = {}
    for name, sym in tickers.items():
        df = yf.download(sym, period="1mo", interval="1d")
        data[name] = df
    return data

data_map = get_market_data()

# --- 3. UI 交互界面 ---
col_left, col_right = st.columns([3, 2])

with col_left:
    st.subheader("📊 实时行情监测")
    oil_df = data_map["WTI原油"]
    st.line_chart(oil_df['Close'])
    
    # 提取最新价和均价
    latest_price = float(oil_df['Close'].iloc[-1].iloc[0])
    avg_5d = float(oil_df['Close'].tail(5).mean().iloc[0])
    
    st.metric("WTI当前价格", f"${latest_price:.2f}", f"5日均价: ${avg_5d:.2f}")

with col_right:
    st.subheader("🤖 AI 宏观策略深度分析")
    
    # 构建专业 Prompt
    prompt = f"""
    作为宏观经济专家，请基于当前 WTI 原油价格 ${latest_price:.2f} 进行分析：
    1. 计算：若油价持续在 $95-$100 运行，对美国 CPI 同比数据的直接推升作用。
    2. 预测：结合 CPI 走势，预计美联储加息/降息概率的量化变化（百分比）。
    3. 情绪：针对石油股（XLE）给出“买入高涨”、“谨慎观望”等明确情绪判断。
    4. 收入：简述高油价对石油企业收入的影响逻辑。
    """

    if st.button("生成 AI 分析报告"):
        with st.spinner("正在连接通义千问进行深度计算..."):
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "你是一位精通全球流动性与宏观经济的首席分析师。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7
                )
                st.markdown("### 💡 分析结论：")
                st.info(response.choices[0].message.content)
            except Exception as e:
                st.error(f"分析请求失败: {e}")
                st.write("排查建议：请检查百炼后台是否‘立即开通’了 qwen-plus 模型，或尝试将代码中的 model_name 改为 qwen-turbo。")

# --- 4. 底部补充信息 ---
st.divider()
st.caption("注：本工具数据通过 yfinance 实时获取。分析结果由阿里云百炼 AI 生成，仅供参考，不作为投资建议。")
