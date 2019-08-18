from django.conf.urls import url
from django.shortcuts import render, redirect
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.db.models import Q
from django.db.models.fields.related import ManyToManyField


class ShowList(object):
    def __init__(self,config,request,datalist):
        self.config=config
        self.request =request
        self.datalist =datalist
        url = self.request.path
        page_num =self.request.GET.get("page")
        count = self.datalist.count()
        from Ladmin.footprint.mypage import Page
        self.page_obj = Page(page_num, count, url,self.request.GET)
        self.page_html = self.page_obj.page_html()
        # 在queryset情况下才能切片
        self.page_list =self.datalist[self.page_obj.start:self.page_obj.end]
        self.actions=self.config.get_new_actions()

    def get_filter_linktags(self):
        print("list_filter:",self.config.list_filter)
        link_dic={}
        import copy
        for filter_field in self.config.list_filter: # ["title","publish","authors",]
            params = copy.deepcopy(self.request.GET)

            cid=self.request.GET.get(filter_field,0)

            print("filter_field",filter_field) # "publish"
            filter_field_obj=self.config.model._meta.get_field(filter_field)
            print("filter_field_obj",filter_field_obj)
            print(type(filter_field_obj))
            from django.db.models.fields.related import ForeignKey
            from django.db.models.fields.related import ManyToManyField
            print("rel======...",filter_field_obj.rel)

            if isinstance(filter_field_obj,ForeignKey) or isinstance(filter_field_obj,ManyToManyField):
                 data_list=filter_field_obj.rel.to.objects.all()# 【publish1,publish2...】
            else:
                 data_list=self.config.model.objects.all().values("pk",filter_field)
                 print("data_list",data_list)


            temp=[]
            # 处理 全部标签
            if params.get(filter_field):
                del params[filter_field]
                temp.append("<a href='?%s'>全部</a>"%params.urlencode())
            else:
                temp.append("<a  class='active' href='#'>全部</a>")

            # 处理 数据标签
            for obj in data_list:
                if isinstance(filter_field_obj,ForeignKey) or isinstance(filter_field_obj,ManyToManyField):
                    pk=obj.pk
                    text=str(obj)
                    params[filter_field] = pk
                else: # data_list= [{"pk":1,"title":"go"},....]
                    print("========")
                    pk=obj.get("pk")
                    text=obj.get(filter_field)
                    params[filter_field] =text


                _url=params.urlencode()
                if cid==str(pk) or cid==text:
                     link_tag="<a class='active' href='?%s'>%s</a>"%(_url,text)
                else:
                    link_tag = "<a style='color:grey' href='?%s'>%s</a>" % (_url, text)
                temp.append(link_tag)

            link_dic[filter_field]=temp

        return link_dic
    def get_action_list(self):
        temp=[]
        for action in self.actions:
            temp.append({
                "name":action.__name__,
                "desc":action.short_description
            })
        return temp

    def get_header_list(self):
        # 构建表头
        header_list = []
        print("header", self.config.new_list_play())

        for field in self.config.new_list_play():

            if callable(field):
                # header_list.append(field.__name__)
                val = field(self.config, header=True)
                header_list.append(val)

            else:
                if field == "__str__":
                    header_list.append(self.config.model._meta.model_name.upper())
                else:
                    # header_list.append(field)
                    val = self.config.model._meta.get_field(field).verbose_name
                    header_list.append(val)
        return header_list

    def get_body(self):
        # 构建表单数据
        new_data_list = []
        for obj in self.page_list:
            temp = []

            for filed in self.config.new_list_play():  # ["__str__",]      ["pk","name","age",edit]

                if callable(filed):
                    val = filed(self.config, obj)
                else:
                    try:
                        field_obj = self.config.model._meta.get_field(filed)
                        if isinstance(field_obj, ManyToManyField):
                            ret = getattr(obj, filed).all()
                            t = []
                            for i in ret:
                                t.append(str(i))
                            val = ",".join(t)

                        else:
                            if field_obj.choices:
                                val = getattr(obj, "get_" + filed + "_display")
                            else:
                                val = getattr(obj, filed)
                            if filed in self.config.list_display_links:
                                # "app01/userinfo/(\d+)/change"
                                _url = self.config.get_change_url(obj)

                                val = mark_safe("<a href='%s'>%s</a>" % (_url, val))

                    except Exception as e:
                        print("field是什么",filed)
                        val = getattr(obj, filed)
                        print("val是什么",val)
                temp.append(val)
            new_data_list.append(temp)
        return new_data_list




