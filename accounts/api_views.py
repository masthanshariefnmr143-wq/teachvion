from rest_framework import serializers, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'role',
                  'phone', 'bio', 'profile_pic', 'created_at']
        read_only_fields = ['id', 'email', 'role', 'created_at']


class RegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=['student', 'trainer', 'admin'])
    password = serializers.CharField(min_length=6, write_only=True)

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("Email already registered.")
        return value.lower()

    def create(self, validated_data):
        return CustomUser.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            role=validated_data['role'],
        )


class RegisterAPIView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            'message': 'Account created successfully.',
            'user': UserSerializer(user).data
        }, status=201)


class ProfileAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user