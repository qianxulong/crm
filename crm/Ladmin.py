from Ladmin.service.Ladmin import site, ModelLadmin
from .models import *
from django.utils.safestring import mark_safe
from django.conf.urls import url
from django.shortcuts import render,redirect
from django.http import JsonResponse
from django.shortcuts import HttpResponse

site.register(ClassList)
class ConsultConfig(ModelLadmin):
    list_display = ["customer", "consultant", "date", "note"]
site.register(ConsultRecord, ConsultConfig)
site.register(Course)



class CourseRecordConfig(ModelLadmin):
    def record(self, obj=None, header=False):
        if header:
            return "考勤"
        return mark_safe("<a href='/ladmin/crm/studyrecord/?course_record=%s'>记录</a>" % obj.pk)

    def record_score(self, obj=None, header=False):
        if header:
            return "录入成绩"
        return mark_safe("<a href='record_score/%s'>录入成绩</a>" % obj.pk)

    def score(self,request,course_record_id):
        if request.method == "POST":
            print(request.POST)

            data = {}
            for key, value in request.POST.items():
                if key == "csrfmiddlewaretoken": continue
                field, pk = key.rsplit("_", 1)
                if pk in data:
                    data[pk][field] = value
                else:
                    data[pk] = {field: value}  # data  {4:{"score":90}}

            print("data", data)

            for pk, update_data in data.items():
                StudyRecord.objects.filter(pk=pk).update(**update_data)

            return redirect(request.path)
        study_record_list=StudyRecord.objects.filter( course_record =course_record_id)
        score_choices = StudyRecord.score_choices
        return render(request, "score.html", locals())

    def extra_url(self):
        temp=[]
        temp.append(url("^record_score/(\d+)",self.score))
        return temp

    list_display = ["class_obj", "day_num", "course_title",record,record_score]

    def patch_studyrecord(self, request, queryset):
        temp = []
        for course_record in queryset:
            all_student = Student.objects.filter(class_list__id=course_record.class_obj.pk)
            for student in all_student:
                obj = StudyRecord(student=student, course_record=course_record)
                temp.append(obj)
        StudyRecord.objects.bulk_create(temp)
    patch_studyrecord.short_description = "批量生成学习记录"
    actions=[patch_studyrecord]



site.register(CourseRecord, CourseRecordConfig)

class CusotmerConfig(ModelLadmin):
    def display_gender(self, obj=None, header=False):
        if header:
            return "性别"
        return obj.get_gender_display()


    def display_course(self, obj=None, header=False):
        if header:
            return "咨询课程"
        temp = []
        for course in obj.course.all():
            s = "<a href='/stark/crm/customer/cancel_course/%s/%s' style='border:1px solid #369;padding:3px 6px'><span>%s</span></a>&nbsp;" % (
                obj.pk, course.pk, course.name,)
            temp.append(s)
        return mark_safe("".join(temp))

    def cancel_course(self, request, customer_id, course_id):
        print(customer_id, course_id)

        obj = Customer.objects.filter(pk=customer_id).first()
        obj.course.remove(course_id)
        return redirect(self.get_list_url())

    def public_customer(self,request):
        from django.db.models import Q
        import datetime
        user_id =request.session["user_id"]
        now =datetime.datetime.now()
        day15 =datetime.timedelta(days=15)
        day3= datetime.timedelta(days=3)
        # 三天未跟进 now-last_consult_date>3   --->last_consult_date<now-3
        # 15天未成单 now-recv_date>15   --->recv_date<now-15


        public_customer =Customer.objects.filter(Q( recv_date__lt=now-day15)|Q(last_consult_date__lt=now-day3),status =2).exclude(consultant=user_id)
        return render(request,"public.html",locals())

    def further(self,request,customer_id):
        from django.db.models import Q
        import datetime
        user_id =2
        now = datetime.datetime.now()
        day15 = datetime.timedelta(days=15)
        day3 = datetime.timedelta(days=3)
        ret =Customer.objects.filter(Q( recv_date__lt=now-day15)|Q(last_consult_date__lt=now-day3),status =2).filter(pk=customer_id).update(consultant=user_id,last_consult_date=now,recv_date=now)
        if not ret:
            return HttpResponse("已经被跟进了")

        CustomerDistrbute.objects.create(customer_id=customer_id,consultant_id=user_id,date=now,status=1)

        return HttpResponse("跟进成功")
    def mycustomer(self,request):
        user_id=3
        customer_distrbute_list=CustomerDistrbute.objects.filter(consultant=user_id)

        return render(request, "mycustomer.html", locals())

    def extra_url(self):

        temp = []

        temp.append(url(r"cancel_course/(\d+)/(\d+)", self.cancel_course))
        temp.append(url(r"public/", self.public_customer))
        temp.append(url(r"further/(\d+)", self.further))
        temp.append(url(r"mycustomer/", self.mycustomer))

        return temp
    list_display = ["name", display_gender, display_course, "consultant", ]

site.register(Customer,CusotmerConfig)

class CustomerDistrbuteConfig(ModelLadmin):
    list_display = ["customer","consultant","date","status"]
site.register(CustomerDistrbute,CustomerDistrbuteConfig)



site.register(Department)
site.register(School)


class StudentConfig(ModelLadmin):

    def score_show(self,obj=None,header=False):
        if header:
            return "查看成绩"
        else:
            return mark_safe("<a href='/ladmin/crm/student/score_view/%s'>点击查看</a>"%obj.pk)


    def score_view(self,request,student_id):
        if request.is_ajax():

            print(request.GET)

            sid = request.GET.get("sid")
            cid = request.GET.get("cid")

            study_record_list = StudyRecord.objects.filter(student=sid, course_record__class_obj=cid)

            data_list = []

            for study_record in study_record_list:
                day_num = study_record.course_record.day_num
                data_list.append(["day%s" % day_num, study_record.score])
            print(data_list)
            return JsonResponse(data_list, safe=False)
        else:
            student = Student.objects.filter(pk=student_id).first()
            class_list = student.class_list.all()

            return render(request, "score_view.html", locals())

    def extra_url(self):
        temp = []
        temp.append(url("^score_view/(\d+)", self.score_view))
        return temp
    list_display = ["username", "class_list",score_show]
site.register(Student, StudentConfig)


class StudyRecordConfig(ModelLadmin):
    list_display = ["student","course_record","record","score"]
    def patch_late(self, request, queryset):
        queryset.update(record="late")

    patch_late.short_description = "迟到"
    actions = [patch_late]

site.register(StudyRecord,StudyRecordConfig)
site.register(UserInfo)
