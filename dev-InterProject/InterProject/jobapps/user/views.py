from django.forms import model_to_dict
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action
from rest_framework.response import Response

from jobapps.student.models import Student
from jobapps.student.serializers import StudentSerializer
from jobapps.user.models import User
from jobapps.user.serializers import UserSerializer


class CustomAuthToken(ObtainAuthToken):
    authentication_classes = []
    permission_classes = []

    # permission_classes = [AllowAny]  # 允许任何人访问

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        """
        登录并获取token
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        # 返回用户信息
        return Response({
            'token': token.key,
            'status': status.HTTP_200_OK,
            'user': model_to_dict(user)
        })


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=False, methods=['GET'])
    def studentInfo(self, request):
        """
        获取学生个人信息
        """
        user = request.user
        # 根据用户id找到对应的学生
        student = Student.objects.filter(user_id=user.id).first()
        return Response(status=status.HTTP_200_OK, data=model_to_dict(student))

    @action(detail=False, methods=['GET'])
    def studentInfoById(self, request):
        """
        根据id获取学生个人信息
        """
        user_id = request.GET.get('id')
        # 根据用户id找到对应的学生
        student = Student.objects.filter(id=user_id).first()
        return Response(status=status.HTTP_200_OK, data=model_to_dict(student))

    @action(detail=False, methods=['POST'], serializer_class=StudentSerializer)
    def updateStudent(self, request):
        """
        学生修改个人信息
        """
        user = request.user
        # 根据用户id找到对应的学生
        student = Student.objects.filter(user_id=user.id).first()

        serializer = StudentSerializer(instance=student, data=request.data)
        serializer.is_valid(raise_exception=True)  # 进行数据验证,未通过则抛出异常
        # 保存修改后的个人信息
        serializer.update(instance=student, validated_data=request.data)

        # TODO 学生修改个人信息后,重新运行冷启动模型

        return Response(status=status.HTTP_200_OK, data=model_to_dict(student))

    @action(detail=False, methods=['GET'])
    def getToken(self, request):
        # 从请求中获取学生学号和姓名
        uid = request.GET.get('uid')
        name = request.GET.get('name')
        # 根据学号查找对应的学生
        student = Student.objects.filter(SID=uid).first()
        if not student:  # 没有找到对应的学生
            # 创建学生信息
            Student.objects.create(SID=uid, REALNAME=name)
            student = Student.objects.filter(SID=uid).first()
            # 为这个学生创建账户
            username = student.SID
            password = '123456'  # 密码默认设为123456
            if not User.objects.filter(username=username).exists():  # 若用户不存在
                user = User.objects.create_user(username=username, password=password)
                user.save()
                # 进行外键关联
                student.user = user
                student.save()
            # 返回token
            user = student.user
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'status': status.HTTP_200_OK,
                'user': model_to_dict(user)
            })
        else:
            # 获取学生对应的用户
            user = student.user
            # 为用户生成token
            token, created = Token.objects.get_or_create(user=user)

            # 返回用户信息
            return Response({
                'token': token.key,
                'status': status.HTTP_200_OK,
                'user': model_to_dict(user)
            })
