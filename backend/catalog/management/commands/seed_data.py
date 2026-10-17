from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Pattern, Question, QuestionPattern
from progress.models import Achievement


PATTERNS = [
    ("Arrays and Strings", "arrays-strings", "Core traversal, indexing, and string manipulation."),
    ("Hashing", "hashing", "Use maps and sets to find relationships efficiently."),
    ("Two Pointers", "two-pointers", "Move coordinated pointers through ordered or paired data."),
    ("Sliding Window", "sliding-window", "Maintain a moving range while tracking a condition."),
    ("Sorting", "sorting", "Use ordering to simplify comparisons and greedy decisions."),
    ("Binary Search", "binary-search", "Narrow a sorted search space with logarithmic decisions."),
    ("Linked Lists", "linked-lists", "Manipulate node references and linked structures."),
    ("Stacks and Queues", "stacks-queues", "Use order-preserving containers for traversal and parsing."),
    ("Trees and Binary Search Trees", "trees-bst", "Traverse hierarchical data and exploit tree ordering."),
    ("Dynamic Programming", "dynamic-programming", "Build solutions from overlapping subproblems."),
]

QUESTIONS = [
    ("Two Sum", "two-sum", "1", "easy", 20, ["arrays-strings", "hashing"]),
    ("Valid Anagram", "valid-anagram", "242", "easy", 15, ["arrays-strings", "hashing"]),
    ("Best Time to Buy and Sell Stock", "best-time-to-buy-and-sell-stock", "121", "easy", 20, ["arrays-strings"]),
    ("Valid Parentheses", "valid-parentheses", "20", "easy", 20, ["stacks-queues"]),
    ("Binary Search", "binary-search", "704", "easy", 20, ["binary-search"]),
    ("Longest Substring Without Repeating Characters", "longest-substring-without-repeating-characters", "3", "medium", 30, ["sliding-window", "hashing"]),
    ("3Sum", "3sum", "15", "medium", 40, ["two-pointers", "sorting"]),
    ("Group Anagrams", "group-anagrams", "49", "medium", 30, ["arrays-strings", "hashing"]),
    ("Reverse Linked List", "reverse-linked-list", "206", "easy", 25, ["linked-lists"]),
    ("House Robber", "house-robber", "198", "medium", 35, ["dynamic-programming"]),
]

ACHIEVEMENTS = [
    ("First Blood", "first-blood", "Complete your first question.", "questions", 1, ""),
    ("Getting Started", "getting-started", "Complete 10 questions.", "questions", 10, ""),
    ("Week Warrior", "week-warrior", "Meet the daily goal for 7 consecutive days.", "streak", 7, ""),
    ("Pattern Hunter", "pattern-hunter", "Practice 5 distinct patterns.", "patterns", 5, ""),
    ("Easy Explorer", "easy-explorer", "Complete 25 Easy questions.", "difficulty", 25, "easy"),
    ("Medium Crusher", "medium-crusher", "Complete 25 Medium questions.", "difficulty", 25, "medium"),
    ("Hard Challenger", "hard-challenger", "Complete 10 Hard questions.", "difficulty", 10, "hard"),
    ("Consistency King", "consistency-king", "Reach a 30-day qualifying streak.", "streak", 30, ""),
    ("Revision Master", "revision-master", "Complete 20 revision tasks.", "revisions", 20, ""),
    ("Century Club", "century-club", "Complete 100 questions.", "questions", 100, ""),
]


class Command(BaseCommand):
    help = "Seed the small, safe DSA Quest catalog and achievement definitions."

    @transaction.atomic
    def handle(self, *args, **options):
        patterns = {}
        for order, (name, slug, description) in enumerate(PATTERNS, start=1):
            pattern, _ = Pattern.objects.update_or_create(
                slug=slug,
                defaults={"name": name, "description": description, "display_order": order, "is_active": True},
            )
            patterns[slug] = pattern

        for title, slug, number, difficulty, minutes, pattern_slugs in QUESTIONS:
            question, _ = Question.objects.update_or_create(
                slug=slug,
                defaults={
                    "title": title,
                    "leetcode_url": f"https://leetcode.com/problems/{slug}/",
                    "difficulty": difficulty,
                    "estimated_minutes": minutes,
                    "is_active": True,
                },
            )
            for position, pattern_slug in enumerate(pattern_slugs):
                QuestionPattern.objects.update_or_create(
                    question=question,
                    pattern=patterns[pattern_slug],
                    defaults={"is_primary": position == 0},
                )

        for name, slug, description, criteria_type, criteria_value, difficulty in ACHIEVEMENTS:
            Achievement.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "description": description,
                    "criteria_type": criteria_type,
                    "criteria_value": criteria_value,
                    "difficulty": difficulty,
                    "is_active": True,
                },
            )
        self.stdout.write(self.style.SUCCESS("Seeded DSA Quest catalog and achievements."))
