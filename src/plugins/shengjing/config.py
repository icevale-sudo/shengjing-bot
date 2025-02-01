from nonebot import get_driver

# Read config
config = get_driver().config
DB_PATH = config.shengjing_db_path
IMG_DIR_PATH = config.shengjing_img_dir_path
PIC_TOKEN=config.smms_api_token
