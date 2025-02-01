from io import BytesIO

import requests
from sqlalchemy import Column, Integer, String, Date, create_engine, text

from src.plugins.shengjing.config import PIC_TOKEN


class QrSj:
    """
    Description: sj系统图片对象
    """
    __tablename__ = 'qr_sj'
    # 图片id，一般不用管
    id = Column(Integer, primary_key=True)
    # 本地图片路径，为预留字段，不用管
    img_path = ""
    # 图片名称，使用uuid4生成
    img_name = ""
    # 图片备注，用于搜索
    img_note = ""
    # 图片权重，预留字段，不用管
    img_seq = 0
    # 图片获取链接，图床返回
    url_get = ""
    # 图片删除链接，图床返回
    url_delete = ""
    # 上传者，从event中获取
    upload_by = ""
    # 上传时间，系统时间自动生成
    upload_time = ""
    # 所属群组，从event中获取
    belong_group = ""
    # 是否删除，0为已删除，1为未删除
    is_deleted = 0
    # 图片在当前群组的id，用于获取图片
    group_id = 0

    def __repr__(self):
        return (
            "QrSj(id:{},img_path:{},img_name:{},img_note:{},img_seq:{},url_get:{},url_delete:{},upload_by:{},upload_time:{})"
            .format(self.id, self.img_path, self.img_name, self.img_note, self.img_seq, self.url_get, self.url_delete,
                    self.upload_by, self.upload_time))

    def imgUpload(self, file_data):
        """
        Description: 将图片上传至图床
        Args:
            file_data: 从链接获取的图片二进制数据

        Returns: 上传结果，成功返回True，失败返回错误信息（图片路径自动写入当前对象）

        """
        # 需在.env.prod中配置图床token
        headers = {'Authorization': PIC_TOKEN}
        # 处理图片数据为IO流，便于添加文件名称
        img_stream = BytesIO(file_data)
        img_stream.name = self.img_name
        # 构建文件流，图床需要将图片流放入smfile字段
        files = {'smfile': img_stream}
        # 图床链接
        url = 'https://sm.ms/api/v2/upload'

        # 发送请求
        res = requests.post(url, files=files, headers=headers).json()
        if res.get('code') != 'success':
            print("[Error] Upload image failed.")
            return res.get('code')
        data = res.get('data')

        # 将获取及删除链接写入对象
        self.url_get = data.get('url')
        self.url_delete = data.get('delete')
        print("[Info] File image URL is: " + self.url_get)
        return "True"

