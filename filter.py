import requests
import re
import concurrent.futures

# 配置：需要抓取的源地址
sources = {
    "中国大陆": "https://iptv-org.github.io/iptv/countries/cn.m3u",
    "台湾地区": "https://iptv-org.github.io/iptv/countries/tw.m3u"
}

def check_url(channel):
    """检测链接是否可用 (超时时间设为3秒)"""
    try:
        # 使用 HEAD 请求节省流量
        response = requests.head(channel['url'], timeout=3, allow_redirects=True)
        if response.status_code == 200:
            return channel
    except:
        return None
    return None

def fetch_and_clean():
    all_channels = []
    
    for region, url in sources.items():
        print(f"正在抓取 {region}...")
        try:
            r = requests.get(url, timeout=10)
            content = r.text
            
            # 使用正则解析 M3U
            # 匹配 #EXTINF 和 URL
            pattern = re.compile(r'#EXTINF:(.*),(.*)\n(http.*)')
            matches = pattern.findall(content)
            
            for info, name, link in matches:
                # 1. 统一名称：将“中央电视台”改为“CCTV”
                clean_name = name.replace("中央电视台", "CCTV").strip()
                
                # 2. 自动打标签（分类）
                group = "其他"
                if "CCTV" in clean_name: group = "央视"
                elif "卫视" in clean_name: group = "卫视"
                elif region == "台湾地区": group = "台湾频道"
                
                all_channels.append({
                    "info": info,
                    "name": clean_name,
                    "url": link.strip(),
                    "group": group
                })
        except Exception as e:
            print(f"抓取 {region} 失败: {e}")

    # 3. 多线程检测死链 (开启20个并发线程)
    print(f"正在检测死链，总计 {len(all_channels)} 个频道...")
    valid_channels = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(check_url, all_channels))
        valid_channels = [c for c in results if c is not None]

    # 4. 按分类排序 (央视 -> 卫视 -> 台湾频道 -> 其他)
    sort_order = {"央视": 0, "卫视": 1, "台湾频道": 2, "其他": 3}
    valid_channels.sort(key=lambda x: sort_order.get(x['group'], 99))

    # 5. 写入文件
    with open("cn_tw.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for c in valid_channels:
            # 注入 group-title 标签供播放器分类
            f.write(f'#EXTINF:-1 group-title="{c["group"]}",{c["name"]}\n')
            f.write(f'{c["url"]}\n')
    
    print(f"同步完成！有效频道数量: {len(valid_channels)}")

if __name__ == "__main__":
    fetch_and_clean()
