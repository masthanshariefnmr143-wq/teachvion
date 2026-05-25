from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib import messages
from .models import Certificate, PartnerCompany
from courses.models import Course
from exams.models import ExamAttempt


# ─── Certificate hub (existing certificate page) ─────────────────
@login_required
def certificate_hub_view(request):
    certificates = Certificate.objects.filter(student=request.user).select_related('course', 'exam_attempt')
    return render(request, 'certificate_hub.html', {'certificates': certificates})


# ─── View single certificate (digital) ───────────────────────────
@login_required
def certificate_detail_view(request, cert_id):
    cert = get_object_or_404(Certificate, id=cert_id, student=request.user)
    return render(request, 'certificate_detail.html', {'cert': cert})


# ─── Choose delivery method ───────────────────────────────────────
@login_required
def certificate_delivery_view(request, cert_id):
    cert = get_object_or_404(Certificate, id=cert_id, student=request.user)

    if request.method == 'POST':
        method = request.POST.get('delivery_method')
        cert.delivery_method = method
        if method == 'post':
            address = request.POST.get('postal_address', '').strip()
            if not address:
                messages.error(request, "Please enter your postal address.")
                return render(request, 'delivery_choice.html', {'cert': cert})
            cert.postal_address = address
        cert.save()

        if method == 'pdf':
            return redirect('certificate_pdf', cert_id=cert.id)
        elif method == 'digital':
            return redirect('certificate_detail', cert_id=cert.id)
        else:
            messages.success(request, "Postal delivery requested. We'll mail it within 5-7 working days.")
            return redirect('certificate_hub')

    return render(request, 'delivery_choice.html', {'cert': cert})


