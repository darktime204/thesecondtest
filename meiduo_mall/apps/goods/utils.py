# 获取 面包屑组件的数据

def get_breadcrumb(cat3):
    # 三级
    # 二级
    cat2 = cat3.parent
    # 一级 id name, url
    cat1 = cat2.parent

    breadcrumb = {
        'cat1': {
            "id": cat1.id,
            'name': cat1.name,
            # 一级分类--->频道表---url属性
            'url': cat1.goodschannel_set.all()[0].url
        },
        'cat2': cat2,
        "cat3": cat3
    }
    return breadcrumb
