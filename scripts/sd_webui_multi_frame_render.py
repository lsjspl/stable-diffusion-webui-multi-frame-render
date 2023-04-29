# Beta V0.72
import numpy as np
from tqdm import trange
from PIL import Image, ImageSequence, ImageDraw
import math

import modules.scripts as scripts
import gradio as gr

from modules import processing, shared, sd_samplers, images
from modules.processing import Processed
from modules.shared import opts, cmd_opts, state
from modules import deepbooru
import os
from types import SimpleNamespace

import helper.videohelpModule as videoHelper


class Script(scripts.Script):
    def title(self):
        return "SD Multi-frame Video rendering - V0.72"

    def show(self, is_img2img):
        return is_img2img

    def ui(self, is_img2img):
        tipsText = """
第一步：
如果src目录没有帧，会直接读取视频帧到src，并复制src到input文件夹。
如果src有帧，会对比src和out的差异文件，复制差异文件到input。
第二步：
sd处理input文件夹的图片。
第三步：
从output文件夹复制到output_frame文件夹，并按顺序重命名帧，生成视频，如果有音频文件，会合并音频。
所以：你可以如果全量生成的图不满意，可以去output文件夹里删除掉，然后再次重新生成，只会重新生成差异的图片。
        """
        videoPath = gr.Text(label="视频文件路径", placeholder="视频路径", info=tipsText)
        fpsSlider = gr.Slider(minimum=10, maximum=30, step=1, label='帧率', value=30,
                              elem_id=self.elem_id("fpsSlider"))
        first_denoise = gr.Slider(minimum=0, maximum=1, step=0.05, label='Initial Denoise Strength', value=1,
                                  elem_id=self.elem_id("first_denoise"))
        append_interrogation = gr.Dropdown(label="Append interrogated prompt at each iteration",
                                           choices=["None", "CLIP", "DeepBooru"], value="None")
        third_frame_image = gr.Dropdown(label="Third Frame Image",
                                        choices=["None", "FirstGen", "GuideImg", "Historical"], value="None")
        # reference_imgs = gr.UploadButton(label="Upload Guide Frames", file_types = ['.png','.jpg','.jpeg'], live=True, file_count = "multiple")
        # reference_imgs = gr.File(file_count="directory", label="Upload Guide Frames", show_label=True)

        color_correction_enabled = gr.Checkbox(label="Enable Color Correction", value=False,
                                               elem_id=self.elem_id("color_correction_enabled"))
        unfreeze_seed = gr.Checkbox(label="Unfreeze Seed", value=False, elem_id=self.elem_id("unfreeze_seed"))
        loopback_source = gr.Dropdown(label="Loopback Source", choices=["PreviousFrame", "InputFrame", "FirstGen"],
                                      value="PreviousFrame")

        return [append_interrogation, videoPath, fpsSlider, first_denoise, third_frame_image,
                color_correction_enabled,
                unfreeze_seed, loopback_source]

    def run(self, p, append_interrogation, videoPath, fpsSlider, first_denoise, third_frame_image,
            color_correction_enabled,
            unfreeze_seed, loopback_source):

        # 初始化视频文件夹
        videoHelper.init(videoPath)
        # 生成序列帧
        videoHelper.video2Img(fpsSlider)
        sortData = videoHelper.sortPath(videoHelper.inputDir)
        reference_imgs = []
        for name in sortData:
            reference_imgs.append(SimpleNamespace(**{"name": f"{videoHelper.srcDir}/{name}"}))

        print(reference_imgs)
        freeze_seed = not unfreeze_seed

        loops = len(reference_imgs)

        processing.fix_seed(p)
        batch_count = p.n_iter

        p.batch_size = 1
        p.n_iter = 1

        output_images, info = None, None
        initial_seed = None
        initial_info = None

        initial_width = p.width
        initial_img = p.init_images[0]

        grids = []
        all_images = []
        original_init_image = p.init_images
        original_prompt = p.prompt
        original_denoise = p.denoising_strength
        state.job_count = loops * batch_count

        initial_color_corrections = [processing.setup_color_correction(p.init_images[0])]

        for n in range(batch_count):
            history = []
            frames = []
            third_image = None
            third_image_index = 0
            frame_color_correction = None

            # Reset to original init image at the start of each batch
            p.init_images = original_init_image
            p.width = initial_width

            for i in range(loops):
                p.n_iter = 1
                p.batch_size = 1
                p.do_not_save_grid = True
                p.control_net_input_image = Image.open(reference_imgs[i].name).convert("RGB").resize(
                    (initial_width, p.height), Image.ANTIALIAS)

                if (i > 0):
                    loopback_image = p.init_images[0]
                    if loopback_source == "InputFrame":
                        loopback_image = p.control_net_input_image
                    elif loopback_source == "FirstGen":
                        loopback_image = history[0]

                    if third_frame_image != "None" and i > 1:
                        p.width = initial_width * 3
                        img = Image.new("RGB", (initial_width * 3, p.height))
                        img.paste(p.init_images[0], (0, 0))
                        # img.paste(p.init_images[0], (initial_width, 0))
                        img.paste(loopback_image, (initial_width, 0))
                        img.paste(third_image, (initial_width * 2, 0))
                        p.init_images = [img]
                        if color_correction_enabled:
                            p.color_corrections = [processing.setup_color_correction(img)]

                        msk = Image.new("RGB", (initial_width * 3, p.height))
                        msk.paste(
                            Image.open(reference_imgs[i - 1].name).convert("RGB").resize((initial_width, p.height),
                                                                                         Image.ANTIALIAS), (0, 0))
                        msk.paste(p.control_net_input_image, (initial_width, 0))
                        msk.paste(Image.open(reference_imgs[third_image_index].name).convert("RGB").resize(
                            (initial_width, p.height), Image.ANTIALIAS), (initial_width * 2, 0))
                        p.control_net_input_image = msk

                        latent_mask = Image.new("RGB", (initial_width * 3, p.height), "black")
                        latent_draw = ImageDraw.Draw(latent_mask)
                        latent_draw.rectangle((initial_width, 0, initial_width * 2, p.height), fill="white")
                        p.image_mask = latent_mask
                        p.denoising_strength = original_denoise
                    else:
                        p.width = initial_width * 2
                        img = Image.new("RGB", (initial_width * 2, p.height))
                        img.paste(p.init_images[0], (0, 0))
                        # img.paste(p.init_images[0], (initial_width, 0))
                        img.paste(loopback_image, (initial_width, 0))
                        p.init_images = [img]
                        if color_correction_enabled:
                            p.color_corrections = [processing.setup_color_correction(img)]

                        msk = Image.new("RGB", (initial_width * 2, p.height))
                        msk.paste(
                            Image.open(reference_imgs[i - 1].name).convert("RGB").resize((initial_width, p.height),
                                                                                         Image.ANTIALIAS), (0, 0))
                        msk.paste(p.control_net_input_image, (initial_width, 0))
                        p.control_net_input_image = msk
                        frames.append(msk)

                        # latent_mask = Image.new("RGB", (initial_width*2, p.height), "white")
                        # latent_draw = ImageDraw.Draw(latent_mask)
                        # latent_draw.rectangle((0,0,initial_width,p.height), fill="black")
                        latent_mask = Image.new("RGB", (initial_width * 2, p.height), "black")
                        latent_draw = ImageDraw.Draw(latent_mask)
                        latent_draw.rectangle((initial_width, 0, initial_width * 2, p.height), fill="white")

                        # p.latent_mask = latent_mask
                        p.image_mask = latent_mask
                        p.denoising_strength = original_denoise
                else:
                    latent_mask = Image.new("RGB", (initial_width, p.height), "white")
                    # p.latent_mask = latent_mask
                    p.image_mask = latent_mask
                    p.denoising_strength = first_denoise
                    p.control_net_input_image = p.control_net_input_image.resize((initial_width, p.height))
                    frames.append(p.control_net_input_image)

                if append_interrogation != "None":
                    p.prompt = original_prompt + ", " if original_prompt != "" else ""
                    if append_interrogation == "CLIP":
                        p.prompt += shared.interrogator.interrogate(p.init_images[0])
                    elif append_interrogation == "DeepBooru":
                        p.prompt += deepbooru.model.tag(p.init_images[0])

                state.job = f"Iteration {i + 1}/{loops}, batch {n + 1}/{batch_count}"

                processed = processing.process_images(p)

                if initial_seed is None:
                    initial_seed = processed.seed
                    initial_info = processed.info

                init_img = processed.images[0]
                if (i > 0):
                    init_img = init_img.crop((initial_width, 0, initial_width * 2, p.height))

                if third_frame_image != "None":
                    if third_frame_image == "FirstGen" and i == 0:
                        third_image = init_img
                        third_image_index = 0
                    elif third_frame_image == "GuideImg" and i == 0:
                        third_image = original_init_image[0]
                        third_image_index = 0
                    elif third_frame_image == "Historical":
                        third_image = processed.images[0].crop((0, 0, initial_width, p.height))
                        third_image_index = (i - 1)

                p.init_images = [init_img]
                if (freeze_seed):
                    p.seed = processed.seed
                else:
                    p.seed = processed.seed + 1

                history.append(init_img)
                if opts.samples_save:
                    # images.save_image(init_img, p.outpath_samples, "Frame", p.seed, p.prompt, opts.grid_format,
                    #                   info=info, short_filename=not opts.grid_extended_filename, grid=True, p=p)
                    fileName = os.path.basename(reference_imgs[i].name).split(".")[0]
                    images.save_image(init_img, videoHelper.outputDir, "Frame", p.seed, p.prompt, opts.grid_format,
                                      info=info, short_filename=not opts.grid_extended_filename, grid=True, p=p,
                                      save_to_dirs=False, forced_filename=fileName)

                frames.append(processed.images[0])

            grid = images.image_grid(history, rows=1)
            if opts.grid_save:
                images.save_image(grid, videoHelper.workspace + "/grid", "grid", initial_seed, p.prompt,
                                  opts.grid_format, info=info, short_filename=not opts.grid_extended_filename,
                                  grid=True,
                                  p=p, save_to_dirs=False)

            grids.append(grid)
            # all_images += history + frames
            all_images += history

            p.seed = p.seed + 1

        if opts.return_grid:
            all_images = grids + all_images

        processed = Processed(p, all_images, initial_seed, initial_info)

        videoHelper.img2VideoN(fpsSlider)
        return processed
