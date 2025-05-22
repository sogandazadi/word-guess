from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework.exceptions import ValidationError
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Game, PlayerGame, UserProfile, Word
from .serializers import GameSerializer, UserProfileSerializer
import random
from rest_framework.permissions import IsAuthenticated
from .models import Game, PlayerGame, Guess
from django.utils import timezone
import random
from django.utils.timezone import now
from django.db import models
from .models import Game, PlayerGame, Guess, UserProfile





from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()  # اضافه کردن توکن به بلک‌لیست
            return Response({"message": "Logged out successfully."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": "Invalid or missing refresh token."}, status=status.HTTP_400_BAD_REQUEST)


class MyProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile, context={'request': request})
        return Response(serializer.data)
    


class RegisterView(APIView):
    def post(self, request):
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")

        if not username or not email or not password:
            raise ValidationError("همه فیلدها الزامی هستند.")

        if User.objects.filter(username=username).exists():
            raise ValidationError("این نام کاربری قبلاً استفاده شده است.")

        user = User.objects.create_user(username=username, email=email, password=password)
        return Response({"message": "ثبت‌نام با موفقیت انجام شد!"}, status=status.HTTP_201_CREATED)

# # تابع کمکی برای گرفتن کلمه تصادفی بر اساس سطح دشواری
# def get_random_word(difficulty):
#     easy_words = ['apple']
#     # , 'bread', 'chair', 'dream', 'eagle'
#     medium_words = ['python']
#     # , 'jungle', 'market', 'garden', 'castle'
#     hard_words = ['computer']
#     # , 'elephant', 'structure', 'mountain', 'building'

#     if difficulty == 'easy':
#         return random.choice(easy_words)
#     elif difficulty == 'medium':
#         return random.choice(medium_words)
#     else:
#         return random.choice(hard_words)
    


import random

def get_random_word(difficulty):
    words = list(Word.objects.filter(difficulty=difficulty))
    if not words:
        return None
    return random.choice(words)



class CreateMultiPlayerGameView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        difficulty = request.data.get('difficulty')
        if difficulty not in ['easy', 'medium', 'hard']:
            return Response({'error': 'Invalid difficulty'}, status=status.HTTP_400_BAD_REQUEST)

        word = get_random_word(difficulty)

        time_limits = {'easy': 3, 'medium': 2, 'hard': 5}
        time_limit = time_limits[difficulty]

        game = Game.objects.create(
            created_by=request.user,
            difficulty=difficulty,
            word=word,
            time_limit_minutes=time_limit,
            status='waiting',
            mode='multi'
        )

        # 🔹 بازیکن اول رو می‌سازیم و در متغیر نگه می‌داریم
        pg = PlayerGame.objects.create(game=game, user=request.user, is_turn=True)

        # 🔹 مقداردهی به current_turn
        game.current_turn = pg
        game.save()

        serializer = GameSerializer(game)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    


class CreateSinglePlayerGameView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        difficulty = request.data.get('difficulty')
        if difficulty not in ['easy', 'medium', 'hard']:
            return Response({'error': 'Invalid difficulty'}, status=status.HTTP_400_BAD_REQUEST)

        word = get_random_word(difficulty)
        time_limits = {'easy': 3, 'medium': 2, 'hard': 5}
        time_limit = time_limits[difficulty]

        game = Game.objects.create(
            created_by=request.user,
            difficulty=difficulty,
            word=word,
            time_limit_minutes=time_limit,
            status='active',  # بازی بلافاصله فعال می‌شود
            mode='single',
            started_at=timezone.now()
        )

        # ساخت بازیکن واقعی
        player_real = PlayerGame.objects.create(game=game, user=request.user, is_turn=True)

        # ساخت بازیکن ربات (فرض کن username='bot' از قبل وجود دارد)
        try:
            bot_user = User.objects.get(username='bot')
        except User.DoesNotExist:
            return Response({'error': 'Bot user not found'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        PlayerGame.objects.create(game=game, user=bot_user, is_turn=False)

        game.current_turn = player_real
        game.save()

        serializer = GameSerializer(game)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    
class LeaderboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        top_users = UserProfile.objects.order_by('-score')[:10]
        data = [
            {
                'username': profile.user.username,
                'score': profile.score,
                'rank': profile.get_rank(),
            }
            for profile in top_users
        ]
        return Response(data)

# class JoinGameView(APIView):
#     permission_classes = [permissions.IsAuthenticated]

#     def post(self, request, game_id):
#         try:
#             game = Game.objects.get(id=game_id)
#         except Game.DoesNotExist:
#             return Response({'error': 'Game not found'}, status=status.HTTP_404_NOT_FOUND)

#         if game.status != 'waiting':
#             return Response({'error': 'Cannot join this game'}, status=status.HTTP_400_BAD_REQUEST)

#         if game.players.filter(user=request.user).exists():
#             return Response({'error': 'You already joined this game'}, status=status.HTTP_400_BAD_REQUEST)

#         PlayerGame.objects.create(game=game, user=request.user, is_turn=False)

#         # وقتی بازیکن دوم اضافه شد، نوبت رو رندوم انتخاب کن
#         players = list(game.players.all())
#         random_player = random.choice(players)
#         for player in players:
#             player.is_turn = (player == random_player)
#             player.save()

#         game.status = 'active'
#         game.started_at = timezone.now() 
#         game.save()

#         return Response({'message': 'Joined the game successfully'}, status=status.HTTP_200_OK)


class JoinGameView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, game_id):
        try:
            game = Game.objects.get(id=game_id)
        except Game.DoesNotExist:
            return Response({'error': 'Game not found'}, status=status.HTTP_404_NOT_FOUND)

        # اضافه کردن شرط برای اجازه join فقط در حالت multi
        if game.mode != 'multi':
            return Response({'error': 'Cannot join a single-player game.'}, status=status.HTTP_400_BAD_REQUEST)

        if game.status != 'waiting':
            return Response({'error': 'Cannot join this game'}, status=status.HTTP_400_BAD_REQUEST)

        if game.players.filter(user=request.user).exists():
            return Response({'error': 'You already joined this game'}, status=status.HTTP_400_BAD_REQUEST)

        PlayerGame.objects.create(game=game, user=request.user, is_turn=False)

        # وقتی بازیکن دوم اضافه شد، نوبت رو رندوم انتخاب کن
        players = list(game.players.all())
        random_player = random.choice(players)
        for player in players:
            player.is_turn = (player == random_player)
            player.save()

        game.status = 'active'
        game.started_at = timezone.now() 
        game.save()

        return Response({'message': 'Joined the game successfully'}, status=status.HTTP_200_OK)


# class GuessLetterView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request, game_id):
#         letter = request.data.get('letter', '').lower()
#         position = request.data.get('position')

#         # اعتبارسنجی ورودی‌ها
#         if not letter or len(letter) != 1 or not letter.isalpha():
#             return Response({'error': 'You must guess a single letter.'}, status=400)

#         try:
#             position = int(position)
#         except (TypeError, ValueError):
#             return Response({'error': 'Position must be provided as an integer.'}, status=400)

#         try:
#             game = Game.objects.get(id=game_id)
#         except Game.DoesNotExist:
#             return Response({'error': 'Game not found.'}, status=404)

#         if game.status != 'active':
#             return Response({'error': 'Game is not active.'}, status=400)

#         if not game.started_at:
#             return Response({'error': 'Game has not started yet.'}, status=400)

#         elapsed_minutes = (now() - game.started_at).total_seconds() / 60
#         if elapsed_minutes > game.time_limit_minutes:
#             game.status = 'finished'

#             players = list(game.players.all())
#             if len(players) == 2:
#                 p1, p2 = players[0], players[1]
#                 profile1, _ = UserProfile.objects.get_or_create(user=p1.user)
#                 profile2, _ = UserProfile.objects.get_or_create(user=p2.user)

#                 if p1.score > p2.score:
#                     winner = p1
#                     game.winner = winner.user
#                     profile1.score += 5
#                     profile1.save()
#                     message = f"Time is up! Game finished. Winner is {winner.user.username}."
#                 elif p1.score < p2.score:
#                     winner = p2
#                     game.winner = winner.user
#                     profile2.score += 5
#                     profile2.save()
#                     message = f"Time is up! Game finished. Winner is {winner.user.username}."
#                 else:
#                     game.winner = None
#                     profile1.score += 1
#                     profile2.score += 1
#                     profile1.save()
#                     profile2.save()
#                     message = "Time is up! Game finished. It's a tie!"
#             else:
#                 message = "Time is up! Game finished."

#             game.save()
#             return Response({'error': message, 'winner': game.winner.username if game.winner else 'tie'}, status=403)

#         try:
#             player_game = PlayerGame.objects.get(game=game, user=request.user)
#         except PlayerGame.DoesNotExist:
#             return Response({'error': 'You are not part of this game.'}, status=403)

#         if not player_game.is_turn:
#             return Response({'error': 'Not your turn.'}, status=403)

#         if position < 0 or position >= len(game.word):
#             return Response({'error': 'Position is out of range.'}, status=400)

#         if Guess.objects.filter(player_game=player_game, position=position, is_correct=True).exists():
#             return Response({'error': 'You already guessed the correct letter for this position.'}, status=400)

#         is_correct = (letter == game.word[position].lower())

#         Guess.objects.create(player_game=player_game, letter=letter, position=position, is_correct=is_correct)

#         if is_correct:
#             player_game.score += 20
#         else:
#             player_game.score -= 20
#         player_game.save()

#         guessed_positions = Guess.objects.filter(player_game=player_game, is_correct=True).values_list('position', flat=True)
#         if set(range(len(game.word))) <= set(guessed_positions):
#             game.status = 'finished'

#             players = list(game.players.all())
#             if len(players) == 2:
#                 p1, p2 = players[0], players[1]
#                 profile1, _ = UserProfile.objects.get_or_create(user=p1.user)
#                 profile2, _ = UserProfile.objects.get_or_create(user=p2.user)

#                 if p1.score > p2.score:
#                     winner = p1
#                     game.winner = winner.user
#                     profile1.score += 5
#                     profile1.save()
#                     message = f"Correct guess! Game finished. Winner is {winner.user.username}."
#                 elif p1.score < p2.score:
#                     winner = p2
#                     game.winner = winner.user
#                     profile2.score += 5
#                     profile2.save()
#                     message = f"Correct guess! Game finished. Winner is {winner.user.username}."
#                 else:
#                     game.winner = None
#                     profile1.score += 1
#                     profile2.score += 1
#                     profile1.save()
#                     profile2.save()
#                     message = "Correct guess! Game finished. It's a tie!"
#             else:
#                 message = "Correct guess! Game finished."

#             game.save()
#             return Response({'message': message, 'winner': game.winner.username if game.winner else None})

#         players = list(game.players.all())
#         for pg in players:
#             pg.is_turn = (pg != player_game)
#             pg.save()

#         return Response({'message': 'Correct!' if is_correct else 'Wrong!', 'score': player_game.score})


# class GuessLetterView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request, game_id):
#         letter = request.data.get('letter', '').lower()
#         position = request.data.get('position')

#         # اعتبارسنجی ورودی‌ها
#         if not letter or len(letter) != 1 or not letter.isalpha():
#             return Response({'error': 'You must guess a single letter.'}, status=400)

#         try:
#             position = int(position)
#         except (TypeError, ValueError):
#             return Response({'error': 'Position must be provided as an integer.'}, status=400)

#         try:
#             game = Game.objects.get(id=game_id)
#         except Game.DoesNotExist:
#             return Response({'error': 'Game not found.'}, status=404)

#         if game.status != 'active':
#             return Response({'error': 'Game is not active.'}, status=400)

#         if not game.started_at:
#             return Response({'error': 'Game has not started yet.'}, status=400)

#         elapsed_minutes = (now() - game.started_at).total_seconds() / 60
#         if elapsed_minutes > game.time_limit_minutes:
#             game.status = 'finished'
#             self._handle_game_finish(game)
#             return Response({'error': 'Time is up! Game finished.', 'winner': game.winner.username if game.winner else 'tie'}, status=403)

#         try:
#             player_game = PlayerGame.objects.get(game=game, user=request.user)
#         except PlayerGame.DoesNotExist:
#             return Response({'error': 'You are not part of this game.'}, status=403)

#         if not player_game.is_turn:
#             return Response({'error': 'Not your turn.'}, status=403)

#         if position < 0 or position >= len(game.word):
#             return Response({'error': 'Position is out of range.'}, status=400)

#         if Guess.objects.filter(player_game=player_game, position=position, is_correct=True).exists():
#             return Response({'error': 'You already guessed the correct letter for this position.'}, status=400)

#         is_correct = (letter == game.word[position].lower())

#         Guess.objects.create(player_game=player_game, letter=letter, position=position, is_correct=is_correct)

#         if is_correct:
#             player_game.score += 20
#         else:
#             player_game.score -= 20
#         player_game.save()

#         guessed_positions = Guess.objects.filter(player_game=player_game, is_correct=True).values_list('position', flat=True)
#         all_positions = set(range(len(game.word)))

#         if set(guessed_positions) == all_positions:
#             game.status = 'finished'
#             self._handle_game_finish(game)
#             return Response({'message': 'Correct guess! Game finished.', 'winner': game.winner.username if game.winner else None})

#         # مدیریت نوبت و حدس ربات در بازی تک نفره
#         if game.mode == 'multi':
#             # تغییر نوبت بازیکنان چند نفره
#             players = list(game.players.all())
#             for pg in players:
#                 pg.is_turn = (pg != player_game)
#                 pg.save()
#         else:
#             # بازی تک نفره: بعد از بازیکن، نوبت ربات
#             player_game.is_turn = False
#             player_game.save()

#             # حدس ربات (یک تابع ساده بنویس)
#             bot_pg = PlayerGame.objects.filter(game=game, user__username='bot').first()
#             if bot_pg and bot_pg.user.username == 'bot':
#                 self._bot_guess(game, bot_pg)

#             # نوبت بازیکن می‌شود
#             player_game.is_turn = True
#             player_game.save()

#         return Response({'message': 'Correct!' if is_correct else 'Wrong!', 'score': player_game.score})

#     def _handle_game_finish(self, game):
#         players = list(game.players.all())
#         if len(players) == 2:
#             p1, p2 = players[0], players[1]
#             profile1, _ = UserProfile.objects.get_or_create(user=p1.user)
#             profile2, _ = UserProfile.objects.get_or_create(user=p2.user)

#             if p1.score > p2.score:
#                 winner = p1
#                 game.winner = winner.user
#                 profile1.score += 5
#                 profile1.save()
#             elif p1.score < p2.score:
#                 winner = p2
#                 game.winner = winner.user
#                 profile2.score += 5
#                 profile2.save()
#             else:
#                 game.winner = None
#                 profile1.score += 1
#                 profile2.score += 1
#                 profile1.save()
#                 profile2.save()
#         else:
#             game.winner = None

#         game.save()

#     def _bot_guess(self, game, bot_pg):
#         # اینجا یه حدس ساده ربات رو بزار (مثلاً حدس حروف تصادفی که حدس زده نشده)
#         guessed_letters = Guess.objects.filter(player_game__game=game).values_list('letter', flat=True)
#         alphabet = set('abcdefghijklmnopqrstuvwxyz')
#         remaining_letters = list(alphabet - set(guessed_letters))

#         if not remaining_letters:
#             return

#         import random
#         letter = random.choice(remaining_letters)

#         # حدس ربات روی اولین موقعیت درست یا اولین موقعیت خالی
#         word = game.word.lower()
#         for pos, ch in enumerate(word):
#             if ch == letter:
#                 is_correct = True
#                 break
#         else:
#             pos = 0
#             is_correct = False

#         Guess.objects.create(player_game=bot_pg, letter=letter, position=pos, is_correct=is_correct)
#         if is_correct:
#             bot_pg.score += 20
#         else:
#             bot_pg.score -= 20
#         bot_pg.save()





from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils.timezone import now
from django.db import transaction
import random

# class GuessLetterView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request, game_id):
#         letter = request.data.get('letter', '').lower()
#         position = request.data.get('position')

#         # اعتبارسنجی ورودی‌ها
#         validation = self._validate_input(letter, position)
#         if 'error' in validation:
#             return Response({'error': validation['error']}, status=validation['status'])

#         letter = validation['letter']
#         position = validation['position']

#         # گرفتن بازی
#         try:
#             game = Game.objects.get(id=game_id)
#         except Game.DoesNotExist:
#             return Response({'error': 'Game not found.'}, status=404)

#         # بررسی وضعیت بازی
#         if game.status != 'active':
#             return Response({'error': 'Game is not active.'}, status=400)

#         if not game.started_at:
#             return Response({'error': 'Game has not started yet.'}, status=400)

#         elapsed_minutes = (now() - game.started_at).total_seconds() / 60
#         if elapsed_minutes > game.time_limit_minutes:
#             game.status = 'finished'
#             self._handle_game_finish(game)
#             return Response({'error': 'Time is up! Game finished.', 'winner': game.winner.username if game.winner else 'tie'}, status=403)

#         # گرفتن بازیکن فعلی
#         try:
#             player_game = PlayerGame.objects.get(game=game, user=request.user)
#         except PlayerGame.DoesNotExist:
#             return Response({'error': 'You are not part of this game.'}, status=403)

#         if not player_game.is_turn:
#             return Response({'error': 'Not your turn.'}, status=403)

#         if position < 0 or position >= len(game.word):
#             return Response({'error': 'Position is out of range.'}, status=400)

#         if Guess.objects.filter(player_game=player_game, position=position, is_correct=True).exists():
#             return Response({'error': 'You already guessed the correct letter for this position.'}, status=400)

#         # ثبت حدس
#         is_correct = (letter == game.word[position].lower())
#         with transaction.atomic():
#             Guess.objects.create(player_game=player_game, letter=letter, position=position, is_correct=is_correct)

#             if is_correct:
#                 player_game.score += 20
#             else:
#                 player_game.score -= 20
#             player_game.save()

#         # بررسی تکمیل کلمه
#         guessed_positions = Guess.objects.filter(player_game=player_game, is_correct=True).values_list('position', flat=True)
#         all_positions = set(range(len(game.word)))

#         if set(guessed_positions) == all_positions:
#             game.status = 'finished'
#             self._handle_game_finish(game)
#             return Response({'message': 'Correct guess! Game finished.', 'winner': game.winner.username if game.winner else None})

#         # تغییر نوبت و حدس ربات
#         self._update_turn(game, player_game)

#         return Response({'message': 'Correct!' if is_correct else 'Wrong!', 'score': player_game.score})


#     def _validate_input(self, letter, position):
#         if not letter or len(letter) != 1 or not letter.isalpha():
#             return {'error': 'You must guess a single letter.', 'status': 400}
#         try:
#             position = int(position)
#         except (TypeError, ValueError):
#             return {'error': 'Position must be provided as an integer.', 'status': 400}
#         return {'letter': letter.lower(), 'position': position}

#     def _handle_game_finish(self, game):
#         players = list(game.players.all())
#         if len(players) == 2:
#             p1, p2 = players[0], players[1]
#             profile1, _ = UserProfile.objects.get_or_create(user=p1.user)
#             profile2, _ = UserProfile.objects.get_or_create(user=p2.user)

#             if p1.score > p2.score:
#                 winner = p1
#                 game.winner = winner.user
#                 profile1.score += 5
#                 profile1.save()
#             elif p1.score < p2.score:
#                 winner = p2
#                 game.winner = winner.user
#                 profile2.score += 5
#                 profile2.save()
#             else:
#                 game.winner = None
#                 profile1.score += 1
#                 profile2.score += 1
#                 profile1.save()
#                 profile2.save()
#         else:
#             game.winner = None

#         game.save()

#     def _update_turn(self, game, current_player_game):
#         if game.mode == 'multi':
#             players = list(game.players.all())
#             for pg in players:
#                 pg.is_turn = (pg != current_player_game)
#                 pg.save()
#         else:
#             # بازی تک نفره: نوبت بازیکن فعلی False می‌شود
#             current_player_game.is_turn = False
#             current_player_game.save()

#             # حدس ربات
#             bot_pg = PlayerGame.objects.filter(game=game, user__username='bot').first()
#             if bot_pg:
#                 self._bot_guess(game, bot_pg)

#             # نوبت بازیکن می‌شود
#             current_player_game.is_turn = True
#             current_player_game.save()

#     def _bot_guess(self, game, bot_pg):
#         guessed_positions = Guess.objects.filter(player_game__game=game, is_correct=True).values_list('position', flat=True)
#         word = game.word.lower()

#         empty_positions = [i for i in range(len(word)) if i not in guessed_positions]

#         if empty_positions:
#             pos = random.choice(empty_positions)
#             letter = word[pos]
#             is_correct = True
#         else:
#             guessed_letters = Guess.objects.filter(player_game__game=game).values_list('letter', flat=True)
#             alphabet = set('abcdefghijklmnopqrstuvwxyz')
#             remaining_letters = list(alphabet - set(guessed_letters))

#             if not remaining_letters:
#                 return

#             letter = random.choice(remaining_letters)
#             pos = 0
#             is_correct = (letter == word[pos])

#         Guess.objects.create(player_game=bot_pg, letter=letter, position=pos, is_correct=is_correct)
#         bot_pg.score += 20 if is_correct else -20
#         bot_pg.save()




class GuessLetterView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, game_id):
        letter = request.data.get('letter', '').lower()
        position = request.data.get('position')

        # اعتبارسنجی ورودی‌ها
        validation = self._validate_input(letter, position)
        if 'error' in validation:
            return Response({'error': validation['error']}, status=validation['status'])

        letter = validation['letter']
        position = validation['position']

        # گرفتن بازی
        try:
            game = Game.objects.get(id=game_id)
        except Game.DoesNotExist:
            return Response({'error': 'Game not found.'}, status=404)

        # بررسی وضعیت بازی
        if game.status != 'active':
            return Response({'error': 'Game is not active.'}, status=400)

        if not game.started_at:
            return Response({'error': 'Game has not started yet.'}, status=400)

        elapsed_minutes = (now() - game.started_at).total_seconds() / 60
        if elapsed_minutes > game.time_limit_minutes:
            game.status = 'finished'
            self._handle_game_finish(game)
            return Response({'error': 'Time is up! Game finished.', 'winner': game.winner.username if game.winner else 'tie'}, status=403)

        # گرفتن بازیکن فعلی
        try:
            player_game = PlayerGame.objects.get(game=game, user=request.user)
        except PlayerGame.DoesNotExist:
            return Response({'error': 'You are not part of this game.'}, status=403)

        if not player_game.is_turn:
            return Response({'error': 'Not your turn.'}, status=403)

        word_text = game.word.word.lower()  # رشته کلمه واقعی

        if position < 0 or position >= len(word_text):
            return Response({'error': 'Position is out of range.'}, status=400)

        if Guess.objects.filter(player_game=player_game, position=position, is_correct=True).exists():
            return Response({'error': 'You already guessed the correct letter for this position.'}, status=400)

        # ثبت حدس
        is_correct = (letter == word_text[position])
        with transaction.atomic():
            Guess.objects.create(player_game=player_game, letter=letter, position=position, is_correct=is_correct)

            if is_correct:
                player_game.score += 20
            else:
                player_game.score -= 20
            player_game.save()

        # بررسی تکمیل کلمه
        guessed_positions = Guess.objects.filter(player_game=player_game, is_correct=True).values_list('position', flat=True)
        all_positions = set(range(len(word_text)))

        if set(guessed_positions) == all_positions:
            game.status = 'finished'
            self._handle_game_finish(game)
            return Response({'message': 'Correct guess! Game finished.', 'winner': game.winner.username if game.winner else None})

        # تغییر نوبت و حدس ربات
        self._update_turn(game, player_game)

        return Response({'message': 'Correct!' if is_correct else 'Wrong!', 'score': player_game.score})

    def _validate_input(self, letter, position):
        if not letter or len(letter) != 1 or not letter.isalpha():
            return {'error': 'You must guess a single letter.', 'status': 400}
        try:
            position = int(position)
        except (TypeError, ValueError):
            return {'error': 'Position must be provided as an integer.', 'status': 400}
        return {'letter': letter.lower(), 'position': position}

    def _handle_game_finish(self, game):
        players = list(game.players.all())
        if len(players) == 2:
            p1, p2 = players[0], players[1]
            profile1, _ = UserProfile.objects.get_or_create(user=p1.user)
            profile2, _ = UserProfile.objects.get_or_create(user=p2.user)

            if p1.score > p2.score:
                winner = p1
                game.winner = winner.user
                profile1.score += 5
                profile1.save()
            elif p1.score < p2.score:
                winner = p2
                game.winner = winner.user
                profile2.score += 5
                profile2.save()
            else:
                game.winner = None
                profile1.score += 1
                profile2.score += 1
                profile1.save()
                profile2.save()
        else:
            game.winner = None

        game.save()

    def _update_turn(self, game, current_player_game):
        if game.mode == 'multi':
            players = list(game.players.all())
            for pg in players:
                pg.is_turn = (pg != current_player_game)
                pg.save()
        else:
            # بازی تک نفره: نوبت بازیکن فعلی False می‌شود
            current_player_game.is_turn = False
            current_player_game.save()

            # حدس ربات
            bot_pg = PlayerGame.objects.filter(game=game, user__username='bot').first()
            if bot_pg:
                self._bot_guess(game, bot_pg)

            # نوبت بازیکن می‌شود
            current_player_game.is_turn = True
            current_player_game.save()

    def _bot_guess(self, game, bot_pg):
        guessed_positions = Guess.objects.filter(player_game__game=game, is_correct=True).values_list('position', flat=True)
        word_text = game.word.word.lower()

        empty_positions = [i for i in range(len(word_text)) if i not in guessed_positions]

        if empty_positions:
            pos = random.choice(empty_positions)
            letter = word_text[pos]
            is_correct = True
        else:
            guessed_letters = Guess.objects.filter(player_game__game=game).values_list('letter', flat=True)
            alphabet = set('abcdefghijklmnopqrstuvwxyz')
            remaining_letters = list(alphabet - set(guessed_letters))

            if not remaining_letters:
                return

            letter = random.choice(remaining_letters)
            pos = 0
            is_correct = (letter == word_text[pos])

        Guess.objects.create(player_game=bot_pg, letter=letter, position=pos, is_correct=is_correct)
        bot_pg.score += 20 if is_correct else -20
        bot_pg.save()



class PlayerGuessesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, game_id):
        try:
            game = Game.objects.get(id=game_id)
        except Game.DoesNotExist:
            return Response({'error': 'Game not found.'}, status=404)

        try:
            player_game = PlayerGame.objects.get(game=game, user=request.user)
        except PlayerGame.DoesNotExist:
            return Response({'error': 'You are not part of this game.'}, status=403)

        guesses = Guess.objects.filter(player_game=player_game).order_by('guessed_at')
        data = []
        for guess in guesses:
            data.append({
                'letter': guess.letter,
                'position': guess.position,
                'is_correct': guess.is_correct,
                'guessed_at': guess.guessed_at,
            })

        return Response({'guesses': data})

class PausedGamesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        paused_games = Game.objects.filter(
            status='paused',
            paused_at__isnull=False
        ).filter(
            models.Q(created_by=user) | models.Q(players__user=user)
        ).distinct()

        data = []
        for game in paused_games:
            players_data = []

            for pg in game.players.all():
                guesses = Guess.objects.filter(player_game=pg).order_by('guessed_at')

                guesses_data = [{
                    'letter': g.letter,
                    'position': g.position,
                    'is_correct': g.is_correct,
                    'guessed_at': g.guessed_at,
                } for g in guesses]

                players_data.append({
                    'username': pg.user.username,
                    'score': pg.score,
                    'guesses': guesses_data
                })

            data.append({
                'game_id': game.id,
                'difficulty': game.difficulty,
                'started_at': game.started_at,
                'paused_at': game.paused_at,
                'status': game.status,
                'players': players_data
            })

        return Response({'paused_games': data})

    

class FinishedGamesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        finished_games = Game.objects.filter(
            status='finished'
        ).filter(
            models.Q(created_by=user) | models.Q(players__user=user)
        ).distinct()

        data = []
        for game in finished_games:
            player_scores = []
            for pg in game.players.all():  # فرض بر اینه related_name='players' روی PlayerGame ست شده
                player_scores.append({
                    'username': pg.user.username,
                    'score': pg.score
                })

            data.append({
                'game_id': game.id,
                'difficulty': game.difficulty,
                'started_at': game.started_at,
                'finished_at': game.finished_at,
                'winner': game.winner.username if game.winner else 'tie',
                'status': game.status,
                'player_scores': player_scores
            })

        return Response({'finished_games': data})
    
    

