import requests
import re
import os

# 综合源
sources = {
    "Fanmingming_V6": "https://gh-proxy.phd.qzz.io/https://raw.githubusercontent.com/fanmingming/live/main/tv/m3u/ipv6.m3u",
    "YueChan_IPTV": "https://gh-proxy.phd.qzz.io/https://raw.githubusercontent.com/YueChan/Live/main/IPTV.m3u",
    "Guovern_Live": "https://gh-proxy.phd.qzz.io/https://raw.githubusercontent.com/Guovern/tv-list/main/m3u/live.m3u",
    "HK_Special": "https://gh-proxy.phd.qzz.io/https://raw.githubusercontent.com/Moexin/IPTV/master/HK.m3u"
}

# 关键词字典保持不变 (此处省略具体内容以节省篇幅，请沿用上个版本的 PROVINCES 字典)
PROVINCES = {
    "北京": ["北京", "京台", "BTV"],
    "上海": ["上海", "东方卫视", "哈哈炫动"],
    # ... 请在此处粘贴上个版本完整的 PROVINCES 字典内容 ...
}

def fetch_and_clean():
    all_channels = []
    seen_urls = set() # 仅用于 URL 去重，不用于频道名去重

    for name, url in sources.items():
        print(f"Fetching: {name}")
        try:
            r = requests.get(url, timeout=20)
            # 兼容更多格式的正则
            matches = re.findall(r'#EXTINF:.*?,(.*?)\n(http.*)', r.text)
            for channel_name, link in matches:
                link = link.strip()
                # 如果这个 URL 已经抓过了，就跳过；但如果是同名不同 URL，则保留
                if link in seen_urls: continue
                
                name_u = channel_name.strip().upper()
                is_ipv6 = "[" in link and "]" in link
                
                # 分类大脑
                group = "其他"
                if any(x in name_u for x in ["HK", "香港", "翡翠", "TVB", "凤凰", "澳门", "MO", "莲花"]):
                    group = "港澳电视"
                elif any(x in name_u for x in ["台湾", "TW", "中天", "年代", "TVBS"]):
                    group = "台湾电视"
                elif "CCTV" in name_u or "CGTN" in name_u:
                    group = "中央台"
                elif "卫视" in name_u:
                    group = "卫视"
                else:
                    found_prov = False
                    for prov, cities in PROVINCES.items():
                        if any(city in name_u for city in cities):
                            group = f"{prov}频道"
                            found_prov = True
                            break
                    if not found_prov and any(x in name_u for x in ["台", "频道", "广播"]):
                        group = "地方台"

                if group != "其他":
                    all_channels.append({
                        "name": channel_name.strip(), 
                        "url": link, 
                        "group": group, 
                        "v6": is_ipv6
                    })
                    seen_urls.add(link)
        except Exception as e:
            print(f"Error fetching {name}: {e}")

    # 排序：组 -> 频道名 -> IPv4优先
    # 这样相同的频道名就会排在一起
    all_channels.sort(key=lambda x: (
        {"中央台": 0, "卫视": 1, "港澳电视": 2, "台湾电视": 3}.get(x['group'], 10),
        x['group'],
        x['name'],
        1 if x['v6'] else 0
    ))

    # 路径处理
    prefix = "data/" if (os.path.exists("/.dockerenv") or os.environ.get("DOCKER_RUNTIME")) else ""
    if prefix: os.makedirs(prefix, exist_ok=True)

    # 写入文件
    with open(f"{prefix}cn_tw.txt", "w", encoding="utf-8") as f_txt, \
         open(f"{prefix}cn_tw.m3u", "w", encoding="utf-8") as f_m3u:
        f_m3u.write("#EXTM3U\n")
        curr_g = None
        for c in all_channels:
            if c['group'] != curr_g:
                curr_g = c['group']
                f_txt.write(f"{curr_g},#genre#\n")
            
            # 写入 TXT 格式 (TVBox 会自动聚合同名源)
            f_txt.write(f"{c['name']},{c['url']}\n")
            
            # 写入 M3U 格式 (增加标记方便识别)
            v6_tag = "[IPv6]" if c['v6'] else ""
            f_m3u.write(f'#EXTINF:-1 group-title="{c["group"]}",{c["name"]} {v6_tag}\n{c["url"]}\n')
            
    print(f"成功抓取 {len(all_channels)} 个链接！")

if __name__ == "__main__":
    fetch_and_clean()