class ModelLadmin(object):
    list_display_links=[]
    modelform_class=None
    list_display=["__str__"]
    search_fields=[]
    actions=[]
    list_filter =[]
    def __init__(self,model,site):
        self.model = model
        self.site =site

    def delete_selected(self, request, queryset):
        queryset.delete()

    delete_selected.short_description = "删除所选对象"

    def get_new_actions(self):
        temp=[]
        temp.append(ModelLadmin.delete_selected)
        temp.extend(self.actions)
        return temp


    def edit(self,obj=None, header=False):
        if header:
            return "操作"
        else:
            url =self.get_change_url(obj)
            return mark_safe("<a href='%s'class ='btn btn-primary '>编辑</a>"%url)

    def delete(self,obj=None,header=False,):
        #先传对象，再传字段
        if header:
            return "删除"
        print(123)
        url = self.get_delete_url(obj)
        print(123)
        return mark_safe("<a href=%s class='btn btn-primary'>删除</a>"%url)

    def checkbox(self,obj=None,header=False):
        if header:
            return mark_safe('<input id="choice" type="checkbox">')

        return mark_safe('<input class="choice_item" type="checkbox" name="selected_pk" value=%s>'%obj.pk)

    def new_list_play(self):
        temp = []
        temp.append(ModelLadmin.checkbox)
        temp.extend(self.list_display)
        if not self.list_display_links:
            temp.append(ModelLadmin.edit)
        temp.append(ModelLadmin.delete)
        return temp


    def get_search_condition(self,request):
        search_condition = request.GET.get("search","")
        self.search_condition = search_condition

        search_connection = Q()
        if search_condition:
            # self.search_fields # ["title","price"]
            search_connection.connector = "or"
            for search_field in self.search_fields:
                search_connection.children.append((search_field + "__contains", search_condition))
        return search_connection

    def get_filter_condition(self, request):
        filter_condition = Q()
        for filter_field, val in request.GET.items():
            if filter_field != "page":
                filter_condition.children.append((filter_field, val))

        return filter_condition
    def list_view(self,request):
        username = request.session["user_name"]
        print(username)
        if request.method=="POST":
            print("POST:", request.POST)
            action = request.POST.get("action")
            selected_pk = request.POST.getlist("selected_pk")
            action_func = getattr(self, action)
            queryset = self.model.objects.filter(pk__in=selected_pk)
            ret = action_func(request, queryset)
        search_condition = self.get_search_condition(request)
        # 获取filter构建Q对象
        filter_condition = self.get_filter_condition(request)
        # 筛选获取当前表所有数据
        data_list = self.model.objects.all().filter(search_condition).filter(filter_condition)  # 【obj1,obj2,....】
        showlist=ShowList(self,request,data_list )
        add_url = self.get_add_url()
        print("*"*120)
        print("local是什么",locals())
        # return render(request, "list_view.html", {"header_list":header_list,"new_data_list":new_data_list})
        return render(request, "list_view.html",locals())

    def delete_view(self,request,id):
        # 字符串参数最后一个传#
        url = self.get_list_url()
        if request.method=="POST":
            self.model.objects.filter(pk=id).first().delete()
            return redirect(url)


        return render(request, 'delete_view.html',locals())


    def change_view(self,request,id):
        model_form_demo = self.get_modelform()
        edit_obj = self.model.objects.filter(pk=id).first()
        if request.method=="POST":
            form=model_form_demo(request.POST,instance=edit_obj)
            if form.is_valid():
                form.save()
                return redirect(self.get_list_url())
            return render(request, 'change_view.html', locals())
        form =model_form_demo(instance=edit_obj)
        return render(request, 'change_view.html',locals())

    def get_modelform(self):
        if not self.modelform_class:
            from django.forms import ModelForm

            class ModelFormdemo(ModelForm):
                class Meta:
                    model =self.model
                    fields ="__all__"
                    label =""

            return ModelFormdemo
        else:
            return self.modelform_class

    def add_view(self,request):
        ModelFormDemo = self.get_modelform()
        form = ModelFormDemo()
        for bfield in form:
            print(bfield.field)  # 字段对象
            print("name", bfield.name)  # 字段名（字符串）
            print(type(bfield.field))  # 字段类型
            from django.forms.models import ModelChoiceField
            if isinstance(bfield.field, ModelChoiceField):
                bfield.is_pop = True

                print("=======>", bfield.field.queryset.model)  # 一对多或者多对多字段的关联模型表

                related_model_name = bfield.field.queryset.model._meta.model_name
                related_app_label = bfield.field.queryset.model._meta.app_label

                _url = reverse("%s_%s_add" % (related_app_label, related_model_name))
                bfield.url = _url + "?pop_res_id=id_%s" % bfield.name
        if request.method == "POST":
            form = ModelFormDemo(request.POST)
            if form.is_valid():
                obj = form.save()
                pop_res_id = request.GET.get("pop_res_id")
                if pop_res_id:
                    res = {"pk": obj.pk, "text": str(obj), "pop_res_id": pop_res_id}
                    return render(request, "pop.html", {"res": res})
                else:
                    return redirect(self.get_list_url())
        return render(request, "add_view.html", locals())

    def extra_url(self):
        return []

    def get_urls2(self):
        tmp =[]
        app_name = self.model._meta.app_label
        model_name = self.model._meta.model_name
        tmp.append(url(r"^\w*$",self.list_view,name="%s_%s_list"%(app_name,model_name)))
        tmp.append(url(r"^add/",self.add_view,name="%s_%s_add"%(app_name,model_name)))
        tmp.append(url(r"^(\d+)/change/$",self.change_view,name="%s_%s_change"%(app_name,model_name)))

        tmp.append(url(r"^(\d+)/delete/$", self.delete_view,name="%s_%s_delete"%(app_name,model_name)))
        tmp.extend(self.extra_url())
        return tmp

    def get_change_url(self,obj):
        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label

        _url = reverse("%s_%s_change" % (app_label, model_name), args=(obj.pk,))

        return _url

    def get_delete_url(self, obj):
        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label

        _url = reverse("%s_%s_delete" % (app_label, model_name), args=(obj.pk,))

        return _url


    def get_add_url(self):

        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label

        _url = reverse("%s_%s_add" % (app_label, model_name))

        return _url

    def get_list_url(self):

        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label

        _url = reverse("%s_%s_list" % (app_label, model_name))

        return _url

    @property
    def urls2(self):
        return self.get_urls2(),None,None


class Ladminsite(object):
    def __init__(self, name='Ladmin'):
        self._registry = {}
        self.name = name

    def register(self, model, Ladmin_class=None, **options):
        if not Ladmin_class:
            Ladmin_class = ModelLadmin
        self._registry[model] = Ladmin_class(model, self)

    def get_urls(self):
        print(self._registry)
        url_list =[]
        for model,Ladmin_class_obj in self._registry.items():
            app_name = model._meta.app_label
            model_name =model._meta.model_name
            print(app_name,model_name)
            url1 =url(r'^/{0}/{1}/'.format(app_name,model_name),Ladmin_class_obj.urls2)
            print(url1)
            url_list.append(url1)
        return  url_list


    @property
    def urls(self):
        return self.get_urls(),None,None

site=Ladminsite()