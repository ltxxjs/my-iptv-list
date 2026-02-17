import requests
import re

# 配置：保留原始源并增加 index 源
sources = {
    "iptv-org_CN": "https://iptv-org.github.io/iptv/countries/cn.m3u",
    "iptv-org_TW": "https://iptv-org.github.io/iptv/countries/tw.m3u",
    "iptv-org_Index": "https://iptv-org.github.io/iptv/index.m3u", # 包含更多细碎地方台
    "Fanmingming": "https://raw.githubusercontent.com/fanmingming/live/main/tv/m3u/ipv6.m3u"
}

def fetch_and_clean():
    all_channels = []
    seen_urls = set()
    
    # 扩展地方台关键词库：增加常见地名和标识
    local_keywords = ["台", "频道", "广播", "电视", "苏州", "无锡", "南京", "常州", "浙江", "江苏"]

    for name, url in sources.items():
        print(f"正在抓取 {name}...")
        try:
            r = requests.get(url, timeout=20)
            content = r.text
            # 改进正则：兼容带双引号的频道名和复杂的 EXTINF 标签
            pattern = re.compile(r'#EXTINF:.*?,(.*?)\n(http.*)')
            matches = pattern.findall(content)
            
            for channel_name, link in matches:
                link = link.strip()
                if link in seen_urls: continue
                
                # 统一清理名称
                clean_name = channel_name.replace("中央电视台", "CCTV").replace('"', '').strip()
                
                group = "其他"
                # 1. 中央台判定
                if any(x in clean_name.upper() for x in ["CCTV", "CGTN", "风云"]):
                    group = "中央台"
                # 2. 台湾频道判定
                elif "TW" in name or any(x in clean_name for x in ["中视", "华视", "台视", "民视", "东森"]):
                    group = "台湾频道"
                # 3. 卫视判定
                elif "卫视" in clean_name:
                    group = "卫视"
                # 4. 地方台判定（核心改进：增加对拼音和特定城市的支持）
                elif any(x in clean_name for x in local_keywords) or "Suzhou" in clean_name:
                    group = "地方台"
                
                # 如果属于我们要的分类，则收录
                if group != "其他":
                    all_channels.append({"name": clean_name, "url": link, "group": group})
                    seen_urls.add(link)

        except Exception as e:
            print(f"抓取 {name} 失败: {e}")

    # 排序与写入（逻辑同前）
    sort_order = {"中央台": 0, "卫视": 1, "地方台": 2, "台湾频道": 3}
    all_channels.sort(key=lambda x: sort_order.get(x['group'], 99))

    # 写入 M3U 和 TXT...（代码省略，同上个版本）
    print(f"同步完成！已收录 {len(all_channels)} 个频道。")

if __name__ == "__main__":
    fetch_and_clean()
