from django.db import models
from django.contrib.auth.models import User


class Poll(models.Model):
    question = models.CharField(max_length=500)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='polls')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.question

    def total_votes(self):
        return Vote.objects.filter(poll=self).count()

    def get_results(self):
        total = self.total_votes()
        results = []
        for option in self.options.all():
            votes = Vote.objects.filter(option=option).count()
            percentage = round((votes / total * 100), 1) if total > 0 else 0
            results.append({
                'id': option.id,
                'text': option.option_text,
                'votes': votes,
                'percentage': percentage,
            })
        return results, total


class PollOption(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='options')
    option_text = models.CharField(max_length=300)

    def __str__(self):
        return self.option_text

    def vote_count(self):
        return Vote.objects.filter(option=self).count()


class Vote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='votes')
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='votes')
    option = models.ForeignKey(PollOption, on_delete=models.CASCADE, related_name='votes')
    voted_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'poll'], name='unique_user_poll_vote')
        ]

    def __str__(self):
        return f"{self.user.username} voted on {self.poll.question}"
