# 1.说明
目前该爬虫有且仅有一个功能：爬取Facebook上`与关键词相关的`、`最近的`、`N条`帖子

# 2.快速开始
配置依赖
```shell
python3 -m pip install -r requirements.txt
```
启动爬虫
```python
import os
from app.spider import FacebookSpider

os.environ['SPIDER_SAVE_PATH'] = 'your-path'  # 默认为项目目录下的./data

spider = FacebookSpider('user', 'password', headless=False)
spider.search('keyword', max_posts=100)
```

# 3.返回示例

| 参数名                  | 类型   | 说明       | 示例                                   |
|----------------------|------|----------|--------------------------------------|
| user_home_page       | str  | 发帖人主页url | 略                                    |
| user_name            | str  | 发帖人用户名   |                                      |
| user_profile         | str  | 发帖人头像图片  | 略                                    |
| user_followers_count | str  | 发帖人粉丝数   | "1.6k"                               |
| post_url             | str  | 帖子url    | 略                                    |
| content              | str  | 帖子内容     | 略                                    |
| img_links            | list | 图片链接     | 略                                    |
| likes                | str  | 点赞数      | "1.1k"                               |
| comments             | str  | 评论数      | "0"                                  |
| shares               | str  | 转发数      | "0"                                  |
| create_time          | str  | 发帖日期     | "Monday, August 28, 2023 at 3:06 PM" |


