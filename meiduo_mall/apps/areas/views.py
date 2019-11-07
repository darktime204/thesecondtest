from django.http import JsonResponse
from django.views import View
from django.core.cache import cache

from apps.areas.models import Area


class AreasView(View):
    def get(self, request):
        # 判断 --省--市 --县

        # SQL
        # 省  select * from tb_areas where parent_id is null;
        # 市  select * from tb_areas where parent_id=130000;
        # 区  select * from tb_areas where parent_id=130100;

        # ORM
        # 省 Area.objects.filter(parent__isnull=True)
        # 市 Area.objects.filter(parent_id=值)
        # 区  Area.objects.filter(parent_id=值)


        # 1.解析参数
        area_id = request.GET.get('area_id')

        if not area_id:

            # 1.先去缓存取
            province_list = cache.get('province_list')

            # 2.如果 缓存没有 才去交互数据库
            if not province_list:
                # 省份
                provinces = Area.objects.filter(parent__isnull=True)

                province_list = [{'id': pro.id, "name": pro.name} for pro in provinces]

                cache.set('province_list', province_list, 3600)
                print('省份的 缓存数据')

            return JsonResponse({'code': 0, "errmsg": 'OK', 'province_list': province_list})
        else:

            sub_data = cache.get('sub_data_%s' % area_id)

            if not sub_data:
                # 第二种 先取父级--- 子级
                parent_data = Area.objects.get(id=area_id)
                cities = parent_data.subs.all()

                # 转换前端格式---->
                subs = []
                for city in cities:
                    subs.append({'id': city.id, 'name': city.name})

                sub_data = {
                    'id': parent_data.id,
                    "name": parent_data.name,
                    'subs': subs,
                }

                cache.set('sub_data_%s' % area_id, sub_data, 3600)

            return JsonResponse({'code': 0, "errmsg": 'OK', 'sub_data': sub_data})
