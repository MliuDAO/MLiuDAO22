import streamlit as st
import pandas as pd
import requests

# --- 1. 配置区域 ---
# 这里是你截图里想要监控的ETF代码列表
TARGET_ETF_LIST = [
    "510320",
    "510380",
    "510370",
    "510360",
    "510350",
    "510330",
    "510310",
    "510300",
]

# --- 2. 页面配置 ---
st.set_page_config(page_title="沪深300 ETF 重点监控", layout="centered")
st.title("🎯 沪深300 ETF ")

# --- 3. 核心数据获取函数 (使用新浪财经接口) ---
def get_target_etf_data(codes):
    """
    直接从新浪财经接口获取指定代码的实时数据
    """
    # 拼接代码字符串，例如：sh510300,sz159919
    # ETF通常以 51 开头是上海(sh)，15 开头是深圳(sz)
    code_params = ""
    for code in codes:
        if code.startswith("51"):
            code_params += f"sh{code},"
        else:
            code_params += f"sz{code},"

    # 新浪财经实时行情接口
    url = f"https://hq.sinajs.cn/list={code_params}"

    headers = {
        "Referer": "https://finance.sina.com.cn",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'gbk'  # 新浪接口返回的是GBK编码

        data_list = []

        # 解析返回的文本数据
        lines = response.text.split(';')
        for line in lines:
            if not line.strip():
                continue

            # 每一行数据格式如：var hq_str_sh510300="名称,开盘,昨收,当前,最高,最低,日期,时间,...";
            if "=" in line:
                parts = line.split('="')
                if len(parts) < 2:
                    continue

                code_raw = parts[0].split('_')[-1] # 获取 sh510300
                data_str = parts[1].replace('";', '').split(',')

                if len(data_str) > 3:
                    name = data_str[0]
                    current_price = data_str[3]
                    open_price = data_str[1]
                    yesterday_close = data_str[2]
                    high = data_str[4]
                    low = data_str[5]
                    date = data_str[30]
                    time = data_str[31]

                    # 计算涨跌幅
                    try:
                        change_pct = (float(current_price) - float(yesterday_close)) / float(yesterday_close) * 100
                    except:
                        change_pct = 0

                    data_list.append({
                        "代码": code_raw.upper(),
                        "名称": name,
                        "当前价": current_price,
                        "涨跌幅(%)": f"{change_pct:.2f}",
                        "今开": open_price,
                        "昨收": yesterday_close,
                        "最高": high,
                        "最低": low,
                        "时间": f"{date} {time}"
                    })

        if not data_list:
            st.warning("接口返回了数据，但解析失败。可能是接口暂时不可用。")
            return None

        return pd.DataFrame(data_list)

    except Exception as e:
        st.error(f"发生网络错误：{e}")
        return None

# --- 4. 主程序界面 ---
if st.button("开始抓取最新数据"):
    with st.spinner('正在连接新浪行情中心...'):
        df = get_target_etf_data(TARGET_ETF_LIST)

        if df is not None and not df.empty:
            st.success("数据抓取成功！")
            # 重新排列列的顺序，让界面更好看
            df = df[["代码", "名称", "当前价", "涨跌幅(%)", "今开", "昨收", "最高", "最低", "时间"]]
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("未获取到有效数据。请稍后再试，或者检查网络连接。")
