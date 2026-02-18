import requests
import re
import os

sources = {
    "iptv-org_CN": "https://iptv-org.github.io/iptv/countries/cn.m3u",
    "Fanmingming": "https://raw.githubusercontent.com/fanmingming/live/main/tv/m3u/ipv6.m3u",
    "YueChan": "https://raw.githubusercontent.com/YueChan/Live/main/IPTV.m3u"
}

def fetch_and_clean():
    all_channels = []
    seen_urls = set()
    local_keywords = ["台", "频道", "广播", "电视", "综合", "新闻", "公共", "生活"]

    for name, url in sources.items():
        try:
            r = requests.get(url, timeout=30)
            matches = re.findall(r'#EXTINF:.*?,(.*?)\n(http.*)', r.text)
            for channel_name, link in matches:
                link = link.strip()
                if link in seen_urls: continue
                clean_name = channel_name.replace("中央电视台", "CCTV").strip()
                is_ipv6 = "[" in link and "]" in link
                display_name = f"{clean_name} [IPv6]" if is_ipv6 else clean_name
                group = "其他"
                if "CCTV" in clean_name.upper(): group = "中央台"
                elif "卫视" in clean_name: group = "卫视"
                elif any(x in clean_name for x in local_keywords): group = "地方台"
                if group != "其他":
                    all_channels.append({"name": display_name, "url": link, "group": group, "v6": is_ipv6})
                    seen_urls.add(link)
        except: pass

    all_channels.sort(key=lambda x: ({"中央台":0,"卫视":1,"地方台":2}.get(x['group'],9), 1 if x['v6'] else 0))

    # --- 关键兼容性逻辑 ---
    # 如果是在 Docker 环境中，保存到 data/ 目录下；否则直接存在根目录
    if os.path.exists("/.dockerenv") or os.environ.get("DOCKER_RUNTIME"):
        os.makedirs("data", exist_ok=True)
        prefix = "data/"
    else:
        prefix = ""

    with open(f"{prefix}cn_tw.txt", "w", encoding="utf-8") as f_txt, \
         open(f"{prefix}cn_tw.m3u", "w", encoding="utf-8") as f_m3u:
        f_m3u.write("#EXTM3U\n")
        curr_g = None
        for c in all_channels:
            if c['group'] != curr_g:
                curr_g = c['group']
                f_txt.write(f"{curr_g},#genre#\n")
            f_txt.write(f"{c['name']},{c['url']}\n")
            f_m3u.write(f'#EXTINF:-1 group-title="{c["group"]}",{c["name"]}\n{c["url"]}\n')
    print(f"成功！文件已保存在: {prefix if prefix else '当前目录'}")

if __name__ == "__main__":
    fetch_and_clean()
