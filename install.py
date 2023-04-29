import launch


if not launch.is_installed('ffmpeg'):
    print('Installing ffmpeg。。。。。')
    launch.run_pip("install ffmpeg", "requirements for ffmpeg")