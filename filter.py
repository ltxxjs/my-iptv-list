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
        response = requests.head(channel['url'], timeout=10, allow_redirects=True)
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
            pattern = re.compile(r'#EXTINF:(.*),(.*)\n(http.*)')
            matches = pattern.findall(content)
            
            for info, name, link in matches:
                # 1. 统一名称替换
                clean_name = name.replace("中央电视台", "CCTV").strip()
                
                # 2. 精细分类逻辑
                group = "其他"
                if region == "台湾地区":
                    group = "台湾频道"
                elif "CCTV" in clean_name:
                    group = "中央台"
                elif "卫视" in clean_name:
                    group = "卫视"
                elif region == "中国大陆":
                    group = "地方台"
                
                all_channels.append({
                    "name": clean_name,
                    "url": link.strip(),
                    "group": group
                })
        except Exception as e:
            print(f"抓取 {region} 失败: {e}")

    # 直接跳过检测，使用所有抓取到的频道
valid_channels = all_channels

    # 4. 排序逻辑
    sort_order = {"中央台": 0, "卫视": 1, "地方台": 2, "台湾频道": 3, "其他": 4}
    valid_channels.sort(key=lambda x: sort_order.get(x['group'], 99))

    # 5.1 写入 M3U 格式文件
    with open("cn_tw.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for c in valid_channels:
            f.write(f'#EXTINF:-1 group-title="{c["group"]}",{c["name"]}\n')
            f.write(f'{c["url"]}\n')

    # 5.2 写入 TXT 格式文件 (增加分类标题)
    with open("cn_tw.txt", "w", encoding="utf-8") as f:
        current_group = None
        for c in valid_channels:
            # 当分类改变时，写入分类标题行（这是部分播放器的标准）
            if c['group'] != current_group:
                current_group = c['group']
                f.write(f"{current_group},#genre#\n")
            f.write(f"{c['name']},{c['url']}\n")
    
    print(f"处理完成！生成 cn_tw.m3u 和 cn_tw.txt")

if __name__ == "__main__":
    fetch_and_clean()
