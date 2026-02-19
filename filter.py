import requests
import re
import os

# 1. 核心源：增加 IPv4 占比高的源，确保海信电视有台看
sources = {
    "Heros_IPv4": "https://mirror.ghproxy.com/https://raw.githubusercontent.com/herosylee/iptv/main/live.m3u",
    "ITV_Local": "https://mirror.ghproxy.com/https://raw.githubusercontent.com/ssili126/tv/main/itvlist.m3u",
    "YueChan_IPTV": "https://mirror.ghproxy.com/https://raw.githubusercontent.com/YueChan/Live/main/IPTV.m3u",
    "Fanmingming_V6": "https://mirror.ghproxy.com/https://raw.githubusercontent.com/fanmingming/live/main/tv/m3u/ipv6.m3u",
    "Guovern_Live": "https://mirror.ghproxy.com/https://raw.githubusercontent.com/Guovern/tv-list/main/m3u/live.m3u",
    "HK_Special": "https://mirror.ghproxy.com/https://raw.githubusercontent.com/Moexin/IPTV/master/HK.m3u"
}

# 2. 详细省份/地市字典
PROVINCES = {
    "北京": ["北京", "京台", "BTV"], "上海": ["上海", "东方卫视", "哈哈炫动"], "天津": ["天津"], "重庆": ["重庆"],
    "广东": ["广东", "广州", "深圳", "珠海", "汕头", "佛山", "韶关", "湛江", "肇庆", "江门", "茂名", "惠州", "梅州", "汕尾", "河源", "阳江", "清远", "东莞", "中山", "潮州", "揭阳", "云浮"],
    "江苏": ["江苏", "南京", "苏州", "无锡", "常州", "扬州", "南通", "泰州", "盐城", "淮安", "徐州", "连云港", "宿迁"],
    "浙江": ["浙江", "杭州", "宁波", "温州", "嘉兴", "湖州", "绍兴", "金华", "衢州", "舟山", "台州", "丽水"],
    "湖南": ["湖南", "长沙", "株洲", "湘潭", "衡阳", "邵阳", "岳阳", "常德", "张家界", "益阳", "郴州", "永州", "怀化", "娄底", "湘西"],
    "湖北": ["湖北", "武汉", "黄石", "十堰", "宜昌", "襄阳", "鄂州", "荆门", "孝感", "荆州", "黄冈", "咸宁", "随州", "恩施", "仙桃", "天门", "潜江"],
    "山东": ["山东", "济南", "青岛", "淄博", "枣庄", "东营", "烟台", "潍坊", "济宁", "泰安", "威海", "日照", "临沂", "德州", "聊城", "滨州", "菏泽"],
    "福建": ["福建", "福州", "厦门", "莆田", "三明", "泉州", "漳州", "南平", "龙岩", "宁德"],
    "河南": ["河南", "郑州", "开封", "洛阳", "平顶山", "安阳", "鹤壁", "新乡", "焦作", "濮阳", "许昌", "漯河", "三门峡", "南阳", "商丘", "信阳", "周口", "驻马店"],
    "河北": ["河北", "石家庄", "唐山", "秦皇岛", "邯郸", "邢台", "保定", "张家口", "承德", "沧州", "廊坊", "衡水"],
    "四川": ["四川", "成都", "自贡", "攀枝花", "泸州", "德阳", "绵阳", "广元", "遂宁", "内江", "乐山", "南充", "眉山", "宜宾", "广安", "达州", "雅安", "巴中", "资阳", "阿坝", "甘孜", "凉山"],
    "安徽": ["安徽", "合肥", "芜湖", "蚌埠", "淮南", "马鞍山", "淮北", "铜陵", "安庆", "黄山", "滁州", "阜阳", "宿州", "六安", "亳州", "池州", "宣城"]
    # ... 其余省份逻辑类似
}

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

def fetch_and_clean():
    all_channels = []
    seen_urls = set()
    
    # 路径处理：兼容本地与 Docker
    prefix = "data/" if (os.path.exists("/.dockerenv") or os.environ.get("DOCKER_RUNTIME")) else ""
    if prefix: os.makedirs(prefix, exist_ok=True)

    # 预先清空/生成文件，防止 Nginx 报 404
    for fname in ["cn_tw.txt", "tv_v4.txt", "cn_tw.m3u"]:
        open(f"{prefix}{fname}", "w").close()

    for name, url in sources.items():
        print(f"正在抓取: {name}...")
        try:
            r = requests.get(url, headers=HEADERS, timeout=25)
            r.encoding = 'utf-8'
            if r.status_code != 200: continue
            
            # 改进的正则，尝试适配更多 M3U 变体
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
                elif any(x in name_u for x in ["香港", "HK", "翡翠", "TVB", "凤凰", "澳门", "台湾", "TW"]): group = "港澳台"
                else:
                    for prov, cities in PROVINCES.items():
                        if any(city in name_u for city in cities):
                            group = f"{prov}频道"
                            break
                    if group == "其他" and any(x in name_u for x in ["台", "频道", "广播"]):
                        group = "地方台"

                if group != "其他":
                    all_channels.append({"name": ch_name.strip(), "url": link, "group": group, "v6": is_ipv6})
                    seen_urls.add(link)
        except Exception as e:
            print(f"抓取 {name} 失败: {e}")

    # 排序：中央台 > 卫视 > 港澳台 > 地区台 (IPv4 靠前)
    group_order = {"中央台": 0, "卫视": 1, "港澳台": 2}
    all_channels.sort(key=lambda x: (group_order.get(x['group'], 10), x['group'], x['name'], 1 if x['v6'] else 0))

    # --- 写入 3 个文件 ---
    print(f"开始写入文件，总频道数: {len(all_channels)}")
    
    with open(f"{prefix}cn_tw.txt", "w", encoding="utf-8") as f_txt, \
         open(f"{prefix}tv_v4.txt", "w", encoding="utf-8") as f_v4, \
         open(f"{prefix}cn_tw.m3u", "w", encoding="utf-8") as f_m3u:
        
        # M3U 文件头部
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
            
            # 3. 写入纯 IPv4 TXT (海信电视)
            if not c['v6']:
                if c['group'] != curr_g_v4:
                    curr_g_v4 = c['group']
                    f_v4.write(f"{curr_g_v4},#genre#\n")
                f_v4.write(f"{c['name']},{c['url']}\n")

    print("✨ 所有格式（M3U & TXT）均已同步更新完成！")

if __name__ == "__main__":
    fetch_and_clean()