# ─── Download PDF Certificate ─────────────────────────────────────
@login_required
def certificate_pdf_view(request, cert_id):
    cert = get_object_or_404(Certificate, id=cert_id, student=request.user)

    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        import io

        buffer = io.BytesIO()
        
        # 1. Define clean margins
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=landscape(A4), 
            leftMargin=0.4*inch, 
            rightMargin=0.4*inch, 
            topMargin=0.4*inch, 
            bottomMargin=0.4*inch
        )
        styles = getSampleStyleSheet()

        # 2. Typography Styles (FIXED: Added proportional leading to prevent overlaps)
        brand_style = ParagraphStyle(
            'BrandLogo', fontSize=32, leading=38, alignment=1, fontName="Helvetica-Bold",
            textColor=colors.HexColor('#5a67d8'), spaceAfter=2
        )
        subtitle_style = ParagraphStyle(
            'CertSubtitle', fontSize=10, leading=14, alignment=1, fontName="Helvetica",
            textColor=colors.HexColor('#94a3b8'), spaceAfter=25
        )
        intro_style = ParagraphStyle(
            'IntroText', fontSize=13, leading=18, alignment=1, fontName="Helvetica",
            textColor=colors.HexColor('#475569'), spaceAfter=12
        )
        name_style = ParagraphStyle(
            'StudentName', fontSize=38, leading=46, alignment=1, fontName="Helvetica-Bold",
            textColor=colors.HexColor('#0f172a'), spaceAfter=12
        )
        course_style = ParagraphStyle(
            'CourseTitle', fontSize=22, leading=28, alignment=1, fontName="Helvetica-Bold",
            textColor=colors.HexColor('#5a67d8'), spaceAfter=20
        )
        badge_style = ParagraphStyle(
            'BadgeText', fontSize=11, leading=14, alignment=1, fontName="Helvetica-Bold",
            textColor=colors.white
        )
        sig_title = ParagraphStyle(
            'SigTitle', fontSize=11, leading=15, alignment=1, fontName="Helvetica-Bold", textColor=colors.HexColor('#1e293b')
        )
        sig_sub = ParagraphStyle(
            'SigSub', fontSize=9, leading=12, alignment=1, fontName="Helvetica", textColor=colors.HexColor('#94a3b8')
        )
        meta_text = ParagraphStyle(
            'MetaText', fontSize=9, leading=12, alignment=1, fontName="Helvetica", textColor=colors.HexColor('#94a3b8')
        )
        meta_code = ParagraphStyle(
            'MetaCode', fontSize=10, leading=14, alignment=1, fontName="Helvetica-Bold", textColor=colors.HexColor('#5a67d8')
        )

        story = []
        icon_url = "https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/72x72/1f393.png"
        
        title_html = f'<img src="{icon_url}" width="32" height="32" valign="middle"/> Teachvion'
        story.append(Paragraph(title_html, brand_style))
        story.append(Paragraph("CERTIFICATE OF COMPLETION", subtitle_style))
        story.append(Spacer(1, 15))

          # ── Credential Statements
        story.append(Paragraph("This is to certify that", intro_style))
        story.append(Paragraph(cert.student.get_full_name(), name_style))
        story.append(Paragraph("has successfully completed the course", intro_style))
        story.append(Paragraph(cert.course.title, course_style))
        story.append(Spacer(1, 5))

        # ── Distinction Pill Badge
        score_pct = cert.exam_attempt.percentage if cert.exam_attempt else 0.0
        badge_html = Paragraph(f"Score: {score_pct:.1f}%  •  Awarded Distinction", badge_style)
        
        badge_table = Table([[badge_html]], colWidths=[260])
        badge_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#134e5e')),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 8),
        ]))
        
        badge_wrapper = Table([[badge_table]], colWidths=[700])
        badge_wrapper.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))
        story.append(badge_wrapper)
        story.append(Spacer(1, 45))

        # ── Footer Signatures & Meta Verification Block
        col1 = [
            Spacer(1, 15),
            Paragraph("Teachvion Team", sig_title),
            Paragraph("Director of Education", sig_sub)
        ]
        
        col2 = [
            Paragraph(cert.certificate_number, meta_code),
            Spacer(1, 4),
            Paragraph(cert.issued_at.strftime('%d %b %Y'), meta_text)
        ]
        
        trainer_name = cert.course.trainer.get_full_name() if cert.course.trainer else "Course Instructor"
        col3 = [
            Spacer(1, 15),
            Paragraph(trainer_name, sig_title),
            Paragraph("Course Instructor", sig_sub)
        ]

        footer_table = Table([ [col1, col2, col3] ], colWidths=[230, 180, 230])
        footer_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('LINEABOVE', (0,0), (0,0), 0.75, colors.HexColor('#cbd5e1')),
            ('LINEABOVE', (2,0), (2,0), 0.75, colors.HexColor('#cbd5e1')),
        ]))
        story.append(footer_table)

        # ── Outer Layout Border Frame Definition
        outer_frame = Table([[story]], colWidths=[740])
        outer_frame.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 2.0, colors.HexColor('#cbd5e1')), # Clean structural gray container frame
            ('TOPPADDING', (0,0), (-1,-1), 35),
            ('BOTTOMPADDING', (0,0), (-1,-1), 35),
            ('LEFTPADDING', (0,0), (-1,-1), 20),
            ('RIGHTPADDING', (0,0), (-1,-1), 20),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ]))

        # ── Canvas Background Function: Draws the purple corner accents precisely
        def draw_decorations(canvas, document):
            canvas.saveState()
            purple = colors.HexColor('#5a67d8')
            canvas.setStrokeColor(purple)
            canvas.setLineWidth(4)
            
            # Left Edge Horizontal Offset calculation bounds
            w, h = landscape(A4)
            pad = 20
            length = 40
            
            # Top-Left Corner Bracket Accent
            canvas.line(pad, h - pad, pad + length, h - pad)
            canvas.line(pad, h - pad, pad, h - (pad + length))
            
            # Top-Right Corner Bracket Accent
            canvas.line(w - pad, h - pad, w - (pad + length), h - pad)
            canvas.line(w - pad, h - pad, w - pad, h - (pad + length))
            
            # Bottom-Left Corner Bracket Accent
            canvas.line(pad, pad, pad + length, pad)
            canvas.line(pad, pad, pad, pad + length)
            
            # Bottom-Right Corner Bracket Accent
            canvas.line(w - pad, pad, w - (pad + length), pad)
            canvas.line(w - pad, pad, w - pad, pad + length)
            
            canvas.restoreState()

        # Build document with our dynamic canvas decorator callback
        doc.build([outer_frame], onFirstPage=draw_decorations)
        buffer.seek(0)
        
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="certificate_{cert.certificate_number}.pdf"'
        return response

    except ImportError:
        return render(request, 'certificate_detail.html', {
            'cert': cert, 'download_mode': True
        })

# ─── Partner companies (score >= 70%) ─────────────────────────────
@login_required
def partner_companies_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    attempt = ExamAttempt.objects.filter(
        student=request.user, course=course, eligible_for_partner=True
    ).order_by('-attempted_at').first()

    if not attempt:
        messages.error(request, "You need 70%+ to access partner companies.")
        return redirect('exam_result', attempt_id=0)

    partners = PartnerCompany.objects.filter(
        courses=course, is_active=True,
        min_score_required__lte=attempt.percentage
    )
    return render(request, 'partner_companies.html', {
        'partners': partners, 'course': course, 'attempt': attempt
    })