import requests
import re
import os

# 1. 恢复全球 + 国内综合源
sources = {
    # 全球核心源 (iptv-org)
    "IPTV_Org_Global": "https://iptv-org.github.io/iptv/index.m3u",
    "IPTV_Org_CN": "https://iptv-org.github.io/iptv/countries/cn.m3u",
    "IPTV_Org_HK": "https://iptv-org.github.io/iptv/countries/hk.m3u",
    "IPTV_Org_TW": "https://iptv-org.github.io/iptv/countries/tw.m3u",
    # 国内精品加速源
    "Heros_IPv4": "https://mirror.ghproxy.com/https://raw.githubusercontent.com/herosylee/iptv/main/live.m3u",
    "YueChan_IPTV": "https://mirror.ghproxy.com/https://raw.githubusercontent.com/YueChan/Live/main/IPTV.m3u",
    "Fanmingming_V6": "https://mirror.ghproxy.com/https://raw.githubusercontent.com/fanmingming/live/main/tv/m3u/ipv6.m3u"
}

# 2. 恢复详细的省份分类字典
PROVINCES = {
    "北京": ["北京", "京台", "BTV"], "上海": ["上海", "东方卫视"], "天津": ["天津"], "重庆": ["重庆"],
    "广东": ["广东", "广州", "深圳", "珠海", "汕头", "佛山", "韶关", "湛江", "肇庆", "江门", "茂名", "惠州", "梅州", "汕尾", "河源", "阳江", "清远", "东莞", "中山", "潮州", "揭阳", "云浮"],
    "江苏": ["江苏", "南京", "苏州", "无锡", "常州", "扬州", "南通", "泰州", "盐城", "淮安", "徐州", "连云港", "宿迁"],
    "浙江": ["浙江", "杭州", "宁波", "温州", "嘉兴", "湖州", "绍兴", "金华", "衢州", "舟山", "台州", "丽水"],
    "湖南": ["湖南", "长沙", "株洲", "湘潭", "衡阳", "邵阳", "岳阳", "常德", "张家界", "益阳", "郴州", "永州", "怀化", "娄底", "湘西"],
    "湖北": ["湖北", "武汉", "黄石", "十堰", "宜昌", "襄阳", "鄂州", "荆门", "孝感", "荆州", "黄冈", "咸宁", "随州", "恩施", "仙桃", "天门", "潜江"],
    "安徽": ["安徽", "合肥", "芜湖", "蚌埠", "淮南", "马鞍山", "淮北", "铜陵", "安庆", "黄山", "滁州", "阜阳", "宿州", "六安", "亳州", "池州", "宣城"],
    "山东": ["山东", "济南", "青岛", "淄博", "枣庄", "东营", "烟台", "潍坊", "济宁", "泰安", "威海", "日照", "临沂", "德州", "聊城", "滨州", "菏泽"],
    "福建": ["福建", "福州", "厦门", "莆田", "三明", "泉州", "漳州", "南平", "龙岩", "宁德"],
    "河南": ["河南", "郑州", "开封", "洛阳", "平顶山", "安阳", "鹤壁", "新乡", "焦作", "濮阳", "许昌", "漯河", "三门峡", "南阳", "商丘", "信阳", "周口", "驻马店"],
    "河北": ["河北", "石家庄", "唐山", "秦皇岛", "邯郸", "邢台", "保定", "张家口", "承德", "沧州", "廊坊", "衡水"],
    "四川": ["四川", "成都", "自贡", "攀枝花", "泸州", "德阳", "绵阳", "广元", "遂宁", "内江", "乐山", "南充", "眉山", "宜宾", "广安", "达州", "雅安", "巴中", "资阳", "阿坝", "甘孜", "凉山"],
    "江西": ["江西", "南昌", "景德镇", "萍乡", "九江", "新余", "鹰潭", "赣州", "吉安", "宜春", "抚州", "上饶"],
    "辽宁": ["辽宁", "沈阳", "大连", "鞍山", "抚顺", "本溪", "丹东", "锦州", "营口", "阜新", "辽阳", "盘锦", "铁岭", "朝阳", "葫芦岛"],
    "吉林": ["吉林", "长春", "四平", "辽源", "通化", "白山", "松原", "白城", "延边"],
    "黑龙江": ["黑龙江", "哈尔滨", "齐齐哈尔", "鸡西", "鹤岗", "双鸭山", "大庆", "伊春", "佳木斯", "七台河", "牡丹江", "黑河", "绥化", "大兴安岭"]
}

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

