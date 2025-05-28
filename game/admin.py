from django.contrib import admin
from .models import Word, Game, PlayerGame, Guess, UserProfile

admin.site.register(Word)
admin.site.register(Game)
admin.site.register(PlayerGame)
admin.site.register(Guess)
admin.site.register(UserProfile)