from django.db import models


class Pattern(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=110, unique=True)
    description = models.TextField(blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name


class Question(models.Model):
    class Difficulty(models.TextChoices):
        EASY = "easy", "Easy"
        MEDIUM = "medium", "Medium"
        HARD = "hard", "Hard"

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    leetcode_url = models.URLField(max_length=500)
    difficulty = models.CharField(max_length=10, choices=Difficulty.choices)
    estimated_minutes = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    catalog_validated_at = models.DateTimeField(null=True, blank=True)
    patterns = models.ManyToManyField(Pattern, through="QuestionPattern", related_name="questions")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["difficulty", "title"]

    def __str__(self):
        return self.title


class QuestionPattern(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    pattern = models.ForeignKey(Pattern, on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["question", "pattern"], name="unique_question_pattern"),
        ]

    def __str__(self):
        return f"{self.question} / {self.pattern}"
