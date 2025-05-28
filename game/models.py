from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Word(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    word = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True) 
    hint = models.TextField(blank=True)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)

    def __str__(self):
        return self.word




class Game(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    STATUS_CHOICES = [
        ('waiting', 'Waiting for second player'),
        ('active', 'Active'),
        ('paused', 'Paused'),  
        ('finished', 'Finished'),
    ]

    MODE_CHOICES = [
        ('single', 'Single Player'),   
        ('multi', 'Multiplayer'),     
    ]

    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_games')
    paused_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='paused_games')
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    word = models.ForeignKey(Word, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='waiting')
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='multi')  

    winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='won_games')
    created_at = models.DateTimeField(auto_now_add=True)
    time_limit_minutes = models.IntegerField(default=10)
    current_turn = models.ForeignKey(
        'PlayerGame',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='games_as_current_turn'
    )
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True) 
    paused_at = models.DateTimeField(null=True, blank=True)   
    player_1 = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='player_1_games')
    player_2 = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='player_2_games')
    

    def __str__(self):
        return f"Game #{self.id} ({self.difficulty}, {self.mode})"



class PlayerGame(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='players')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    joined_at = models.DateTimeField(auto_now_add=True)
    is_turn = models.BooleanField(default=False) 

    hints_used = models.IntegerField(default=0)
    hint_used = models.BooleanField(default=False) 
    letter_hint_used = models.BooleanField(default=False) 

    def __str__(self):
        return f"{self.user.username} in Game #{self.game.id}"

class Guess(models.Model):
    player_game = models.ForeignKey(PlayerGame, on_delete=models.CASCADE, related_name='guesses')
    letter = models.CharField(max_length=1)
    position = models.IntegerField(default=0)
    is_correct = models.BooleanField()
    guessed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.letter} (pos {self.position}) - {'✔' if self.is_correct else '❌'}"



class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)  

    def get_rank(self):
        if self.score < 20:
            return "تازه‌کار"
        elif self.score < 45:
            return "مبتدی"
        elif self.score < 70:
            return "نیمه‌ماهر"
        elif self.score < 100:
            return "ماهر"
        elif self.score < 130:
            return "حرفه‌ای"
        elif self.score < 160:
            return "استاد"
        elif self.score < 200:
            return "برتر"
        else:
            return "افسانه‌ای"


    def __str__(self):
        return f"{self.user.username} - {self.get_rank()} ({self.score} pts)"
    