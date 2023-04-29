import os
import shutil
import time
import tkinter as tk
import tkinter.filedialog as file
from pathlib import Path

fileName = ""
base = f"D:\Mr5\Desktop\AI\\video"
workspace = f"{base}\\{fileName}"
srcDir = workspace + "\\src"
inputDir = workspace + "\\input"
outputDir = workspace + "\\output"
outputHDir = workspace + "\\output_h"
videoPath = workspace + f"\\{fileName}.mp4"


# 利用ffmpeg视频取帧

# 转换视频


def img2Video(inputPath="", outPath="", fps=30, crf=18):
    timeMill = int(round(time.time() * 1000))

    accCmd = ''
    if os.path.exists('{workspace}\\output.aac'):
        accCmd = f'-i "{workspace}\\output.aac" -c:a aac '

    input_frame = inputPath + "_frame"

    if os.path.exists(input_frame):
        shutil.rmtree(input_frame)

    shutil.copytree(inputPath, input_frame)
    rename(input_frame)

    cmd = f'ffmpeg -f image2 -r {fps} -i "{input_frame}\\%d.png" {accCmd} ' \
          f'-c:v libx264 -crf {crf} -preset:v slow -pix_fmt yuv420p ' \
          f'-vf "scale=1080:-2" ' \
          f'{outPath}\\output_{timeMill}.mp4 '
    exeCMD(cmd)


def img2VideoN(fps, level=18):
    img2Video(outputDir, workspace, fps, level)


def img2VideoH(fps, level=18):
    img2Video(outputHDir, workspace, fps, level)


def videoInsFrame(path=videoPath, fps=30):
    timeMill = int(round(time.time() * 1000))
    cmd = f'ffmpeg -threads 16 -i {path} -filter_complex minterpolate="fps={fps}" {workspace}\\output_ins_{timeMill}.mp4'
    exeCMD(cmd)


def video2Img(fps=30):
    # if os.path.exists(src):
    #     shutil.rmtree(src)
    if os.listdir(srcDir):
        diff_file()
        return
    cmd = f'ffmpeg -i {videoPath} -vf fps={fps} {srcDir}\\%d.png'
    exeCMD(cmd)

    cmd = f'ffmpeg -i {videoPath} -vn -c:a copy -y {workspace}/output.aac'
    exeCMD(cmd)
    diff_file()


def video2ImgLimit(fps=30):
    if os.path.exists(srcDir):
        shutil.rmtree(srcDir)
    os.makedirs(srcDir, exist_ok=True)
    cmd = f'ffmpeg -i {videoPath} -vframes {fps} {srcDir}\\%d.png'
    exeCMD(cmd)


def zipVideo(inputPath, outPath, level=18):
    timeMill = int(round(time.time() * 1000))
    cmd = f'ffmpeg -i {inputPath} -c:v libx265 -x265-params crf={level}:preset=placebo {outPath}\\output_zip_{timeMill}.mp4'
    # cmd = f'ffmpeg -i {path} -c:v libx265 -x265-params crf=30:preset=placebo {workspace}\\output_zip_{timeMill}.mp4'
    exeCMD(cmd)


def exeCMD(cmd):
    print(cmd)
    os.system(f"powershell.exe -c {cmd}")


def diff_file():
    if not os.path.exists(outputDir):
        os.makedirs(outputDir)
    srcs = set([_ for _ in os.listdir(srcDir)])
    outs = set([_ for _ in os.listdir(outputDir)])
    # fileName1对比fileName2，fileName1中多出来的文件；注意，如果fileName2里有fileName1中没有的文件，也不会筛选出来
    diffs = srcs.difference(outs)
    print(diffs)

    # 删除input文件里的所有文件
    if os.path.exists(inputDir):
        shutil.rmtree(inputDir)

    os.makedirs(inputDir)

    for name in diffs:
        shutil.copyfile(os.path.join(srcDir, name),
                        os.path.join(inputDir, name))


def rename(path):
    sorted_data = sortPath(path)
    i = 1
    for name in sorted_data:
        stuffx = name.split(".")[1]
        os.rename(f"{path}\{name}", f"{path}\{i}.{stuffx}")
        i = i + 1


def sortPath(path):
    names = os.listdir(path)
    return sorted(names, key=lambda x: (
        int(''.join(filter(str.isdigit, x))), ''.join(filter(str.isalpha, x))))


def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def color(text):
    return f"\033[31m{text}\033[0m"


def init(path):
    global fileName, base, workspace, srcDir, inputDir, outputDir, outputHDir, videoPath
    fileName = os.path.basename(path).replace(".mp4", "")
    # base = f"D:\Mr5\Desktop\AI\\video"
    base = os.path.dirname(path)
    workspace = f"{base}/{fileName}"
    srcDir = workspace + "/src"
    inputDir = workspace + "/input"
    outputDir = workspace + "/output"
    outputHDir = workspace + "/output_h"
    videoPath = path

    for path in [workspace, srcDir, outputDir, outputHDir, inputDir]:
        mkdir(path)


