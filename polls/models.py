from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Poll(models.Model):
    question = models.CharField(max_length=300)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_polls'
    )
    pub_date = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this poll should close (optional)"
    )
    allow_multiple = models.BooleanField(
        default=False,
        help_text="Allow users to select multiple choices"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Manually deactivate a poll if needed"
    )

    class Meta:
        ordering = ['-pub_date']

    def __str__(self):
        return self.question

    @property
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    @property
    def total_votes(self):
        return sum(choice.votes for choice in self.choices.all())
    
    @property
    def days_remaining(self):
        if self.expires_at:
            delta = self.expires_at - timezone.now()
            return max(0, delta.days)
        return None


class Choice(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='choices')
    choice_text = models.CharField(max_length=300)
    votes = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['id']  # or you can add an order field later

    def __str__(self):
        return self.choice_text


class Vote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    # For multiple choice support - one Vote can have multiple choices
    choices = models.ManyToManyField(Choice, related_name='votes_received')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'poll')  # still one vote entry per user per poll
        indexes = [
            models.Index(fields=['poll', 'user']),
        ]

    def __str__(self):
        choices_str = ", ".join(c.choice_text for c in self.choices.all())
        return f"{self.user.username} voted {choices_str} in '{self.poll}'"

    def get_choice_list(self):
        return list(self.choices.all())