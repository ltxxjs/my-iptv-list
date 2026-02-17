import requests

urls = [
    "https://iptv-org.github.io/iptv/countries/cn.m3u", # 中国大陆
    "https://iptv-org.github.io/iptv/countries/tw.m3u"  # 台湾
]

with open("cn_tw.m3u", "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    for url in urls:
        r = requests.get(url)
        lines = r.text.split('\n')
        # 跳过每个文件的第一行 #EXTM3U
        f.write('\n'.join(lines[1:]))