class PauseGameView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, game_id):
        try:
            game = Game.objects.get(id=game_id)
        except Game.DoesNotExist:
            return Response({'error': 'Game not found.'}, status=404)

        try:
            player_game = PlayerGame.objects.get(game=game, user=request.user)
        except PlayerGame.DoesNotExist:
            return Response({'error': 'You are not part of this game.'}, status=403)

        # فقط بازیکنی که نوبتش هست می‌تونه پاز کنه
        if not player_game.is_turn:
            return Response({'error': 'It is not your turn to pause the game.'}, status=403)

        if game.status != 'active':
            return Response({'error': 'Game is not active.'}, status=400)

        if game.paused_at is not None:
            return Response({'error': 'Game is already paused.'}, status=400)

        # ثبت زمان توقف و تغییر وضعیت به paused
        game.paused_at = timezone.now()
        game.status = 'paused'
        game.save()

        return Response({'message': 'Game paused successfully.'}, status=200)
    
class ResumeGameView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, game_id):
        try:
            game = Game.objects.get(id=game_id)
        except Game.DoesNotExist:
            return Response({'error': 'Game not found.'}, status=404)

        try:
            player_game = PlayerGame.objects.get(game=game, user=request.user)
        except PlayerGame.DoesNotExist:
            return Response({'error': 'You are not part of this game.'}, status=403)

        # فقط بازیکنی که نوبتش هست می‌تونه بازی رو ادامه بده
        if not player_game.is_turn:
            return Response({'error': 'It is not your turn to resume the game.'}, status=403)

        if game.status != 'paused':
            return Response({'error': 'Game is not paused.'}, status=400)

        if game.paused_at is None:
            return Response({'error': 'Game is not paused.'}, status=400)

        # محاسبه و اضافه کردن زمان توقف به started_at
        pause_duration = timezone.now() - game.paused_at
        if game.started_at:
            game.started_at += pause_duration

        game.paused_at = None
        game.status = 'active'
        game.save()

        return Response({'message': 'Game resumed successfully.'}, status=200)



class GameStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, game_id):
        try:
            game = Game.objects.get(id=game_id)
        except Game.DoesNotExist:
            return Response({'error': 'Game not found'}, status=404)

        try:
            PlayerGame.objects.get(game=game, user=request.user)
        except PlayerGame.DoesNotExist:
            return Response({'error': 'You are not part of this game.'}, status=403)

        guesses = Guess.objects.filter(player_game__game=game).order_by('guessed_at')

        players = game.players.all()
        players_data = []
        for pg in players:
            players_data.append({
                'username': pg.user.username,
                'score': pg.score,
                'is_turn': pg.is_turn,
            })

        guesses_by_player = {}
        for guess in guesses:
            username = guess.player_game.user.username
            if username not in guesses_by_player:
                guesses_by_player[username] = []
            guesses_by_player[username].append({
                'letter': guess.letter,
                'position': guess.position,
                'is_correct': guess.is_correct,
                'guessed_at': guess.guessed_at,
            })

        # محاسبه زمان باقی‌مانده
        elapsed = (now() - game.started_at).total_seconds() / 60 if game.started_at else 0
        remaining = max(game.time_limit_minutes - elapsed, 0)

        data = {
            'game_id': game.id,
            'word_length': len(game.word.word),
            'difficulty': game.difficulty,
            'status': game.status,
            'time_limit_minutes': game.time_limit_minutes,
            'time_elapsed_minutes': elapsed,
            'time_remaining_minutes': remaining,
            'paused_at': game.paused_at,
            'current_turn': game.current_turn.user.username if game.current_turn else None,
            'players': players_data,
            'guesses': guesses_by_player,
        }

        if game.status == 'finished':
            data['winner'] = game.winner.username if game.winner else 'draw'

        return Response(data)
    


class ActiveGamesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        active_games = Game.objects.filter(
            status='active',
            players__user=user
        ).distinct()

        data = [{
            'id': game.id,
            'difficulty': game.difficulty,
            'started_at': game.started_at,
            'status': game.status,
        } for game in active_games]

        return Response({'active_games': data})
    

class WaitingGamesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        waiting_games = Game.objects.filter(
            status='waiting',
            created_by=user
        )

        data = [{
            'id': game.id,
            'difficulty': game.difficulty,
            'created_at': game.created_at,
            'status': game.status,
        } for game in waiting_games]

        return Response({'waiting_games': data})
    




# class UseHintView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request, game_id):
#         hint_type = request.data.get('hint_type')  # 'letter' یا 'description'
#         if hint_type not in ['letter', 'description']:
#             return Response({'error': 'Invalid hint type.'}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             game = Game.objects.get(id=game_id)
#         except Game.DoesNotExist:
#             return Response({'error': 'Game not found.'}, status=status.HTTP_404_NOT_FOUND)

#         try:
#             player_game = PlayerGame.objects.get(game=game, user=request.user)
#         except PlayerGame.DoesNotExist:
#             return Response({'error': 'You are not part of this game.'}, status=status.HTTP_403_FORBIDDEN)

#         # چک نوبت
#         if not player_game.is_turn:
#             return Response({'error': 'It is not your turn.'}, status=status.HTTP_403_FORBIDDEN)

