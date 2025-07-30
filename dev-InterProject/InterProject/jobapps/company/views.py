from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, viewsets
from .models import Company
from .serializers import CompanySerializer, SaveCompanySerializer
from ..middle.models import CompanyCode
from ..user.models import User


class CompanyViewSet(viewsets.ModelViewSet):
    authentication_classes = []
    queryset = Company.objects.all()
    serializer_class = CompanySerializer

    @action(detail=False, methods=['POST'], serializer_class=SaveCompanySerializer)
    def save(self, request):
        """
        创建公司账号
        """
        # 对传入数据进行序列化
        serializer = SaveCompanySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # 获取传入数据
        username = serializer.data['username']
        password = serializer.data['password']
        name = serializer.data['name']
        email = serializer.data['email']
        # 统一社会信用代码
        unifiedCode = serializer.data['unifiedCode']

        # 重复创建
        if Company.objects.filter(unifiedCode=unifiedCode).exists():
            return Response(status=status.HTTP_200_OK)

        # 创建企业
        company = Company.objects.create(name=name, unifiedCode=unifiedCode, email=email)

        # 为企业分配企业编号
        middle = CompanyCode.objects.filter(SHTYXYDM=unifiedCode).first()
        company.COMPANYID = middle.COMPANYID

        # 创建用户
        if not User.objects.filter(username=username).exists():  # 若用户不存在
            user = User.objects.create_user(username=username, password=password)
            user.save()
            # 外键关联
            company.user = user
            company.save()

        return Response(status=status.HTTP_200_OK)
