from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from .models import Certificate


class CertificateListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        certs = Certificate.objects.filter(student=request.user).select_related('course')
        return Response([{
            'id': c.id,
            'certificate_number': c.certificate_number,
            'course': c.course.title,
            'score': c.exam_attempt.percentage if c.exam_attempt else None,
            'issued_at': c.issued_at,
            'delivery_method': c.delivery_method,
        } for c in certs])