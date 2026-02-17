import requests
import re

# 整合全球及国内最全的源
sources = {
    "iptv-org_CN": "https://iptv-org.github.io/iptv/countries/cn.m3u",
    "iptv-org_Index": "https://iptv-org.github.io/iptv/index.m3u",
    "Fanmingming": "https://raw.githubusercontent.com/fanmingming/live/main/tv/m3u/ipv6.m3u",
    "YueChan": "https://raw.githubusercontent.com/YueChan/Live/main/IPTV.m3u"
}

def fetch_and_clean():
    all_channels = []
    seen_urls = set()
    
    # 只要频道名包含这些词，且不属于央视/卫视，就全部归入“地方台”
    local_identifiers = ["台", "频道", "广播", "电视", "综合", "新闻", "公共", "影院", "生活", "交通", "纪实"]

    for name, url in sources.items():
        print(f"正在抓取源: {name}")
        try:
            r = requests.get(url, timeout=30)
            pattern = re.compile(r'#EXTINF:.*?,(.*?)\n(http.*)')
            matches = pattern.findall(r.text)
            
            for channel_name, link in matches:
                link = link.strip()
                if link in seen_urls: continue
                
                # 规范化频道名称
                clean_name = channel_name.replace("中央电视台", "CCTV").replace('"', '').strip()
                group = "其他"
                
                # 1. 中央台逻辑
                if any(x in clean_name.upper() for x in ["CCTV", "CGTN"]):
                    group = "中央台"
                # 2. 卫视逻辑
                elif "卫视" in clean_name:
                    group = "卫视"
                # 3. 台湾/港澳逻辑 (基于来源或特定名称)
                elif "TW" in name or any(x in clean_name for x in ["中视", "华视", "凤凰"]):
                    group = "其他台"
                # 4. 地方台全量抓取逻辑
                # 只要是中国大陆源里的，或者是名字里带地方特征的，全收录
                elif any(x in clean_name for x in local_identifiers) or name == "iptv-org_CN":
                    group = "地方台"
                
                if group != "其他":
                    all_channels.append({"name": clean_name, "url": link, "group": group})
                    seen_urls.add(link)
        except Exception as e:
            print(f"抓取 {name} 出错: {e}")

    # 排序：中央台 -> 卫视 -> 地方台
    sort_order = {"中央台": 0, "卫视": 1, "地方台": 2}
    all_channels.sort(key=lambda x: sort_order.get(x['group'], 99))

    # 同时写入 txt 和 m3u
    with open("cn_tw.txt", "w", encoding="utf-8") as f_txt, open("cn_tw.m3u", "w", encoding="utf-8") as f_m3u:
        f_m3u.write("#EXTM3U\n")
        curr_g = None
        for c in all_channels:
            if c['group'] != curr_g:
                curr_g = c['group']
                f_txt.write(f"{curr_g},#genre#\n")
            f_txt.write(f"{c['name']},{c['url']}\n")
            f_m3u.write(f'#EXTINF:-1 group-title="{c["group"]}",{c["name"]}\n{c["url"]}\n')
    
    print(f"处理完成！当前共收录 {len(all_channels)} 个频道。")

if __name__ == "__main__":
    fetch_and_clean()
