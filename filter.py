import requests
import re
import os

# 1. 核心源：保留对中文友好的源，去掉全球总索引以提高速度和纯净度
sources = {
    "IPTV_Org_CN": "https://iptv-org.github.io/iptv/countries/cn.m3u",
    "IPTV_Org_HK": "https://iptv-org.github.io/iptv/countries/hk.m3u",
    "IPTV_Org_TW": "https://iptv-org.github.io/iptv/countries/tw.m3u",
    "Heros_IPv4": "https://mirror.ghproxy.com/https://raw.githubusercontent.com/herosylee/iptv/main/live.m3u",
    "YueChan_IPTV": "https://mirror.ghproxy.com/https://raw.githubusercontent.com/YueChan/Live/main/IPTV.m3u",
    "Fanmingming_V6": "https://mirror.ghproxy.com/https://raw.githubusercontent.com/fanmingming/live/main/tv/m3u/ipv6.m3u",
    "Guovern_Live": "https://mirror.ghproxy.com/https://raw.githubusercontent.com/Guovern/tv-list/main/m3u/live.m3u"
}

# 2. 详细的省份分类字典 (用于严格匹配)
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
    "黑龙江": ["黑龙江", "哈尔滨", "齐齐哈尔", "鸡西", "鹤岗", "双鸭山", "大庆", "伊春", "佳木斯", "七台河", "牡丹江", "黑河", "绥化", "大兴安岭"],
    "广西": ["广西", "南宁", "柳州", "桂林", "梧州", "北海", "防城港", "钦州", "贵港", "玉林", "百色", "贺州", "河池", "来宾", "崇左"],
    "海南": ["海南", "海口", "三亚"],
    "云南": ["云南", "昆明"], "贵州": ["贵州", "贵阳"], "陕西": ["陕西", "西安"], "甘肃": ["甘肃", "兰州"],
    "宁夏": ["宁夏", "银川"], "内蒙古": ["内蒙古"], "新疆": ["新疆"], "青海": ["青海"], "西藏": ["西藏"]
}

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

def fetch_and_clean():
    all_channels = []
    seen_urls = set()
    
    is_github = os.environ.get('GITHUB_ACTIONS') == 'true'
    prefix = "" if is_github else "data/"
    if prefix and not os.path.exists(prefix): os.makedirs(prefix)

    for name, url in sources.items():
        print(f"正在抓取中文源: {name}...")
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            r.encoding = 'utf-8'
            if r.status_code != 200: continue
            
            matches = re.findall(r'#EXTINF:.*?,(.*?)\n(http.*)', r.text)
            
            for ch_name, link in matches:
                link = link.strip()
                if link in seen_urls: continue
                
                name_u = ch_name.strip().upper()
                is_ipv6 = "[" in link and "]" in link
                
                # --- 严格过滤逻辑：仅保留中文相关频道 ---
                group = None
                
                # 1. 中央台
                if any(x in name_u for x in ["CCTV", "CGTN", "中央"]): 
                    group = "中央台"
                # 2. 卫视
                elif "卫视" in name_u: 
                    group = "卫视"
                # 3. 港澳台
                elif any(x in name_u for x in ["香港", "HK", "翡翠", "TVB", "凤凰", "澳门", "台湾", "TW", "中视", "华视", "民视"]): 
                    group = "港澳台"
                # 4. 地方省市
                else:
                    for prov, keywords in PROVINCES.items():
                        if any(k in name_u for k in keywords):
                            group = f"{prov}频道"
                            break
                    
                # 只有匹配到上述中文组的才加入列表
                if group:
                    all_channels.append({"name": ch_name.strip(), "url": link, "group": group, "v6": is_ipv6})
                    seen_urls.add(link)
                
        except Exception as e:
            print(f"源 {name} 访问失败: {e}")

    # 排序
    group_order = {"中央台": 0, "卫视": 1, "港澳台": 2}
    all_channels.sort(key=lambda x: (group_order.get(x['group'], 10), x['group'], x['name']))

    print(f"中文频道提取完毕，共计: {len(all_channels)} 条线路")

    # 写入三个文件
    with open(f"{prefix}cn_tw.m3u", "w", encoding="utf-8") as f_m3u, \
         open(f"{prefix}cn_tw.txt", "w", encoding="utf-8") as f_txt, \
         open(f"{prefix}tv_v4.txt", "w", encoding="utf-8") as f_v4:
        
        f_m3u.write("#EXTM3U\n")
        curr_g_txt, curr_g_v4 = None, None
        
        for c in all_channels:
            # 写入 M3U
            f_m3u.write(f'#EXTINF:-1 group-title="{c["group"]}",{c["name"]}\n{c["url"]}\n')
            
            # 写入 TXT (全量)
            if c['group'] != curr_g_txt:
                curr_g_txt = c['group']
                f_txt.write(f"{curr_g_txt},#genre#\n")
            f_txt.write(f"{c['name']},{c['url']}\n")
            
            # 写入 TXT (纯 IPv4)
            if not c['v6']:
                if c['group'] != curr_g_v4:
                    curr_g_v4 = c['group']
                    f_v4.write(f"{curr_g_v4},#genre#\n")
                f_v4.write(f"{c['name']},{c['url']}\n")

    print(f"✨ 中文净化版同步成功！")

if __name__ == "__main__":
    fetch_and_clean()
