from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Poll(models.Model):
    question = models.CharField(max_length=500)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='polls', null=True, blank=True)
    created_by_organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, related_name='polls', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Poll expiration
    expires_at = models.DateTimeField(null=True, blank=True)
    is_closed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.question

    def total_votes(self):
        return Vote.objects.filter(poll=self).count()
    
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    def get_creator(self):
        """Returns the creator (User or Organization)"""
        return self.created_by_organization or self.created_by

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
    """
    Vote model with privacy-first design.
    Votes are stored securely - poll creators cannot identify individual voters.
    Only aggregate statistics are exposed.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='votes')
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='votes')
    option = models.ForeignKey(PollOption, on_delete=models.CASCADE, related_name='votes')
    voted_at = models.DateTimeField(auto_now=True)
    
    # Anonymity tracking
    is_anonymous = models.BooleanField(default=True)  # Vote is anonymous to poll creator by default

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'poll'], name='unique_user_poll_vote')
        ]
        indexes = [
            models.Index(fields=['user', '-voted_at']),
            models.Index(fields=['poll', '-voted_at']),
        ]

    def __str__(self):
        return f"Vote on {self.poll.question} (Anonymous)"
    
    def clean(self):
        """Validate that user is not voting on their own poll"""
        from django.core.exceptions import ValidationError
        poll_creator = self.poll.created_by or self.poll.created_by_organization
        if isinstance(poll_creator, User) and self.poll.created_by == self.user:
            raise ValidationError("You cannot vote on your own poll.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def get_voter_info(self, requesting_user):
        """
        Returns voter info based on privacy settings.
        Only the voter themselves can see their own vote in their history.
        Poll creators only see aggregate statistics.
        Other users never see individual votes.
        """
        if requesting_user == self.user:
            # User can see their own vote
            return {
                'option': self.option.option_text,
                'voted_at': self.voted_at,
                'is_own_vote': True
            }
        # All other users cannot see individual votes
        return None
