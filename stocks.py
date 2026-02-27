import datetime

import pandas as pd
import httpx
import time
import random
import os


# 💡 新增：防御性计算函数，防止停牌股或异常数据导致程序崩溃
def safe_math(value, divisor=100):
    try:
        # 尝试转换并计算
        return round(float(value) / divisor, 3)
    except (TypeError, ValueError):
        # 如果是 "-"、None 或其他非数字，返回 0
        return 0


def get_full_market_2026_resumable():
    today = datetime.date.today().strftime("%Y%m%d")
    output_file = "A股全量行情_" + today + ".xlsx"

    if os.path.exists(output_file):
        existing_df = pd.read_excel(output_file)
        all_data = existing_df.to_dict('records')
        start_page = (len(all_data) // 20) + 1
        print(f"🔄 恢复进度：已抓取 {len(all_data)} 支，将从第 {start_page} 页开始补全...")
    else:
        all_data = []
        start_page = 1
        print("🚀 开启全新抓取任务...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Referer": "https://quote.eastmoney.com/center/grid_list.html",
        "Cookie": "qgqp_b_id=7b369fd6632b2397df8431fe2f87aca6; st_pvi=80805563959579;",
        "Connection": "keep-alive"
    }

    with httpx.Client(headers=headers, http2=False, timeout=30.0, verify=False) as client:
        # 5339支 / 20支 ≈ 268页，跑扫到 300 页确保全覆盖
        for page in range(start_page, 300):
            url = "https://push2.eastmoney.com/api/qt/clist/get"
            params = {
                "np": "1", "fltt": "1", "invt": "2",
                "fs": "m:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23,m:0 t:81 s:2048",
                "fields": "f12,f14,f2,f3,f6,f8,f100,f102,f103",
                "fid": "f3",
                "pn": str(page),
                "pz": "20",
                "po": "1",
                "ut": "fa5fd1943c7b386f172d6893dbfba10b",
                "wbp2u": "|0|0|0|web",
                "_": str(int(time.time() * 1000))
            }

            try:
                wait = random.uniform(4.0, 7.0)
                time.sleep(wait)
                response = client.get(url, params=params)

                # 将原来的 res_json.get('data').get('diff') 替换为以下逻辑：
                if response.status_code == 200:
                    res_json = response.json()
                    data_obj = res_json.get('data')

                    # 💡 核心修复：如果 data 已经没了，说明真的抓完了，直接退出循环
                    if data_obj is None:
                        print(f"🏁 恭喜！已到达市场尽头。共抓取 {len(all_data)} 支标的。")
                        break

                    stocks = data_obj.get('diff', [])
                    if not stocks:
                        print("🏁 数据已抓取完毕！")
                        break

                    for s in stocks:
                        raw_code = str(s.get('f12', '')).strip()
                        formatted_code = raw_code.zfill(6)
                        name = str(s.get('f14', '')).strip()
                        # 1. 过滤债券：代码通常以 11、12、13 开头
                        # if raw_code.startswith(('11', '12', '13', '20')): continue
                        # 2. 过滤退市及债券关键词
                        # if any(k in name for k in ['退', '债', '转', '期', 'B']): continue
                        if any(k in name for k in ['退']): continue
                        # 3. 过滤特定北交所/三板（如需纯沪深主板可加）
                        # if raw_code.startswith(('4', '8')): continue
                        # 💡 核心改动：使用 safe_math 处理所有字段
                        all_data.append({
                            "代码": formatted_code,
                            "名称": name,
                            "行业板块": s.get('f100'),
                            "相关概念": f"{s.get('f102', '')}, {s.get('f103', '')}",
                            "现价": safe_math(s.get('f2')),
                            "涨幅%": safe_math(s.get('f3')),
                            "成交额(亿)": round(safe_math(s.get('f6'), 100000000), 2),
                            "换手%": safe_math(s.get('f8'))
                        })

                    # 实时保存进度
                    df_temp = pd.DataFrame(all_data)
                    df_temp.to_excel(output_file, index=False)
                    print(f"✅ 第 {page} 页成功 | 累计: {len(all_data)} 支 | 延迟: {round(wait, 1)}s")
                else:
                    print(f"⚠️ 响应异常 (码: {response.status_code})，建议重启热点换 IP。")
                    break
            except Exception as e:
                print(f"💥 捕获异常: {e}")
                print("💡 正在尝试保持当前进度... 请重启热点后再次点击运行。")
                break

    print(f"✨ 运行结束。数据已锁定在：{output_file}")


if __name__ == "__main__":
    get_full_market_2026_resumable()
