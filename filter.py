import requests
import re

# 配置：除了原始源，增加了国内主流的聚合源
sources = {
    "iptv-org_CN": "https://iptv-org.github.io/iptv/countries/cn.m3u",
    "iptv-org_TW": "https://iptv-org.github.io/iptv/countries/tw.m3u",
    "Fanmingming": "https://raw.githubusercontent.com/fanmingming/live/main/tv/m3u/ipv6.m3u",
    "YueChan": "https://raw.githubusercontent.com/YueChan/Live/main/IPTV.m3u"
}

def fetch_and_clean():
    all_channels = []
    seen_urls = set() # 用于去重
    
    for name, url in sources.items():
        print(f"正在抓取 {name}...")
        try:
            r = requests.get(url, timeout=15)
            content = r.text
            # 兼容多种 M3U 格式的正则
            pattern = re.compile(r'#EXTINF:.*?,(.*?)\n(http.*)')
            matches = pattern.findall(content)
            
            for channel_name, link in matches:
                link = link.strip()
                # 去重：如果 URL 已经存在，就不再添加
                if link in seen_urls:
                    continue
                
                # 统一名称：将“中央电视台”改为“CCTV”
                clean_name = channel_name.replace("中央电视台", "CCTV").strip()
                
                # 过滤出中国大陆和台湾相关的频道 (针对聚合源)
                # 如果是国内源，我们只需要包含特定关键词的频道，防止引入太多外国台
                group = "其他"
                if any(x in clean_name.upper() for x in ["CCTV", "CGTN", "风云"]):
                    group = "中央台"
                elif "卫视" in clean_name:
                    group = "卫视"
                elif any(x in clean_name for x in ["台", "频道", "广播", "电视"]):
                    group = "地方台"
                
                # 特别处理台湾频道标识 (针对混合源)
                if "TW" in name or any(x in clean_name for x in ["中视", "华视", "台视", "民视", "东森", "三立"]):
                    group = "台湾频道"

                # 只保留我们关心的分类，剔除无关的外国台
                if group != "其他":
                    all_channels.append({
                        "name": clean_name,
                        "url": link,
                        "group": group
                    })
                    seen_urls.add(link)

        except Exception as e:
            print(f"抓取 {name} 失败: {e}")

    # 排序逻辑
    sort_order = {"中央台": 0, "卫视": 1, "地方台": 2, "台湾频道": 3}
    all_channels.sort(key=lambda x: sort_order.get(x['group'], 99))

    # 1. 写入 M3U
    with open("cn_tw.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for c in all_channels:
            f.write(f'#EXTINF:-1 group-title="{c["group"]}",{c["name"]}\n')
            f.write(f'{c["url"]}\n')

    # 2. 写入 TXT
    with open("cn_tw.txt", "w", encoding="utf-8") as f:
        current_group = None
        for c in all_channels:
            if c['group'] != current_group:
                current_group = c['group']
                f.write(f"{current_group},#genre#\n")
            f.write(f"{c['name']},{c['url']}\n")
    
    print(f"处理完成！总计获得有效频道: {len(all_channels)} 个")

if __name__ == "__main__":
    fetch_and_clean()
