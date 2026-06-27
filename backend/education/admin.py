from django.contrib import admin

from .models import Course, Enrollment, Lesson, Module


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 1


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'level', 'instructor', 'duration_label', 'order', 'is_published')
    list_editable = ('order', 'is_published')
    list_filter = ('level', 'is_published')
    search_fields = ('title', 'description', 'instructor')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ModuleInline]


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_editable = ('order',)
    list_filter = ('course',)
    search_fields = ('title',)
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'duration_label', 'order', 'is_preview')
    list_editable = ('order', 'is_preview')
    list_filter = ('module__course', 'is_preview')
    search_fields = ('title', 'content')


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'progress', 'enrolled_at')
    list_filter = ('course',)
    search_fields = ('user__username', 'user__email', 'course__title')
    readonly_fields = ('user', 'course', 'enrolled_at')

    def has_add_permission(self, request):
        return False
