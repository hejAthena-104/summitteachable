from django.conf import settings
from django.db import models
from django.urls import reverse


class Course(models.Model):
    """An academy course."""

    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField(blank=True)
    short_description = models.CharField(max_length=300, blank=True)
    instructor = models.CharField(max_length=120, default='Summit Teachable')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    duration_label = models.CharField(max_length=40, blank=True, help_text='e.g. "6h 30m"')
    # Thumbnails live at static/images/courses/<thumbnail_slug>.png
    thumbnail_slug = models.CharField(max_length=120, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'title']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('education:course_detail', kwargs={'slug': self.slug})

    @property
    def lesson_count(self):
        return Lesson.objects.filter(module__course=self).count()

    @property
    def module_count(self):
        return self.modules.count()


class Module(models.Model):
    course = models.ForeignKey(Course, related_name='modules', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.course.title} — {self.title}'


class Lesson(models.Model):
    module = models.ForeignKey(Module, related_name='lessons', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    video_url = models.URLField(blank=True, help_text='YouTube/Vimeo embed URL')
    content = models.TextField(blank=True)
    duration_label = models.CharField(max_length=40, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_preview = models.BooleanField(
        default=False,
        help_text='Previewable without enrolling.',
    )

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.module.title} — {self.title}'

    @property
    def course(self):
        return self.module.course


class Enrollment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='enrollments', on_delete=models.CASCADE)
    course = models.ForeignKey(Course, related_name='enrollments', on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    progress = models.PositiveIntegerField(default=0, help_text='Percent complete (0-100).')

    class Meta:
        unique_together = ('user', 'course')
        ordering = ['-enrolled_at']

    def __str__(self):
        return f'{self.user} → {self.course}'
