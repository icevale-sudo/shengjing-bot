[English](./README_EN.md) | **简体中文**

---

## 阅读文档

请阅读以下文档，并部署NapCatQQ、安装NoneBot脚手架、创建Simple模板的NoneBot项目。

- [NoneBot ](https://nonebot.dev/)
- [NapCatQQ](https://github.com/NapNeko/NapCatQQ)


## 部署步骤

- 搭建Python v3.9+裸机或虚拟环境
- NoneBot环境准备
  - 参考文档安装NoneBot
  - 创建`simple`模板
    - 使用OneBot v11 API
    - 保存路径使用`src`
    - 安装依赖
    - 不建立虚拟环境
  - 将生成的`src`目录中的`pyproject.toml`复制到此文件夹下，其他文件可以移除
- 依赖项
  - Python安装`aiosqlite`包
  ```bash
  pip install aiosqlite
  ```
  - Nonebot安装可选插件`nonebot-plugin-plus-one`和`nonebot-plugin-dialectlist`
  ```bash
  nb plugin install nonebot-plugin-plus-one

  nb plugin install nonebot-plugin-orm
  pip install "nonebot-plugin-orm[sqlite]"
  nb plugin install nonebot-plugin-dialectlist
  ```
- 项目配置
  - 修改`.env.template`中的`ONEBOT_WS_URLS`、`SUPERUSERS`、`GROUP_WHITELIST`、`SHENGJING_DB_PATH`、`SHENGJING_IMG_DIR_PATH`、`PLUS_ONE_WHITE_LIST`至自己的配置
  - 重命名`.env.template`为`.env`
- Bot后端启动
  - 在项目目录下执行`nb run`，启动NoneBot
    - 若仍有报错信息，使用`nb plugin install <插件名>`安装缺失的插件
- 配置NapCatQQ进行连接
  - 注意使用古董版本-新版QQ插件似乎遭到狙击
  - 在网页配置界面中：
    - 启用正向WebSocket服务：`ws://<IP>:<port>`
    - 设置Access token为`ONEBOT_ACCESS_TOKEN`内容
    - 保存