def fetch_and_clean():
    all_channels = []
    seen_urls = set()
    
    is_github = os.environ.get('GITHUB_ACTIONS') == 'true'
    prefix = "" if is_github else "data/"
    if prefix and not os.path.exists(prefix): os.makedirs(prefix)

    # 预初始化文件
    for ext in ["cn_tw.m3u", "cn_tw.txt", "tv_v4.txt"]:
        open(f"{prefix}{ext}", "w", encoding="utf-8").close()

    for name, url in sources.items():
        print(f"正在尝试拉取全球源: {name}...")
        try:
            r = requests.get(url, headers=HEADERS, timeout=40) # 全球源较大，增加超时
            r.encoding = 'utf-8'
            if r.status_code != 200: continue
            
            # 改进的正则提取，增加对 group-title 的初步抓取
            matches = re.findall(r'#EXTINF:.*?(?:group-title="(.*?)")?,(.*?)\n(http.*)', r.text)
            
            for g_title, ch_name, link in matches:
                link = link.strip()
                if link in seen_urls: continue
                
                name_u = ch_name.strip().upper()
                is_ipv6 = "[" in link and "]" in link
                
                # 分类引擎
                group = "全球其他"
                if any(x in name_u for x in ["CCTV", "CGTN"]): group = "中央台"
                elif "卫视" in name_u: group = "卫视"
                elif any(x in name_u for x in ["香港", "HK", "翡翠", "TVB", "凤凰", "澳门", "台湾", "TW"]): group = "港澳台"
                else:
                    # 匹配地市
                    found_prov = False
                    for prov, keywords in PROVINCES.items():
                        if any(k in name_u for k in keywords):
                            group = f"{prov}频道"
                            found_prov = True
                            break
                    
                    # 如果不是地市，尝试保留原有的全球组名
                    if not found_prov and g_title:
                        group = g_title.strip()

                all_channels.append({"name": ch_name.strip(), "url": link, "group": group, "v6": is_ipv6})
                seen_urls.add(link)
                
        except Exception as e:
            print(f"源 {name} 访问跳过: {e}")

    # 排序：中央台 > 卫视 > 港澳台 > 地区频道 > 其他
    group_order = {"中央台": 0, "卫视": 1, "港澳台": 2}
    all_channels.sort(key=lambda x: (group_order.get(x['group'], 10), x['group'], x['name'], 1 if x['v6'] else 0))

    print(f"抓取完毕，总计获得全世界频道线路: {len(all_channels)}")

    # --- 写入三个文件 ---
    with open(f"{prefix}cn_tw.m3u", "w", encoding="utf-8") as f_m3u, \
         open(f"{prefix}cn_tw.txt", "w", encoding="utf-8") as f_txt, \
         open(f"{prefix}tv_v4.txt", "w", encoding="utf-8") as f_v4:
        
        f_m3u.write("#EXTM3U\n")
        curr_g_txt, curr_g_v4 = None, None
        
        for c in all_channels:
            # 1. 写入 M3U (全球全量)
            f_m3u.write(f'#EXTINF:-1 group-title="{c["group"]}",{c["name"]}\n{c["url"]}\n')
            
            # 2. 写入 TXT (全量)
            if c['group'] != curr_g_txt:
                curr_g_txt = c['group']
                f_txt.write(f"{curr_g_txt},#genre#\n")
            f_txt.write(f"{c['name']},{c['url']}\n")
            
            # 3. 写入纯 IPv4 (电视专用)
            if not c['v6']:
                if c['group'] != curr_g_v4:
                    curr_g_v4 = c['group']
                    f_v4.write(f"{curr_g_v4},#genre#\n")
                f_v4.write(f"{c['name']},{c['url']}\n")

    print(f"✨ 全球同步成功！")

if __name__ == "__main__":
    fetch_and_clean()