#         # حداکثر دفعات استفاده از هینت‌ها:
#         max_letter_hints = 2
#         max_description_hints = 1

#         if hint_type == 'letter':
#             if player_game.letter_hints_used >= max_letter_hints:
#                 return Response({'error': 'You have used all your letter hints.'}, status=status.HTTP_403_FORBIDDEN)
#             if player_game.score < 20:
#                 return Response({'error': 'Not enough score to use this hint.'}, status=status.HTTP_403_FORBIDDEN)

#             # پیدا کردن اولین حرف درست حدس زده نشده
#             word = game.word.word.lower()  # فرض بر اینکه مدل Word فیلد word دارد
#             guessed_positions = Guess.objects.filter(player_game=player_game, is_correct=True).values_list('position', flat=True)
#             remaining_positions = [i for i in range(len(word)) if i not in guessed_positions]
#             if not remaining_positions:
#                 return Response({'error': 'No hints available, word already guessed.'}, status=status.HTTP_400_BAD_REQUEST)

#             hint_pos = remaining_positions[0]
#             hint_letter = word[hint_pos]

#             # کم کردن امتیاز و افزایش تعداد دفعات استفاده
#             player_game.score -= 20
#             player_game.letter_hints_used += 1
#             player_game.save()

#             return Response({'hint_type': 'letter', 'position': hint_pos, 'letter': hint_letter, 'score': player_game.score})

