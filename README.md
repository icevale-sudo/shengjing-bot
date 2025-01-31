[English](./README_EN.md) | **简体中文**

---

## 阅读文档

请阅读以下文档，并部署NapCatQQ、安装NoneBot脚手架、创建Simple模板的NoneBot项目。

- [NoneBot ](https://nonebot.dev/)
- [NapCatQQ](https://github.com/NapNeko/NapCatQQ)

## 部署步骤

- 克隆本项目，替换文件。
- 修改`.env.prod`中的`HOST`、`PORT`、`SUPERUSERS`、`GROUP_WHITELIST`、`SHENGJING_DB_PATH`、`SHENGJING_IMG_DIR_PATH`、`PLUS_ONE_WHITE_LIST`至自己的配置。
- 在项目目录下执行`nb run`，并依据报错信息使用`nb plugin install <插件名>`安装缺失的插件。
- 所有缺失插件安装好后，执行`nb run`启动NoneBot。