from pathlib import Path
import re
from resize_pic import crop_image
from PIL import Image
from modify import replace_gif


def format_name(format_path:Path):
    """
    遍历所有文件夹以及文件，进行字符替换
    （ 替换为 (
    ） 替换为 )
    """
    for item in format_path.rglob("*"):
        item.rename(item.parent / item.name.replace('（', '(').replace('）', ')'))
        print(f"重命名{item}为{item.parent / item.name.replace('（', '(').replace('）', ')')}")
    # 仅保留第一个#，其他的#替换为''
    pattern = re.compile(r'#(.*)#')
    for item in format_path.rglob('*'):
        new_name = pattern.sub(lambda x: '#' + x.group(1).replace('#', ''), item.name)
        new_path = item.parent / new_name
        item.rename(new_path)

    print("重命名完成")




# 整理文件名
def format_filename(video_dir:Path, flag=False):
    """
    重命名每个目录下的文件
    其中:
    1.目录名为视频名(BVxx)，其中视频名中的中文字符已经被替换为英文字符；视频名为<分pid#分P视频名.mp4>
    2.目录下的文件：*.mp4(对应视频)、*.srt(对应字幕)、*.ass(对应弹幕)、*.jpg(封面)
    3.视频：视频数目==1: 单个视频, 改名为<视频名.mp4>, 视频数目>1:分P视频,改名为<视频名 - 分pid#分P视频.mp4>
    4.字幕：视频数目==1: 单个视频, 改名为<视频名.zh.srt>, 视频数目>1:分P视频,改名为<视频名 - 分pid#分P视频.zh.srt>
    5.弹幕: 视频数目==1: 单个视频, 改名为<视频名.danmu.ass>, 视频数目>1:分P视频,改名为<视频名 - 分pid#分P视频.danmu.ass>
    6.封面: 优先寻找竖向图, 改名为<poster.jpg>, 若无竖向图,则寻找横向图进行剪裁,改名为<poster.jpg>, 其他的图片删除
    """
    # 步骤1：获取视频名/id
    title = re.search(r'^(.+)\(', video_dir.name).group(1)
    bvid = re.search(r'\((.+)\)', video_dir.name).group(1)
    # 获取父目录名
    full_title = video_dir.parent.name

    # 步骤2：获取视频数目以及列表
    video_list = list(video_dir.glob("*.mp4"))
    video_num = len(video_list)
    # 获取字幕文件列表
    subtitle_list = list(video_dir.glob("*.srt"))
    # 获取弹幕文件列表
    danmu_list = list(video_dir.glob("*.ass"))
    # 获取图片文件列表jpg，png, gif
    image_list = list(video_dir.glob("*.jpg")) + list(video_dir.glob("*.png")) + list(video_dir.glob("*.gif"))

    # 步骤3：重命名
    if video_num == 1:
        # 重命名视频文件
        video_list[0].rename(video_dir / f"{title}.mp4")
        # 重命名字幕文件
        if subtitle_list:
            subtitle_file = subtitle_list[0]
            subtitle_file.rename(video_dir / f"{title}.zh.srt")
        # 重命名弹幕文件
        danmu_file = danmu_list[0]
        danmu_file.rename(video_dir / f"{title}.danmu.ass")
        # 重命名图片文件
        image_file = image_list[0]
        # 若为竖向图，则直接改名为poster.jpg
        image_obj = Image.open(image_file)
        if image_obj.height > image_obj.width:
            image_obj.close()
            image_file.rename(video_dir / "poster.jpg")
        # 若为横向图，则剪裁为竖向图，再改名为poster.jpg
        else:
            crop_image(image_file, video_dir / "poster.jpg", 0.65)
            image_obj.close()
            image_file.unlink()
    elif video_num > 1:
        for video in video_list:
            # 获取id/分P名, 原视频名为<分pid#分P视频名.mp4>, 以#分割，考虑到有些视频名中含有'.'，去除后缀名
            pid, pname = video.stem.split("#")
            video.rename(video_dir / f"{full_title} - {pid}#{pname}.mp4")
            # 寻找对应的ID，以#分割, 重命名字幕文件
            if subtitle_list:
                # 判断是否有对应的ID的字幕文件
                if f"{pid}#" not in [subtitle.stem for subtitle in subtitle_list]:
                    pass
                else:
                    subtitle_file = [subtitle for subtitle in subtitle_list if subtitle.stem.split("#")[0] == pid][0]
                    subtitle_file.rename(video_dir / f"{full_title} - {pid}#{pname}.zh.srt")

            # 重命名弹幕文件
            danmu_file = [danmu for danmu in danmu_list if danmu.stem.split("#")[0] == pid][0]
            danmu_file.rename(video_dir / f"{full_title} - {pid}#{pname}.danmu.ass")
        # 重命名图片文件, 寻找竖向图
        image_file = []
        for image in image_list:
            image_obj = Image.open(image)
            if image_obj.height > image_obj.width:
                image_file.append(image)
            image_obj.close()
        if image_file:
            image_file = image_file[0]
            image_file.rename(video_dir / "poster.jpg")
        # 若无竖向图，则寻找横向图进行剪裁
        else:
            image_file = image_list[0]
            crop_image(image_file, video_dir / "poster.jpg", 0.65)
        # 删除其他图片
        for image in image_list:
            # 不是poster.jpg的图片
            if image.name != "poster.jpg":
                image.unlink()
    print(f"视频名：{title}，视频数目：{video_num}，视频id：{bvid}，重命名完成！")



if __name__ == "__main__":
    input_file = Path("C:/Users/wff19/Downloads/Compressed/DownKyi-1.5.7/Media/link")
    format_name(input_file)
    replace_gif(input_file)
    for video_dir in input_file.glob("*"):
        # 判断是否存在poster.jpg 以及 存在gif文件
        if not (video_dir / "poster.jpg").exists() :
            print(video_dir.name)
            format_filename(video_dir)