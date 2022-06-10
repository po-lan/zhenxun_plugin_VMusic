import random
import subprocess 
from PIL import Image
from pathlib import Path
from time import sleep
from .music_163 import get_song_id,get_song,get_lyrics
from configs.path_config import TEMP_PATH
from utils.utils import get_message_img
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, GroupMessageEvent, MessageSegment,Message
from utils.http_utils import AsyncHttpx
from nonebot.params import CommandArg
from nonebot.typing import T_State
from services.log import logger
from nonebot import on_command
from services.log import logger
import os

dir_path = Path(__file__).parent
IMG_PATH = str((dir_path).absolute()) + "/"

__zx_plugin_name__ = "V点歌"
__plugin_usage__ = """
usage：
    在线点歌
    以视频形式输出
    输出时间很长 且大量占用服务器性能
    图片边长需要为2的倍数
    指令：
        V点歌 [歌名] ?图片
            如果 携带图片会使用图片作为背景
            未携带则在图库里自动寻找
            如果图片为替换可以尝试清理缓存
        V点歌导入
            需要处理的图片放入 picin 后 使用V点歌导入命令自动裁剪
        V缓存删除 [歌名]
            删除某首音乐曾经生成的缓存

""".strip()
__plugin_des__ = "以视频+背景图的形式输出音乐"
__plugin_cmd__ = ["V点歌 [歌名]","V点歌导入","V缓存删除 [歌名]"]
__plugin_type__ = ("一些工具",)
__plugin_version__ = 0.1
__plugin_author__ = "落灰"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["V点歌 [歌名]","V点歌导入","V缓存删除 [歌名]",],
}


music_handler = on_command("V点歌", priority=5, block=True)

@music_handler.handle()
async def handle_first_receive(event: GroupMessageEvent,state: T_State, arg: Message = CommandArg(), ):
    if args := arg.extract_plain_text().strip():
        state["song_name"] = args
        state["img"] = get_message_img(event.json())


@music_handler.got("song_name", prompt="歌名是？")
async def _(bot: Bot, event: MessageEvent, state: T_State):
    song = state["song_name"]
    song_id = await get_song_id(song)
    if not song_id:
        await music_handler.finish("没有找到这首歌！", at_sender=True)
    else:
        url = await get_song(song_id)

        if url:
            id = random.randint(1,10000)
            msgImg = None
            if len(state["img"]) > 0:
                if await AsyncHttpx.download_file(
                    state["img"][0], TEMP_PATH / f"vMusic_{song_id}_{id}.jpg"
                ):
                    print( state["img"][0])
                    img = Image.open(TEMP_PATH / f"vMusic_{song_id}_{id}.jpg")

                    if img.format == "GIF":
                        img.close()
                        await music_handler.finish("不支持动态图作为背景")
                        return 
                    if img.format == "PNG":
                        r, g, b= img.split()
                        img = Image.merge("RGB", (r, g, b))
                        img.convert('RGB').save( (TEMP_PATH / f"vMusic_{song_id}_PTJ_{id}.jpg"), quality=70)
                        msgImg = (TEMP_PATH / f"vMusic_{song_id}_PTJ_{id}.jpg")

                    w = img.width      
                    h = img.height
                    if w % 2 == 0 and h % 2 == 0:
                        msgImg = (TEMP_PATH / f"vMusic_{song_id}_{id}.jpg")
                    else:
                        if  w % 2 != 0:
                            w -= 1
                        if  h % 2 != 0:
                            h -= 1
                        cropped = img.crop((0, 0, w , h))
                        cropped.convert('RGB').save(TEMP_PATH / f"vMusic_{song_id}_s_{id}.jpg")
                        msgImg = (TEMP_PATH / f"vMusic_{song_id}_s_{id}.jpg")
                else:
                    logger.warning(f"背景下载图片失败...")

            #lrc = await get_lyrics(song_id)
            
            #if lrc != None:
            #    lrcToSrt(lrc,song_id)

            try:

                img =  str((dir_path / "pic" / random.choice(os.listdir(dir_path / "pic"))).absolute()) if msgImg == None else msgImg

                srt = str((TEMP_PATH / f"vMusic_{song_id}.srt"))

                #cmd = f"""ffmpeg -r 30 -loop 1 -i {img} -i {url} {("-vf subtitles="+srt+" ") if lrc else " "}-shortest -preset ultrafast {TEMP_PATH}/{song_id}.mp4 -y """
                cmd = f"""ffmpeg -r 5 -loop 1 -i {img} -i {url} -shortest -preset ultrafast -vcodec libx264 {TEMP_PATH}/{song_id}.mp4 -y """


                path = Path(TEMP_PATH) / (str(song_id) + ".mp4")
                if os.path.exists(path) == False:

                    subprocess.Popen(cmd, shell=True)

                    i = 0
                    
                    sleep(10)

                    while  i < 15:
                        try:
                            await music_handler.send(MessageSegment.video(path))
                            logger.success(f"V点歌{song}视频发送完成")
                            break
                        except:
                            i += 1
                            sleep(5)
                    
                    if i == 15:
                        await music_handler.send("可能是转码时间有一些长，可以等几分钟在试")
                    
                else:
                    await music_handler.send(MessageSegment.video(path))
                
            except:
                await music_handler.finish("V点歌失败")
            
        else:
            await music_handler.finish("音乐获取失败")

    logger.info(
        f"(USER {event.user_id}, GROUP "
        f"{event.group_id if isinstance(event, GroupMessageEvent) else 'private'})"
        f" 点歌 :{song}"
    )


delc = on_command("V缓存删除", priority=5, block=True)
@delc.handle()
async def _( arg: Message = CommandArg(),):
    if args := arg.extract_plain_text().strip():
        song_id = await get_song_id(args)
        path = TEMP_PATH/ (str(song_id)+".mp4")
        if os.path.exists(path):
            os.remove(path)

picu = on_command("V点歌导入", priority=5, block=True)
@picu.handle()
async def _():
    pics = os.listdir(str(dir_path / "picin/"))
    for pic in pics:
        img = Image.open(str(dir_path / "picin" / pic))
        w = img.width      
        h = img.height
        if w % 2 == 0 and h % 2 == 0:
            img.close()
            os.rename(str(dir_path / "picin" / pic) , str(dir_path / "pic" / pic))
        else:
            if  w % 2 != 0:
                w -= 1
            if  h % 2 != 0:
                h -= 1
            cropped = img.crop((0, 0, w , h))
            cropped.save(str(dir_path / "pic" / pic))
            os.remove(str(dir_path / "picin" / pic))

    await picu.finish(f"完成,本次添加了{len(pics)}张随机背景图")


def lrcToSrt(text,song_id):
    count = 0
    lines = text.splitlines()
    path = (TEMP_PATH / f"vMusic_{song_id}.srt")
    for i in range(len(lines)):
        count += 1
        time = '00:' + lines[i-1].split(']')[0][1:] + '9' + ' --> ' + '00:' + lines[i].split(']')[0][1:] + '0'
        time = time.replace('.', ',')
        srt = lines[i-1].split(']')[1].strip('\n')
        with open(path, 'a', encoding='utf-8') as ff:
            ff.write(str(count-1) + '\n')
            ff.write(time + '\n')
            ff.write(srt)
            ff.write('\n'*2)