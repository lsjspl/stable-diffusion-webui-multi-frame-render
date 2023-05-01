# stable-diffusion-webui-multi-frame-render

插件基于多帧渲染插件(https://xanthius.itch.io/multi-frame-rendering-for-stablediffusion)
进行修改增强

插件需要ffmpeg

修改内容如下   
第一步：   
在视频同目录生成同名文件夹   
如果src目录没有帧，会直接读取视频帧到src，并复制src到input文件夹。   
如果src有帧，会对比src和out的差异文件，复制差异文件到input。    
第二步：   
sd处理input文件夹的图片。   
第三步：   
从output文件夹复制到output_frame文件夹，并按顺序重命名帧，生成视频，如果有音频文件，会合并音频。   
所以：你如果全量生成的图不满意，可以去output文件夹里删除掉不满意的图，然后再次重新生成，此时只会重新生成output被删除的图片。   
  
其他乱七八糟的我就不写了，本来自己用的，写出来了就也分享出来了，也许能方便到别人  

如果你删除output里部分没生成好的图片，重新生成这部分图片，先按照如下设置，以保证新生成的图片和旧的图片样式统一

![7efa7dfeff45e880e706421225bf7ac](https://user-images.githubusercontent.com/2315298/235463871-c88de7ac-6571-4746-8643-596b7ca5d655.png)
