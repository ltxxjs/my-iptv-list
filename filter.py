import requests
import re

# 整合了四个强力源，确保覆盖苏州等地方台
sources = {
    "iptv-org_CN": "https://iptv-org.github.io/iptv/countries/cn.m3u",
    "iptv-org_Index": "https://iptv-org.github.io/iptv/index.m3u",
    "Fanmingming": "https://raw.githubusercontent.com/fanmingming/live/main/tv/m3u/ipv6.m3u",
    "YueChan": "https://raw.githubusercontent.com/YueChan/Live/main/IPTV.m3u"
}

def fetch_and_clean():
    all_channels = []
    seen_urls = set()
    # 强化苏州、江苏区域关键词搜索
    local_keywords = ["苏州", "Suzhou", "江苏", "Jiangsu", "南京", "无锡", "常州"]

    for name, url in sources.items():
        try:
            r = requests.get(url, timeout=30)
            pattern = re.compile(r'#EXTINF:.*?,(.*?)\n(http.*)')
            matches = pattern.findall(r.text)
            
            for channel_name, link in matches:
                link = link.strip()
                if link in seen_urls: continue
                
                clean_name = channel_name.replace("中央电视台", "CCTV").replace('"', '').strip()
                group = "其他"
                
                if any(x in clean_name.upper() for x in ["CCTV", "CGTN"]):
                    group = "中央台"
                elif "卫视" in clean_name:
                    group = "卫视"
                elif any(x.lower() in clean_name.lower() for x in local_keywords):
                    group = "地方台"
                elif any(x in clean_name for x in ["台", "频道", "广播"]):
                    group = "地方台"
                
                if group != "其他":
                    all_channels.append({"name": clean_name, "url": link, "group": group})
                    seen_urls.add(link)
        except:
            pass

    # 排序：中央台 > 卫视 > 地方台
    sort_order = {"中央台": 0, "卫视": 1, "地方台": 2}
    all_channels.sort(key=lambda x: sort_order.get(x['group'], 99))

    # 同时写两个文件输出
    with open("cn_tw.txt", "w", encoding="utf-8") as f_txt, open("cn_tw.m3u", "w", encoding="utf-8") as f_m3u:
        f_m3u.write("#EXTM3U\n")
        curr_g = None
        for c in all_channels:
            if c['group'] != curr_g:
                curr_g = c['group']
                f_txt.write(f"{curr_g},#genre#\n")
            f_txt.write(f"{c['name']},{c['url']}\n")
            f_m3u.write(f'#EXTINF:-1 group-title="{c["group"]}",{c["name"]}\n{c["url"]}\n')

if __name__ == "__main__":
    fetch_and_clean()
