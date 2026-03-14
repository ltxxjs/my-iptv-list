import requests
import re
import os

# 1. 明确定义 PROXY 变量，修复截图中的 NameError 报错
PROXY = "https://gh-proxy.phd.qzz.io/"

# 2. 核心数据源：IPTV-Org 官方源 (大陆/香港/台湾) + 优质补充源
sources = {
    "IPTV_Org_CN": "https://iptv-org.github.io/iptv/countries/cn.m3u",
    "IPTV_Org_HK": "https://iptv-org.github.io/iptv/countries/hk.m3u",
    "IPTV_Org_TW": "https://iptv-org.github.io/iptv/countries/tw.m3u",
    "YanG_Gather": f"{PROXY}https://raw.githubusercontent.com/YanG-1989/m3u/main/Gather.m3u",
    "Guovern_Live": f"{PROXY}https://raw.githubusercontent.com/Guovern/tv-list/main/m3u/live.m3u"
}

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

def get_group(name):
    n = name.upper()
    if any(x in n for x in ["CCTV", "CGTN", "中央"]): return "中央台"
    if "卫视" in n: return "卫视"
    if any(x in n for x in ["香港", "翡翠", "凤凰", "HK", "TVB"]): return "香港频道"
    if any(x in n for x in ["台湾", "TW", "东森", "中视", "三立"]): return "台湾频道"
    # 自动识别省份
    provinces = ["广东", "北京", "上海", "湖南", "浙江", "江苏", "四川", "湖北", "山东", "福建"]
    for p in provinces:
        if p in n: return f"{p}频道"
    return "地方及其他"

def run():
    all_ch = []
    urls = set()

    for s_name, s_url in sources.items():
        print(f"正在抓取: {s_name}...")
        try:
            r = requests.get(s_url, headers=HEADERS, timeout=30)
            r.encoding = 'utf-8'
            if r.status_code != 200: continue
            
            # 使用宽容模式正则，抓取所有有效链接
            items = re.findall(r'#EXTINF:.*?,(.*?)\n(http.*?)(?:\n|$)', r.text, re.DOTALL)
            
            for name, link in items:
                link = link.strip().split('\n')[0].strip()
                if link in urls or not link.startswith("http"): continue
                
                name_clean = name.strip()
                group = get_group(name_clean)
                all_ch.append({"name": name_clean, "url": link, "group": group, "v6": "[" in link})
                urls.add(link)
        except Exception as e:
            print(f"源 {s_name} 抓取跳过: {e}")

    # 排序逻辑
    group_order = {"中央台": 0, "卫视": 1, "香港频道": 2, "台湾频道": 3}
    all_ch.sort(key=lambda x: (group_order.get(x['group'], 50), x['group'], x['name']))

    # --- 统一同步写入所有文本文件 ---
    # 只要后缀是 .txt，你要求的 git add *.txt 就能全部抓到
    target_files = ["cn_tw.txt", "tv_all.txt", "tv_v4.txt"]
    for fname in target_files:
        with open(fname, "w", encoding="utf-8") as f:
            curr_g = None
            for c in all_ch:
                if c['group'] != curr_g:
                    curr_g = c['group']
                    f.write(f"{curr_g},#genre#\n")
                v6_tag = " (IPv6)" if c['v6'] else ""
                f.write(f"{c['name']}{v6_tag},{c['url']}\n")

    # --- 写入 M3U 文件 ---
    with open("cn_tw.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for c in all_ch:
            v6_tag = " (IPv6)" if c['v6'] else ""
            f.write(f'#EXTINF:-1 group-title="{c["group"]}",{c["name"]}{v6_tag}\n{c["url"]}\n')

    print(f"✨ 处理完成！共抓取 {len(all_ch)} 个频道链接。")

if __name__ == "__main__":
    run()
