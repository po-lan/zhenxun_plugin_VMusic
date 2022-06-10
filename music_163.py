from utils.http_utils import AsyncHttpx
import json


headers = {"referer": "http://music.163.com"}
cookies = {"appver": "2.0.2"}


async def search_song(song_name: str):
    """
    搜索歌曲
    :param song_name: 歌名
    """
    r = await AsyncHttpx.post(
        f"http://music.163.com/api/search/get/",
        data={"s": song_name, "limit": 1, "type": 1, "offset": 0},
    )
    if r.status_code != 200:
        return None
    return json.loads(r.text)


async def get_song_id(song_name: str) -> int:
    
    r = await search_song(song_name)
    try:
        return r["result"]["songs"][0]["id"]
    except KeyError:
        return 0


async def get_song_info(songId: int):
    """
    获取歌曲信息
    """
    r = await AsyncHttpx.post(
        f"http://music.163.com/api/song/detail/?id={songId}&ids=%5B{songId}%5D",
    )
    if r.status_code != 200:
        return None
    return json.loads(r.text)

"""async def get_song_info2():
    
    print(111)
    r = await AsyncHttpx.post(
        "https://music.liuzhijin.cn/",
        headers={
            "origin":"https://music.liuzhijin.cn/",
            "accept":"application/json, text/javascript, */*; q=0.01",
            "referer":f"https://music.liuzhijin.cn/?id={1891628173}&type=netease"
        },
        params={"input":1891628173, "filter":"id", "type":"netease", "page":1},
    )
    print(233)
    print(r.text)
    if r.status_code != 200:
        return None
    print(json.loads(r.text))
"""

async def get_lyrics(songId: int):
        
    r = await AsyncHttpx.get(f"http://music.163.com/api/song/media?id={songId}")
    if r.status_code != 200:
        return None
    return json.loads(r.text)['lyric']


async def get_song(songId: int):
    """
    获取歌曲
    """
    url = (await AsyncHttpx.get(f"https://music.163.com/song/media/outer/url?id={songId}.mp3")).headers["location"]
    #print(url)
    #r = await AsyncHttpx.download_file(url = url,path=f'./resources/record/temp/{songId}.mp3')
    
    return url