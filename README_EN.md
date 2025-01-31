**English** | [简体中文](./README.md)

---


## Read Documents

Please read the following document and deploy NapCatQQ, install the NoneBot scaffolding, and create a Simple template NoneBot project.

- [NoneBot ](https://nonebot.dev/)
- [NapCatQQ](https://github.com/NapNeko/NapCatQQ)

## Deployment Steps

- Clone this project and replace the files.
- Modify the values in `.env.template` for `ONEBOT_WS_URLS`, `SUPERUSERS`, `GROUP_WHITELIST`, `SHENGJING_DB_PATH`, `SHENGJING_IMG_DIR_PATH`, and `PLUS_ONE_WHITE_LIST` to your own configurations.
- Rename `.env.template` to `.env`.
- Run `nb run` in the project directory, and install any missing plugins by following the error messages with `nb plugin install <plugin_name>`.
- Once all missing plugins are installed, run `nb run` to start NoneBot.