#         else:  # hint_type == 'description'
#             if player_game.description_hint_used:
#                 return Response({'error': 'You have already used the description hint.'}, status=status.HTTP_403_FORBIDDEN)
#             if player_game.score < 40:
#                 return Response({'error': 'Not enough score to use this hint.'}, status=status.HTTP_403_FORBIDDEN)

#             # کم کردن امتیاز و ثبت استفاده
#             player_game.score -= 40
#             player_game.description_hint_used = True
#             player_game.save()

#             # نمایش توضیح کلمه
#             description = game.word.description  # فرض بر این است که مدل Word فیلد description دارد

#             return Response({'hint_type': 'description', 'description': description, 'score': player_game.score})



class UseHintView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, game_id):
        hint_type = request.data.get('hint_type')  # 'letter' یا 'hint'
        position = request.data.get('position')  # اختیاری برای hint_type == 'letter'

        if hint_type not in ['letter', 'hint']:
            return Response({'error': 'Invalid hint type.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            game = Game.objects.get(id=game_id)
        except Game.DoesNotExist:
            return Response({'error': 'Game not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            player_game = PlayerGame.objects.get(game=game, user=request.user)
        except PlayerGame.DoesNotExist:
            return Response({'error': 'You are not part of this game.'}, status=status.HTTP_403_FORBIDDEN)

        if not player_game.is_turn:
            return Response({'error': 'It is not your turn.'}, status=status.HTTP_403_FORBIDDEN)

        max_hints_total = 2
        if player_game.hints_used >= max_hints_total:
            return Response({'error': 'You have used all your hints.'}, status=status.HTTP_403_FORBIDDEN)

        word_text = game.word.word.lower()

        if hint_type == 'letter':
            if player_game.letter_hint_used:
                return Response({'error': 'You have already used a letter hint.'}, status=status.HTTP_403_FORBIDDEN)

            if player_game.score < 20:
                return Response({'error': 'Not enough score to use this hint.'}, status=status.HTTP_403_FORBIDDEN)

            if position is None:
                return Response({'error': 'Position is required for letter hint.'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                position = int(position)
            except ValueError:
                return Response({'error': 'Position must be an integer.'}, status=status.HTTP_400_BAD_REQUEST)

            if position < 0 or position >= len(word_text):
                return Response({'error': 'Invalid position.'}, status=status.HTTP_400_BAD_REQUEST)

            if Guess.objects.filter(player_game=player_game, position=position, is_correct=True).exists():
                return Response({'error': 'Letter at this position already guessed correctly.'}, status=status.HTTP_400_BAD_REQUEST)

            hint_letter = word_text[position]

            # به‌روزرسانی وضعیت بازیکن
            player_game.score -= 20
            player_game.hints_used += 1
            player_game.letter_hint_used = True
            player_game.save()

            return Response({
                'hint_type': 'letter',
                'position': position,
                'letter': hint_letter,
                'score': player_game.score
            })

        else:  # hint_type == 'hint'
            if player_game.hint_used:
                return Response({'error': 'You have already used the hint text.'}, status=status.HTTP_403_FORBIDDEN)

            if player_game.score < 30:
                return Response({'error': 'Not enough score to use this hint.'}, status=status.HTTP_403_FORBIDDEN)

            player_game.score -= 30
            player_game.hints_used += 1
            player_game.hint_used = True
            player_game.save()

            hint_text = game.word.hint

            return Response({
                'hint_type': 'hint',
                'hint': hint_text,
                'score': player_game.score
            })
