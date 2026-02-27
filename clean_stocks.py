import datetime
import time

import pandas as pd


def clean_my_excel():
    today = datetime.date.today().strftime("%Y%m%d")
    file_path = "A股全量行情_" + today + ".xlsx"
    print("🧹 正在开始最后的数据清洗...")

    # 读取数据，强制代码为字符串（防止掉0）
    df = pd.read_excel(file_path, dtype={'代码': str})

    # 1. 剔除重复项（防止断点续传产生的重复）
    df = df.drop_duplicates(subset=['代码'])

    # 2. 核心过滤逻辑：
    # 剔除代码以 1, 2, 5 开头的（债券、基金、B股）
    # 剔除名称含“退、债、转、期”的
    # df = df[~df['代码'].str.startswith(('1', '2', '5', '4'))]  # 剔除债券及非活跃三板
    # df = df[~df['名称'].str.contains('退|债|转|期|B|指数')]
    df = df[~df['名称'].str.contains('退')]

    # 3. 剔除成交额为0的（死票或已退市但接口残留的）
    df = df[df['成交额(亿)'] > 0]

    # 4. 排序：按成交额从大到小排（主力在哪里，机会就在哪里）
    df = df.sort_values(by='成交额(亿)', ascending=False)

    output_clean = "A股两会决策精英库" + today + ".xlsx"
    df.to_excel(output_clean, index=False)
    print(f"✨ 清洗完成！剩余 {len(df)} 支核心标的。")
    print(f"📂 纯净文件已生成：{output_clean}")


if __name__ == "__main__":
    clean_my_excel()
