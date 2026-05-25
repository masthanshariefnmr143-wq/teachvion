from django import forms
from urllib.parse import parse_qs, urlparse
from .models import Lesson, ClassTiming, Course


def normalize_video_url(url):
    """
    Converts any YouTube / Vimeo URL to the embeddable form.
    Returns the embed URL string, or None if it cannot be normalized.
    If the URL is already an embed URL, return it as-is.
    """
    if not url:
        return None

    url = url.strip()

    # Already an embed URL — return immediately
    if '/embed/' in url or 'player.vimeo.com' in url:
        return url

    try:
        parsed   = urlparse(url)
        hostname = (parsed.hostname or '').lower()
        path     = parsed.path or ''

        # ── YouTube ──────────────────────────────────
        if 'youtube.com' in hostname or 'youtu.be' in hostname:

            video_id = None

            # youtu.be/VIDEO_ID
            if 'youtu.be' in hostname:
                video_id = path.lstrip('/')

            # youtube.com/watch?v=VIDEO_ID
            elif path == '/watch':
                params   = parse_qs(parsed.query)
                video_id = params.get('v', [''])[0]

            # youtube.com/shorts/VIDEO_ID
            elif path.startswith('/shorts/'):
                video_id = path.replace('/shorts/', '').split('/')[0]

            # youtube.com/v/VIDEO_ID
            elif path.startswith('/v/'):
                video_id = path.split('/')[2]

            if video_id:
                return f'https://www.youtube.com/embed/{video_id}'
            return None

        # ── Vimeo ──────────────────────────────────
        if 'vimeo.com' in hostname:
            video_id = path.lstrip('/').split('/')[0]
            if video_id.isdigit():
                return f'https://player.vimeo.com/video/{video_id}'
            return None

    except Exception:
        return None

    # Not a recognizable URL — return None
    return None


class LessonUploadForm(forms.ModelForm):
    class Meta:
        model   = Lesson
        fields  = ['title', 'video_file', 'video_url', 'pdf_file',
                   'notes', 'order', 'duration_mins']
        widgets = {
            'notes':     forms.Textarea(attrs={'rows': 4}),
            'video_url': forms.URLInput(attrs={
                'placeholder': 'https://www.youtube.com/watch?v=... or embed URL'
            }),
        }

    def clean(self):
        cleaned    = super().clean()
        video_file = cleaned.get('video_file')
        video_url  = cleaned.get('video_url', '').strip()

        if not video_file and not video_url:
            raise forms.ValidationError(
                "Please provide either a video file (MP4) or a video URL (YouTube/Vimeo)."
            )

        if video_url:
            normalized = normalize_video_url(video_url)
            if normalized is None:
                raise forms.ValidationError(
                    "Invalid video URL. Please use a YouTube or Vimeo link "
                    "(e.g. https://www.youtube.com/watch?v=XXXX or the embed URL)."
                )
            cleaned['video_url'] = normalized

        return cleaned


class ClassTimingForm(forms.ModelForm):
    class Meta:
        model   = ClassTiming
        fields  = ['date', 'day_of_week', 'start_time', 'end_time', 'meeting_link', 'notes']
        widgets = {
            'date':       forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time':   forms.TimeInput(attrs={'type': 'time'}),
        }


class CourseForm(forms.ModelForm):
    class Meta:
        model  = Course
        fields = ['title', 'description', 'category', 'price', 'thumbnail', 'badge']