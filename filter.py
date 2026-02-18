import requests
import re
import os

# 综合源：涵盖 IPv6 精品流与大量 IPv4 地市流
# 使用更稳定的 mirror.ghproxy.com 镜像
sources = {
    "Heros_IPv4": "https://mirror.ghproxy.com/https://raw.githubusercontent.com/herosylee/iptv/main/live.m3u",
    "ITV_Local": "https://mirror.ghproxy.com/https://raw.githubusercontent.com/ssili126/tv/main/itvlist.m3u",
    "YueChan_IPTV": "https://mirror.ghproxy.com/https://raw.githubusercontent.com/YueChan/Live/main/IPTV.m3u",
    "Fanmingming_V6": "https://mirror.ghproxy.com/https://raw.githubusercontent.com/fanmingming/live/main/tv/m3u/ipv6.m3u",
    "Guovern_Live": "https://mirror.ghproxy.com/https://raw.githubusercontent.com/Guovern/tv-list/main/m3u/live.m3u",
    "HK_Special": "https://mirror.ghproxy.com/https://raw.githubusercontent.com/Moexin/IPTV/master/HK.m3u"
}

# 伪装 Header，防止请求被 GitHub 或源站拒绝
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def fetch_and_clean():
    all_channels = []
    seen_urls = set()
    
    # 1. 确定路径并强制创建 data 目录
    prefix = "data/" if (os.path.exists("/.dockerenv") or os.environ.get("DOCKER_RUNTIME")) else ""
    if prefix: 
        os.makedirs(prefix, exist_ok=True)
        print(f"检测到 Docker 环境，输出路径定为: {prefix}")

    # 2. 核心改动：立即生成/清空两个文件，防止 Nginx 报 404
    open(f"{prefix}cn_tw.txt", "w", encoding="utf-8").close()
    open(f"{prefix}tv_v4.txt", "w", encoding="utf-8").close()

    # 3. 开始抓取
    for name, url in sources.items():
        print(f"正在尝试抓取: {name}...")
        try:
            # 增加超时时间到 30 秒
            r = requests.get(url, headers=HEADERS, timeout=30)
            r.encoding = 'utf-8'
            
            if r.status_code != 200:
                print(f"抓取 {name} 失败，HTTP 状态码: {r.status_code}")
                continue

            # 正则提取频道名和 URL
            matches = re.findall(r'#EXTINF:.*?,(.*?)\n(http.*)', r.text)
            count = 0
            for channel_name, link in matches:
                link = link.strip()
                if link in seen_urls: 
                    continue
                
                name_u = channel_name.strip().upper()
                is_ipv6 = "[" in link and "]" in link
                
                # 分类逻辑
                group = "其他"
                if any(x in name_u for x in ["CCTV", "CGTN"]): group = "中央台"
                elif "卫视" in name_u: group = "卫视"
                elif any(x in name_u for x in ["香港", "HK", "翡翠", "凤凰", "澳门", "台湾", "TW"]): group = "港澳台"
                else: group = "地方台"

                all_channels.append({
                    "name": channel_name.strip(), 
                    "url": link, 
                    "group": group, 
                    "v6": is_ipv6
                })
                seen_urls.add(link)
                count += 1
            print(f"{name} 抓取成功，新增 {count} 条有效线路")
            
        except Exception as e:
            print(f"抓取 {name} 异常: {e}")

    if not all_channels:
        print("!!! 错误：未能从任何源抓取到数据，请检查网络环境 !!!")
        return

    # 4. 排序逻辑：组名 -> 频道名 -> IPv4 优先
    all_channels.sort(key=lambda x: (x['group'], x['name'], 1 if x['v6'] else 0))

    # 5. 写入文件
    print(f"准备写入文件，总线路数: {len(all_channels)}...")
    with open(f"{prefix}cn_tw.txt", "w", encoding="utf-8") as f_all, \
         open(f"{prefix}tv_v4.txt", "w", encoding="utf-8") as f_v4:
        
        curr_g_all, curr_g_v4 = None, None
        
        for c in all_channels:
            # 写入全量列表 (IPv4 + IPv6)
            if c['group'] != curr_g_all:
                curr_g_all = c['group']
                f_all.write(f"{curr_g_all},#genre#\n")
            f_all.write(f"{c['name']},{c['url']}\n")
            
            # 写入纯 IPv4 列表 (海信电视专用)
            if not c['v6']:
                if c['group'] != curr_g_v4:
                    curr_g_v4 = c['group']
                    f_v4.write(f"{curr_g_v4},#genre#\n")
                f_v4.write(f"{c['name']},{c['url']}\n")
            
    print(f"恭喜！所有列表已更新完毕。")
    print(f"全量列表：http://192.168.2.16:28024/cn_tw.txt")
    print(f"电视专用：http://192.168.2.16:28024/tv_v4.txt")

if __name__ == "__main__":
    fetch_and_clean()
