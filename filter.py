import requests
import re
import os

# 综合源：涵盖了大部分省级、地市级和港台频道
sources = {
    "Fanmingming_V6": "https://raw.githubusercontent.com/fanmingming/live/main/tv/m3u/ipv6.m3u",
    "YueChan_IPTV": "https://raw.githubusercontent.com/YueChan/Live/main/IPTV.m3u",
    "Adult_IPTV": "https://raw.githubusercontent.com/Guovern/tv-list/main/m3u/live.m3u",
    "HK_Special": "https://raw.githubusercontent.com/Moexin/IPTV/master/HK.m3u"
}

# 全平台全国省市关键词字典
PROVINCES = {
    "北京": ["北京", "京台", "BTV"],
    "上海": ["上海", "东方卫视", "哈哈炫动"],
    "天津": ["天津"],
    "重庆": ["重庆"],
    "广东": ["广东", "广州", "深圳", "珠海", "汕头", "佛山", "韶关", "湛江", "肇庆", "江门", "茂名", "惠州", "梅州", "汕尾", "河源", "阳江", "清远", "东莞", "中山", "潮州", "揭阳", "云浮"],
    "江苏": ["江苏", "南京", "苏州", "无锡", "常州", "扬州", "南通", "泰州", "盐城", "淮安", "徐州", "连云港", "宿迁"],
    "浙江": ["浙江", "杭州", "宁波", "温州", "嘉兴", "湖州", "绍兴", "金华", "衢州", "舟山", "台州", "丽水"],
    "山东": ["山东", "济南", "青岛", "淄博", "枣庄", "东营", "烟台", "潍坊", "济宁", "泰安", "威海", "日照", "临沂", "德州", "聊城", "滨州", "菏泽"],
    "福建": ["福建", "福州", "厦门", "莆田", "三明", "泉州", "漳州", "南平", "龙岩", "宁德"],
    "湖南": ["湖南", "长沙", "株洲", "湘潭", "衡阳", "邵阳", "岳阳", "常德", "张家界", "益阳", "郴州", "永州", "怀化", "娄底", "湘西"],
    "湖北": ["湖北", "武汉", "黄石", "十堰", "宜昌", "襄阳", "鄂州", "荆门", "孝感", "荆州", "黄冈", "咸宁", "随州", "恩施", "仙桃", "天门", "潜江"],
    "河南": ["河南", "郑州", "开封", "洛阳", "平顶山", "安阳", "鹤壁", "新乡", "焦作", "濮阳", "许昌", "漯河", "三门峡", "南阳", "商丘", "信阳", "周口", "驻马店"],
    "河北": ["河北", "石家庄", "唐山", "秦皇岛", "邯郸", "邢台", "保定", "张家口", "承德", "沧州", "廊坊", "衡水"],
    "四川": ["四川", "成都", "自贡", "攀枝花", "泸州", "德阳", "绵阳", "广元", "遂宁", "内江", "乐山", "南充", "眉山", "宜宾", "广安", "达州", "雅安", "巴中", "资阳", "阿坝", "甘孜", "凉山"],
    "安徽": ["安徽", "合肥", "芜湖", "蚌埠", "淮南", "马鞍山", "淮北", "铜陵", "安庆", "黄山", "滁州", "阜阳", "宿州", "六安", "亳州", "池州", "宣城"],
    "江西": ["江西", "南昌", "景德镇", "萍乡", "九江", "新余", "鹰潭", "赣州", "吉安", "宜春", "抚州", "上饶"],
    "辽宁": ["辽宁", "沈阳", "大连", "鞍山", "抚顺", "本溪", "丹东", "锦州", "营口", "阜新", "辽阳", "盘锦", "铁岭", "朝阳", "葫芦岛"],
    "吉林": ["吉林", "长春", "四平", "辽源", "通化", "白山", "松原", "白城", "延边"],
    "黑龙江": ["黑龙江", "哈尔滨", "齐齐哈尔", "鸡西", "鹤岗", "双鸭山", "大庆", "伊春", "佳木斯", "七台河", "牡丹江", "黑河", "绥化", "大兴安岭"],
    "云南": ["云南", "昆明", "曲靖", "玉溪", "保山", "昭通", "丽江", "普洱", "临沧", "楚雄", "红河", "文山", "西双版纳", "大理", "德宏", "怒江", "迪庆"],
    "贵州": ["贵州", "贵阳", "六盘水", "遵义", "安顺", "毕节", "铜仁", "黔西南", "黔东南", "黔南"],
    "山西": ["山西", "太原", "大同", "阳泉", "长治", "晋城", "朔州", "晋中", "运城", "忻州", "临汾", "吕梁"],
    "陕西": ["陕西", "西安", "铜川", "宝鸡", "咸阳", "渭南", "延安", "汉中", "榆林", "安康", "商洛"],
    "甘肃": ["甘肃", "兰州", "嘉峪关", "金昌", "白银", "天水", "武威", "张掖", "平凉", "酒泉", "庆阳", "定西", "陇南", "临夏", "甘南"],
    "广西": ["广西", "南宁", "柳州", "桂林", "梧州", "北海", "防城港", "钦州", "贵港", "玉林", "百色", "贺州", "河池", "来宾", "崇左"],
    "内蒙古": ["内蒙古", "呼和浩特", "包头", "乌海", "赤峰", "通辽", "鄂尔多斯", "呼伦贝尔", "巴彦淖尔", "乌兰察布", "兴安", "锡林郭勒", "阿拉善"],
    "宁夏": ["宁夏", "银川", "石嘴山", "吴忠", "固原", "中卫"],
    "青海": ["青海", "西宁", "海东", "海北", "黄南", "海南", "果洛", "玉树", "海西"],
    "新疆": ["新疆", "乌鲁木齐", "克拉玛依", "吐鲁番", "哈密", "昌吉", "博尔塔拉", "巴音郭楞", "阿克苏", "克孜勒苏", "喀什", "和田", "伊犁", "塔城", "阿勒泰"],
    "海南": ["海南", "海口", "三亚", "三沙", "儋州"],
    "西藏": ["西藏", "拉萨", "日喀则", "昌都", "林芝", "山南", "那曲", "阿里"]
}

