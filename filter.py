import requests
import re
import os

# 1. 核心直播源（增加 IPv4 权重源）
sources = {
    "Heros_IPv4": "https://gh-proxy.phd.qzz.io/https://raw.githubusercontent.com/herosylee/iptv/main/live.m3u",
    "ITV_Local": "https://gh-proxy.phd.qzz.io/https://raw.githubusercontent.com/ssili126/tv/main/itvlist.m3u",
    "YueChan_IPTV": "https://gh-proxy.phd.qzz.io/https://raw.githubusercontent.com/YueChan/Live/main/IPTV.m3u",
    "Fanmingming_V6": "https://gh-proxy.phd.qzz.io/https://raw.githubusercontent.com/fanmingming/live/main/tv/m3u/ipv6.m3u",
    "Guovern_Live": "https://gh-proxy.phd.qzz.io/https://raw.githubusercontent.com/Guovern/tv-list/main/m3u/live.m3u",
    "HK_Special": "https://gh-proxy.phd.qzz.io/https://raw.githubusercontent.com/Moexin/IPTV/master/HK.m3u"
}

# 2. 全量地区分类字典
PROVINCES = {
    "北京": ["北京", "京台", "BTV"], "上海": ["上海", "东方卫视"], "广东": ["广东", "广州", "深圳", "珠海", "佛山", "东莞", "中山", "惠州"],
    "江苏": ["江苏", "南京", "苏州", "无锡", "常州"], "浙江": ["浙江", "杭州", "宁波", "温州"], "湖南": ["湖南", "长沙"],
    "湖北": ["湖北", "武汉"], "四川": ["四川", "成都"], "安徽": ["安徽", "合肥"], "福建": ["福建", "福州", "厦门"],
    "山东": ["山东", "济南", "青岛"], "河南": ["河南", "郑州"], "河北": ["河北", "石家庄"], "陕西": ["陕西", "西安"],
    "江西": ["江西", "南昌"], "辽宁": ["辽宁", "大连", "沈阳"], "广西": ["广西", "南宁", "桂林"], "贵州": ["贵州", "贵阳"],
    "云南": ["云南", "昆明"], "黑龙江": ["黑龙江", "哈尔滨"], "吉林": ["吉林", "长春"]
}

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

def fetch_and_clean():
    all_channels = []
    seen_urls = set()
    
    # 路径识别：GitHub Actions 环境下不使用 data 文件夹，本地运行（Docker）使用 data/
    is_github = os.environ.get('GITHUB_ACTIONS') == 'true'
    prefix = "" if is_github else "data/"
    
    if prefix and not os.path.exists(prefix):
        os.makedirs(prefix)
        print(f"创建本地目录: {prefix}")

    # 预先强制生成 3 个空文件防止 404
    for ext in ["cn_tw.m3u", "cn_tw.txt", "tv_v4.txt"]:
        open(f"{prefix}{ext}", "w", encoding="utf-8").close()

    for name, url in sources.items():
        print(f"正在抓取: {name}")
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            r.encoding = 'utf-8'
            if r.status_code != 200: continue
            
            matches = re.findall(r'#EXTINF:.*?,(.*?)\n(http.*)', r.text)
            for ch_name, link in matches:
                link = link.strip()
                if link in seen_urls: continue
                
                name_u = ch_name.strip().upper()
                is_ipv6 = "[" in link and "]" in link
                
                # 分类引擎
                group = "其他"
                if any(x in name_u for x in ["CCTV", "CGTN"]): group = "中央台"
                elif "卫视" in name_u: group = "卫视"
                elif any(x in name_u for x in ["香港", "HK", "TVB", "翡翠", "凤凰", "澳门", "台湾", "TW"]): group = "港澳台"
                else:
                    for prov, keywords in PROVINCES.items():
                        if any(k in name_u for k in keywords):
                            group = f"{prov}频道"
                            break
                    if group == "其他" and any(x in name_u for x in ["台", "频道", "广播"]): group = "地方台"

                all_channels.append({"name": ch_name.strip(), "url": link, "group": group, "v6": is_ipv6})
                seen_urls.add(link)
        except Exception as e:
            print(f"{name} 抓取异常: {e}")

    # 排序逻辑：权重 -> 组名 -> IPv4优先
    group_order = {"中央台": 0, "卫视": 1, "港澳台": 2}
    all_channels.sort(key=lambda x: (group_order.get(x['group'], 10), x['group'], x['name'], 1 if x['v6'] else 0))

    # --- 写入文件 ---
    print(f"准备写入文件，共 {len(all_channels)} 条线路")
    with open(f"{prefix}cn_tw.m3u", "w", encoding="utf-8") as f_m3u, \
         open(f"{prefix}cn_tw.txt", "w", encoding="utf-8") as f_txt, \
         open(f"{prefix}tv_v4.txt", "w", encoding="utf-8") as f_v4:
        
        f_m3u.write("#EXTM3U\n")
        curr_g_txt, curr_g_v4 = None, None
        
        for c in all_channels:
            # 1. 写入 M3U (全量)
            f_m3u.write(f'#EXTINF:-1 group-title="{c["group"]}",{c["name"]}\n{c["url"]}\n')
            
            # 2. 写入 TXT (全量)
            if c['group'] != curr_g_txt:
                curr_g_txt = c['group']
                f_txt.write(f"{curr_g_txt},#genre#\n")
            f_txt.write(f"{c['name']},{c['url']}\n")
            
            # 3. 写入 TXT (纯 IPv4)
            if not c['v6']:
                if c['group'] != curr_g_v4:
                    curr_g_v4 = c['group']
                    f_v4.write(f"{curr_g_v4},#genre#\n")
                f_v4.write(f"{c['name']},{c['url']}\n")

    print(f"✨ 同步成功！GitHub 环境: {is_github}")

if __name__ == "__main__":
    fetch_and_clean()
