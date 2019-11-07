from apps.goods.models import GoodsChannel
from collections import OrderedDict

# 封装 获取 三级分类 数据函数
def get_categories():
    categories = OrderedDict()
    # - 1.获取所有的频道 37个
    channels = GoodsChannel.objects.order_by('group_id', 'sequence')
    #   2.遍历所有的频道:
    for channel in channels:
        #   - ​	组id= 每一个频道.grou_id
        group_id = channel.group_id

        if group_id not in categories:
            categories[group_id] = {'channels': [], 'sub_cats': []}

        # - 3.一级分类 =  频道.category
        cat1 = channel.category
        cat1.url = channel.url
        categories[group_id]['channels'].append(cat1)

        # - 4.二级分类= 一级.subs.all()
        for cat2 in cat1.subs.all():
            cat2.sub_cats = []
            # - 5.三级==二级.subs.all()
            for cat3 in cat2.subs.all():
                cat2.sub_cats.append(cat3)

            categories[group_id]['sub_cats'].append(cat2)


    return categories