def selectFile(tips="视频文件", types="*.mp4"):
    tkObj = tk.Tk()
    desktop = os.path.join(os.path.expanduser("~"), 'Desktop')
    pathInput = file.askopenfilename(
        filetypes=[(tips, types)], initialdir=rf"{desktop}", title="选择要处理的视频")
    tkObj.destroy()
    return pathInput


def selectDirectory():
    tkObj = tk.Tk()
    desktop = os.path.join(os.path.expanduser("~"), 'Desktop')
    pathInput = file.askdirectory(initialdir=rf"{desktop}", title="选择要处理的视频")
    tkObj.destroy()
    return pathInput


def start():
    fps = 30
    path = ""
    level = 18

    def startNow():
        nonlocal fps, path, level
        print(color(r"请选择要处理的视频:"))
        while path == "":
            path = selectFile()
            print(f"输入的视频地址：{path}")

        print(color(r"请输入帧率 default:30"))
        fpsResult = input("请输入:")
        if fpsResult:
            fps = int(fpsResult)
        print(color(r"请输入压缩级别 0-》51（无损：文件最大-》最低画质：文件最小） default:18"))
        levelResult = input("请输入:")
        if levelResult:
            level = int(levelResult)
        init(f"{path}")

    while True:
        print(color(
            f"""
-----------------------------------------------------------
|    请选择要执行的操作:                                      |
|    0:重置参数                                        |
|    1:视频转图片 video2Img(fps)                            |
|    2:output图片转视频 img2VideoN(fps)                      |
|    3:output_h图片转视频 img2VideoH(fps)                    |
|    4:提取src和out的差异帧到input diff_file()               |
|    5:提取前多少帧 video2ImgLimit()                        |
|    6:插帧 videoInsFrame()           |
|    7:无损压缩视频 zipVideo()   
|    8:从帧文件夹生成视频 img2Video(fps, inputPath, outPath)
|    当前配置 fps:{fps} 视频：{path}                  
-----------------------------------------------------------
        """))
        result = input("请选择:")

        # 初始化视频地址
        if result == "0":
            path = ""
            fps = 30
            level = 18

        # 视频转帧 fps:每秒多少帧
        if result == "1":
            if path == "":
                startNow()
            video2Img(fps)
        # 从output文件夹生成视频fps:每秒多少帧
        if result == "2":
            if path == "":
                startNow()
            img2VideoN(fps, level)

        # 从output_h文件夹生成视频 fps:每秒多少帧
        if result == "3":
            if path == "":
                startNow()
            img2VideoH(fps, level)
        # 对比src和out的差异，并且把output里少的部分提取来到input文件夹里，用于重复生成坏掉的图
        if result == "4":
            if path == "":
                startNow()
            diff_file()

        # 提取前多少帧
        if result == "5":
            inputFps = input("请输入提取的帧数")
            fpsTmp = 100
            if inputFps:
                fpsTmp = int(inputFps)
            video2ImgLimit(fpsTmp)

        # 对视频进行插帧
        if result == "6":
            pathResult = selectFile()
            path = ""
            init(pathResult)
            inputFps = input("请输入帧数")
            fpsTmp = 30
            if inputFps:
                fpsTmp = int(inputFps)
            videoInsFrame(rf"{pathResult}", fpsTmp)

        if result == "7":
            pathResult = selectFile()
            outputPath = Path(pathResult).parent
            path = ""
            print("请输入压缩级别 0-》51（无损：文件最大-》最低画质：文件最小） default:18")
            levelInput = input("请输入:")
            levelTmp = 18
            if levelInput:
                levelTmp = int(levelInput)
            init(pathResult)
            zipVideo(pathResult, outputPath, levelTmp)

        if result == "8":
            pathResult = selectDirectory()
            outputPath = Path(pathResult).parent
            print("请输入fps")
            fpsInput = input("请输入:")
            fpsTmp = 30
            if fpsInput:
                fpsTmp = int(fpsInput)
            img2Video(pathResult, outputPath, fpsTmp)


def startCode(path, fps):
    init(path)
    # 视频转帧 fps:每秒多少帧
    video2Img(fps)
    # 从output文件夹生成视频fps:每秒多少帧
    # img2VideoN(fps)
    # 从output_h文件夹生成视频 fps:每秒多少帧
    # img2VideoH(fps)
    # 对比src和out的差异，并且把output里少的部分提取来到input文件夹里，用于重复生成坏掉的图
    # diff_file()
    # 提取前多少帧
    # video2ImgLimit(fps)
    # 对视频进行插帧
    # videoInsFrame(rf"{path}",fps)

    # zipVideo()