def fetch_and_clean():
    all_channels = []
    seen_urls = set()

    for name, url in sources.items():
        print(f"Fetching: {name}")
        try:
            r = requests.get(url, timeout=20)
            # 增强型匹配正则，捕获更多属性
            matches = re.findall(r'#EXTINF:.*?,(.*?)\n(http.*)', r.text)
            for channel_name, link in matches:
                link = link.strip()
                if link in seen_urls: continue
                
                name_u = channel_name.upper()
                is_ipv6 = "[" in link and "]" in link
                display_name = f"{channel_name} [IPv6]" if is_ipv6 else channel_name
                
                # --- 分类大脑 ---
                group = "其他"
                
                # 1. 香港/澳门 (独立优先级)
                if any(x in name_u for x in ["HK", "香港", "翡翠", "TVB", "凤凰", "澳门", "MO", "莲花"]):
                    group = "港澳电视"
                # 2. 台湾 (可选)
                elif any(x in name_u for x in ["台湾", "TW", "中天", "年代", "TVBS"]):
                    group = "台湾电视"
                # 3. 中央台
                elif "CCTV" in name_u or "CGTN" in name_u:
                    group = "中央台"
                # 4. 卫视
                elif "卫视" in name_u:
                    group = "卫视"
                # 5. 全国各省遍历
                else:
                    found_prov = False
                    for prov, cities in PROVINCES.items():
                        if any(city in name_u for city in cities):
                            group = f"{prov}频道"
                            found_prov = True
                            break
                    # 6. 如果没匹配到具体省份但带“台”字的归类
                    if not found_prov and any(x in name_u for x in ["台", "频道", "广播"]):
                        group = "地方台"

                if group != "其他":
                    all_channels.append({"name": display_name, "url": link, "group": group, "v6": is_ipv6})
                    seen_urls.add(link)
        except Exception as e:
            print(f"Error fetching {name}: {e}")

    # 定义分组排序优先级
    def sort_key(x):
        # 排序权重：中央 > 卫视 > 港澳 > 台湾 > 各省
        priority = {
            "中央台": 0,
            "卫视": 1,
            "港澳电视": 2,
            "台湾电视": 3
        }
        # 如果在 priority 字典里没找到，说明是省份频道，给一个统一的基础权重
        p_val = priority.get(x['group'], 10)
        # 返回元组进行多级排序：权重 -> 组名 -> IPv4优先
        return (p_val, x['group'], 1 if x['v6'] else 0)

    all_channels.sort(key=sort_key)

    # 路径处理 (适配 Docker 数据卷)
    prefix = "data/" if (os.path.exists("/.dockerenv") or os.environ.get("DOCKER_RUNTIME")) else ""
    if prefix: os.makedirs(prefix, exist_ok=True)

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
    print("All tasks finished successfully!")

if __name__ == "__main__":
    fetch_and_clean()
