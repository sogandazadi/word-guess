from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Game, PlayerGame, Guess, Word
from .models import UserProfile
from django.conf import settings

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class WordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Word
        fields = ['word', 'description' , 'hint'] 

class GameSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    winner = UserSerializer(read_only=True)

    class Meta:
        model = Game
        fields = ['id', 'created_by', 'difficulty', 'word', 'status', 'winner', 'created_at', 'time_limit_minutes']

class PlayerGameSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = PlayerGame
        fields = ['id', 'game', 'user', 'score', 'joined_at', 'is_turn' , 'hints_used' , 'hint_used']

class GuessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guess
        fields = ['id', 'player_game', 'letter', 'is_correct', 'guessed_at']

class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    rank = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ['username', 'score', 'rank', 'avatar_url']

    def get_rank(self, obj):
        return obj.get_rank()

    def get_avatar_url(self, obj):
        request = self.context.get('request')
        if obj.avatar and hasattr(obj.avatar, 'url'):
            url = obj.avatar.url
        else:
            url = settings.MEDIA_URL + 'avatars/default_avatar.png' 

        if request is not None:
            return request.build_absolute_uri(url)
        return url