import requests
import re
import os
import time

# 定义代理前缀，确保 GitHub 原始链接可访问
PROXY = "https://gh-proxy.phd.qzz.io/"

# 扩展源列表：包含专门的地方台聚合源
sources = {
    "IPTV_Org_CN": f"https://iptv-org.github.io/iptv/countries/cn.m3u?t={int(time.time())}",
    "IPTV_Org_HK": f"https://iptv-org.github.io/iptv/countries/hk.m3u?t={int(time.time())}",
    "IPTV_Org_TW": f"https://iptv-org.github.io/iptv/countries/tw.m3u?t={int(time.time())}",
    "YanG_Gather": f"{PROXY}https://raw.githubusercontent.com/YanG-1989/m3u/main/Gather.m3u",
    "Fanmingming": f"{PROXY}https://raw.githubusercontent.com/fanmingming/live/main/tv/m3u/ipv6.m3u",
    "Guovern_Live": f"{PROXY}https://raw.githubusercontent.com/Guovern/tv-list/main/m3u/live.m3u"
}

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

def get_group(name):
    n = name.upper()
    # 1. 中央台
    if any(x in n for x in ["CCTV", "CGTN", "中央"]): return "中央台"
    # 2. 卫视
    if "卫视" in n: return "卫视"
    # 3. 港澳台
    if any(x in n for x in ["香港", "翡翠", "凤凰", "HK", "TVB", "澳门"]): return "港澳频道"
    if any(x in n for x in ["台湾", "TW", "东森", "中视", "三立"]): return "台湾频道"
    
    # 4. 补全 34 个省级行政区识别逻辑
    provinces = [
        "广东", "北京", "上海", "天津", "重庆", "河北", "山西", "辽宁", "吉林", "黑龙江",
        "江苏", "浙江", "安徽", "福建", "江西", "山东", "河南", "湖北", "湖南", "海南",
        "四川", "贵州", "云南", "陕西", "甘肃", "青海", "台湾", "内蒙古", "广西", "西藏",
        "宁夏", "新疆"
    ]
    for p in provinces:
        if p in n: return f"{p}频道"
        
    return "地方及其他"

def run():
    all_ch = []
    urls = set()

    for s_name, s_url in sources.items():
        print(f"正在同步: {s_name}...")
        try:
            r = requests.get(s_url, headers=HEADERS, timeout=30)
            r.encoding = 'utf-8'
            if r.status_code != 200: continue
            
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

    # 排序优先级：中央 > 卫视 > 港澳 > 台湾 > 各省频道
    group_order = {"中央台": 0, "卫视": 1, "港澳频道": 2, "台湾频道": 3}
    all_ch.sort(key=lambda x: (group_order.get(x['group'], 50), x['group'], x['name']))

    # 统一同步写入所有文本文件
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

    # 写入 M3U
    with open("cn_tw.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for c in all_ch:
            v6_tag = " (IPv6)" if c['v6'] else ""
            f.write(f'#EXTINF:-1 group-title="{c["group"]}",{c["name"]}{v6_tag}\n{c["url"]}\n')

    print(f"✨ 同步成功！共抓取到 {len(all_ch)} 个频道，已按省份补全分类。")

if __name__ == "__main__":
    run()
