from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Course, Enrollment, Lesson
from .utils import education_unlocked


@login_required
def catalog(request):
    courses = Course.objects.filter(is_published=True)
    enrolled_ids = set(
        Enrollment.objects.filter(user=request.user).values_list('course_id', flat=True)
    )
    context = {
        'courses': courses,
        'unlocked': education_unlocked(request.user),
        'enrolled_ids': enrolled_ids,
    }
    return render(request, 'education/catalog.html', context)


@login_required
def course_detail(request, slug):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    unlocked = education_unlocked(request.user)
    enrollment = Enrollment.objects.filter(user=request.user, course=course).first()

    context = {
        'course': course,
        'modules': course.modules.prefetch_related('lessons').all(),
        'unlocked': unlocked,
        'enrollment': enrollment,
        'is_enrolled': enrollment is not None,
    }
    return render(request, 'education/course_detail.html', context)


@login_required
@require_POST
def enroll(request, slug):
    course = get_object_or_404(Course, slug=slug, is_published=True)

    if not education_unlocked(request.user):
        messages.warning(request, 'Make a deposit to unlock the academy.')
        return redirect('dashboard:deposits')

    enrollment, created = Enrollment.objects.get_or_create(user=request.user, course=course)
    if created:
        messages.success(request, f'You are now enrolled in "{course.title}".')
    else:
        messages.info(request, f'You are already enrolled in "{course.title}".')
    return redirect('education:course_detail', slug=course.slug)


@login_required
def lesson_player(request, slug, lesson_id):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    lesson = get_object_or_404(Lesson, pk=lesson_id, module__course=course)

    enrollment = Enrollment.objects.filter(user=request.user, course=course).first()

    # Access: enrolled, or this lesson is a free preview.
    if enrollment is None and not lesson.is_preview:
        if not education_unlocked(request.user):
            messages.warning(request, 'Make a deposit to unlock the academy.')
            return redirect('dashboard:deposits')
        messages.info(request, 'Enroll to access this lesson.')
        return redirect('education:course_detail', slug=course.slug)

    # "Mark complete" bumps progress across the course's lessons.
    if request.method == 'POST' and enrollment is not None:
        total = course.lesson_count or 1
        step = max(1, round(100 / total))
        enrollment.progress = min(100, enrollment.progress + step)
        enrollment.save(update_fields=['progress'])
        messages.success(request, 'Lesson marked complete.')
        return redirect('education:lesson', slug=course.slug, lesson_id=lesson.id)

    modules = course.modules.prefetch_related('lessons').all()
    context = {
        'course': course,
        'lesson': lesson,
        'modules': modules,
        'enrollment': enrollment,
        'is_enrolled': enrollment is not None,
    }
    return render(request, 'education/lesson_player.html', context)
