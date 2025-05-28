import re
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework.exceptions import ValidationError
from rest_framework import permissions, status
from .models import Game, PlayerGame, UserProfile, Word
from .serializers import GameSerializer, UserProfileSerializer
import random
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.utils.timezone import now
from django.db import models
from .models import Game, PlayerGame, Guess, UserProfile
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
from rest_framework.parsers import MultiPartParser, FormParser
import os
from django.conf import settings


class JoinableGamesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        games = Game.objects.filter(status='waiting').exclude(created_by=user)
        serializer = GameSerializer(games, many=True)

        data = serializer.data
        for game, game_data in zip(games, data):
            creator = game.created_by
            username = creator.username

            default_avatar_url = request.build_absolute_uri(settings.MEDIA_URL + 'avatars/default_avatar.png')
            if hasattr(creator, 'userprofile') and creator.userprofile.avatar:
                avatar_url = request.build_absolute_uri(creator.userprofile.avatar.url)
            else:
                avatar_url = default_avatar_url

            game_data['created_by'] = {
                'username': username,
                'avatar': avatar_url
            }

        return Response(data)


class UpdateUsernameView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        new_username = request.data.get('username')
        if not new_username:
            return Response({'error': 'نام کاربری الزامی است.'}, status=status.HTTP_400_BAD_REQUEST)

        if new_username == request.user.username:
            return Response({'error': 'نام کاربری جدید نباید با قبلی یکسان باشد.'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=new_username).exists():
            return Response({'error': 'این نام کاربری قبلاً استفاده شده است.'}, status=status.HTTP_400_BAD_REQUEST)

        request.user.username = new_username
        request.user.save()
        return Response({'message': 'نام کاربری با موفقیت به‌روزرسانی شد.'})    

class UpdateEmailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        new_email = request.data.get('email')
        if not new_email:
            return Response({'error': 'ایمیل الزامی است.'}, status=status.HTTP_400_BAD_REQUEST)

        if new_email == request.user.email:
            return Response({'error': 'ایمیل جدید نباید با ایمیل فعلی یکسان باشد.'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=new_email).exists():
            return Response({'error': 'این ایمیل قبلاً استفاده شده است.'}, status=status.HTTP_400_BAD_REQUEST)

        request.user.email = new_email
        request.user.save()
        return Response({'message': 'ایمیل با موفقیت به‌روزرسانی شد.'})

    
class UpdatePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        new_password = request.data.get('password')
        if not new_password:
            return Response({'error': 'رمز عبور الزامی است.'}, status=status.HTTP_400_BAD_REQUEST)

        if request.user.check_password(new_password):
            return Response({'error': 'رمز عبور جدید نباید با رمز عبور فعلی یکسان باشد.'}, status=status.HTTP_400_BAD_REQUEST)

        if len(new_password) < 8:
            return Response({'error': 'رمز عبور باید حداقل ۸ کاراکتر داشته باشد.'}, status=status.HTTP_400_BAD_REQUEST)
        if not re.search(r'\d', new_password):
            return Response({'error': 'رمز عبور باید حداقل شامل یک عدد باشد.'}, status=status.HTTP_400_BAD_REQUEST)
        if not re.search(r'[A-Za-z]', new_password):
            return Response({'error': 'رمز عبور باید شامل حروف نیز باشد.'}, status=status.HTTP_400_BAD_REQUEST)

        request.user.set_password(new_password)
        request.user.save()
        return Response({'message': 'رمز عبور با موفقیت به‌روزرسانی شد.'})

    
class UpdateAvatarView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def patch(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)

        new_avatar = request.FILES.get('avatar')
        if not new_avatar:
            return Response({'error': 'No avatar provided.'}, status=status.HTTP_400_BAD_REQUEST)


        if profile.avatar and profile.avatar.name and 'default_avatar.png' not in profile.avatar.name:
            old_avatar_path = os.path.join(settings.MEDIA_ROOT, profile.avatar.name)
            if os.path.exists(old_avatar_path):
                os.remove(old_avatar_path)

        profile.avatar = new_avatar
        profile.save()

        return Response({'message': 'Avatar updated successfully.'})
    

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
        avatar = request.FILES.get("avatar")

        if not username or not email or not password:
            return Response({"error": "همه فیلدها الزامی هستند."}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({"error": "این نام کاربری قبلاً استفاده شده است."}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({"error": "این ایمیل قبلاً استفاده شده است."}, status=status.HTTP_400_BAD_REQUEST)

        if len(password) < 8:
            return Response({"error": "پسورد باید حداقل ۸ کاراکتر باشد."}, status=status.HTTP_400_BAD_REQUEST)

        if not re.search(r"[A-Z]", password):
            return Response({"error": "پسورد باید حداقل یک حرف بزرگ داشته باشد."}, status=status.HTTP_400_BAD_REQUEST)

        if not re.search(r"\d", password):
            return Response({"error": "پسورد باید حداقل یک عدد داشته باشد."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, email=email, password=password)

        profile = UserProfile.objects.create(user=user)
        if avatar:
            profile.avatar = avatar
            profile.save()

        return Response({"message": "ثبت‌نام با موفقیت انجام شد!"}, status=status.HTTP_201_CREATED)
    

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
            return Response({'error': 'درجه سختی را اشتباه وارد کرده اید'}, status=status.HTTP_400_BAD_REQUEST)

        word = get_random_word(difficulty)

        time_limits = {'easy': 3, 'medium': 2, 'hard': 5}
        time_limit = time_limits[difficulty]

        game = Game.objects.create(
            created_by=request.user,
            difficulty=difficulty,
            word=word,
            time_limit_minutes=time_limit,
            status='waiting',
            mode='multi',
            player_1=request.user,  
            player_2=None            
        )

        pg = PlayerGame.objects.create(game=game, user=request.user, is_turn=True)


        game.current_turn = pg
        game.save()

        serializer = GameSerializer(game)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
class CreateSinglePlayerGameView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        difficulty = request.data.get('difficulty')
        if difficulty not in ['easy', 'medium', 'hard']:
            return Response({'error': 'درجه سختی را اشتباه وارد کرده اید'}, status=status.HTTP_400_BAD_REQUEST)

        word = get_random_word(difficulty)
        time_limits = {'easy': 3, 'medium': 2, 'hard': 5}
        time_limit = time_limits[difficulty]

        game = Game.objects.create(
            created_by=request.user,
            difficulty=difficulty,
            word=word,
            time_limit_minutes=time_limit,
            status='active',
            mode='single',
            started_at=timezone.now(),
            player_1=request.user,    
            player_2=bot_user        
        )


        player_real = PlayerGame.objects.create(game=game, user=request.user, is_turn=True)


        try:
            bot_user = User.objects.get(username='bot')
        except User.DoesNotExist:
            return Response({'error': 'کاربر bot پیدا نشد'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        PlayerGame.objects.create(game=game, user=bot_user, is_turn=False)

        game.current_turn = player_real
        game.save()

        serializer = GameSerializer(game)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class LeaderboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        top_users = UserProfile.objects.exclude(user__username='bot').order_by('-score')[:10]

        data = []
        for profile in top_users:
            if profile.avatar and hasattr(profile.avatar, 'url'):
                avatar_url = request.build_absolute_uri(profile.avatar.url)
            else:
                avatar_url = request.build_absolute_uri(settings.MEDIA_URL + 'avatars/default_avatar.png')

            data.append({
                'username': profile.user.username,
                'score': profile.score,
                'rank': profile.get_rank(),
                'avatar_url': avatar_url,  
            })

        return Response(data)


class JoinGameView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, game_id):
        try:
            game = Game.objects.get(id=game_id)
        except Game.DoesNotExist:
            return Response({'error': 'بازی پیدا نشد'}, status=status.HTTP_404_NOT_FOUND)

        if game.mode != 'multi':
            return Response({'error': 'نمی توان به بازی یک نفره اضافه شد'}, status=status.HTTP_400_BAD_REQUEST)

        if game.status != 'waiting':
            return Response({'error': 'نمی توان به بازی اضافه شد'}, status=status.HTTP_400_BAD_REQUEST)

        if game.players.filter(user=request.user).exists():
            return Response({'error': 'شما از قبل به این بازی اضافه شده اید'}, status=status.HTTP_400_BAD_REQUEST)

        PlayerGame.objects.create(game=game, user=request.user, is_turn=False)

        if game.players.count() == 2:
            game.player_2 = game.players.exclude(user=game.created_by).first().user
            game.save()

        players = list(game.players.all())
        random_player = random.choice(players)
        for player in players:
            player.is_turn = (player == random_player)
            player.save()

        game.status = 'active'
        game.started_at = timezone.now() 
        game.save()

        return Response({'message': 'با موفقیت به بازی اضافه شدید'}, status=status.HTTP_200_OK)
    

class GuessLetterView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, game_id):
        letter = request.data.get('letter', '')
        position = request.data.get('position')

        validation = self._validate_input(letter, position)
        if 'error' in validation:
            return Response({'error': validation['error']}, status=validation['status'])

        letter = validation['letter']
        position = validation['position']

        try:
            game = Game.objects.get(id=game_id)
        except Game.DoesNotExist:
            return Response({'error': 'بازی پیدا نشد'}, status=404)

        if game.status != 'active':
            return Response({'error': 'بازی در حال انجام نیست'}, status=400)

        if not game.started_at:
            return Response({'error': 'بازی هنوز شروع نشده است'}, status=400)

        elapsed_minutes = (now() - game.started_at).total_seconds() / 60
        if elapsed_minutes > game.time_limit_minutes:
            game.status = 'finished'
            self._handle_game_finish(game)
            return Response({'error': 'زمان شما به پایان رسیده! بازی تمام شد', 'برنده': game.winner.username if game.winner else 'مساوی'}, status=403)

        try:
            player_game = PlayerGame.objects.get(game=game, user=request.user)
        except PlayerGame.DoesNotExist:
            return Response({'error': 'شما عضو این بازی نیستید'}, status=403)

        if not player_game.is_turn:
            return Response({'error': 'نوبت شما نیست'}, status=403)

        word_text = game.word.word

        if position < 0 or position >= len(word_text):
            return Response({'error': 'جایگاه وارد شده معتبر نیست'}, status=400)

        if Guess.objects.filter(player_game=player_game, position=position, is_correct=True).exists():
            return Response({'error': 'برای این جایگاه قبلاً حدس درست وارد شده'}, status=400)

        is_correct = (letter.strip() == word_text[position].strip())

        with transaction.atomic():
            Guess.objects.create(player_game=player_game, letter=letter, position=position, is_correct=is_correct)

            if is_correct:
                player_game.score += 20
            else:
                player_game.score -= 20
            player_game.save()

        guessed_positions = Guess.objects.filter(player_game=player_game, is_correct=True).values_list('position', flat=True)
        all_positions = set(range(len(word_text)))

        if set(guessed_positions) == all_positions:
            game.status = 'finished'
            self._handle_game_finish(game)
            return Response({'message': 'تبریک! شما تمام کلمه را حدس زدید', 'برنده': game.winner.username if game.winner else None})

        self._update_turn(game, player_game)

        return Response({'message': 'حدس درست بود!' if is_correct else 'حدس اشتباه بود!', 'امتیاز': player_game.score})

    def _validate_input(self, letter, position):
        if not letter or len(letter.strip()) != 1 or not re.match(r'^[آ-ی]$', letter.strip()):
            return {'error': 'شما باید یک حرف فارسی وارد کنید', 'status': 400}
        try:
            position = int(position)
        except (TypeError, ValueError):
            return {'error': 'جایگاه باید عدد صحیح باشد', 'status': 400}
        return {'letter': letter.strip(), 'position': position}

    def _handle_game_finish(self, game):
        players = list(game.players.all())
        if len(players) == 2:
            p1, p2 = players[0], players[1]
            profile1, _ = UserProfile.objects.get_or_create(user=p1.user)
            profile2, _ = UserProfile.objects.get_or_create(user=p2.user)

            if p1.score > p2.score:
                game.winner = p1.user
                profile1.score += 5
            elif p2.score > p1.score:
                game.winner = p2.user
                profile2.score += 5
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
            current_player_game.is_turn = False
            current_player_game.save()

            bot_pg = PlayerGame.objects.filter(game=game, user__username='bot').first()
            if bot_pg:
                self._bot_guess(game, bot_pg)

            current_player_game.is_turn = True
            current_player_game.save()

    def _bot_guess(self, game, bot_pg):
        guessed_positions = Guess.objects.filter(player_game__game=game, is_correct=True).values_list('position', flat=True)
        word_text = game.word.word

        empty_positions = [i for i in range(len(word_text)) if i not in guessed_positions]

        if empty_positions:
            pos = random.choice(empty_positions)
            letter = word_text[pos]
            is_correct = True
        else:
            guessed_letters = Guess.objects.filter(player_game__game=game).values_list('letter', flat=True)
            all_letters = set('اآبپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی')
            remaining_letters = list(all_letters - set(guessed_letters))

            if not remaining_letters:
                return

            letter = random.choice(remaining_letters)
            pos = 0
            is_correct = (letter.strip() == word_text[pos].strip())

        Guess.objects.create(player_game=bot_pg, letter=letter, position=pos, is_correct=is_correct)
        bot_pg.score += 20 if is_correct else -20
        bot_pg.save()


class PlayerGuessesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, game_id):
        try:
            game = Game.objects.get(id=game_id)
        except Game.DoesNotExist:
            return Response({'error': 'بازی پیدا نشد'}, status=404)

        try:
            player_game = PlayerGame.objects.get(game=game, user=request.user)
        except PlayerGame.DoesNotExist:
            return Response({'error': 'شما عضوی از این بازی نیستید'}, status=403)

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

                avatar_url = None
                if hasattr(pg.user, 'userprofile') and pg.user.userprofile.avatar:
                    avatar_url = request.build_absolute_uri(pg.user.userprofile.avatar.url)
                else:
                    avatar_url = request.build_absolute_uri(settings.MEDIA_URL + 'avatars/default_avatar.png')

                players_data.append({
                    'username': pg.user.username,
                    'score': pg.score,
                    'guesses': guesses_data,
                    'avatar': avatar_url,
                })

            data.append({
                'game_id': game.id,
                'paused_by': game.paused_by.username if game.paused_by else None,
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
            for pg in game.players.all():  
                # افزودن آواتار
                if hasattr(pg.user, 'userprofile') and pg.user.userprofile.avatar:
                    avatar_url = request.build_absolute_uri(pg.user.userprofile.avatar.url)
                else:
                    avatar_url = request.build_absolute_uri(settings.MEDIA_URL + 'avatars/default_avatar.png')

                player_scores.append({
                    'username': pg.user.username,
                    'score': pg.score,
                    'avatar': avatar_url
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
            return Response({'error': 'بازی پیدا نشد'}, status=404)

        try:
            player_game = PlayerGame.objects.get(game=game, user=request.user)
        except PlayerGame.DoesNotExist:
            return Response({'error': 'شما عضوی از این بازی نیستید'}, status=403)


        if not player_game.is_turn:
            return Response({'error': 'نوبت شما نیست و نمی توانید بازی را متوقف کنید'}, status=403)

        if game.status != 'active':
            return Response({'error': 'بازی در حال انجام نیست'}, status=400)

        if game.paused_at is not None:
            return Response({'error': 'بازی از قبل متوقف شده است'}, status=400)


        game.paused_at = timezone.now()
        game.status = 'paused'
        game.save()

        return Response({'message': 'بازی با موفقیت متوقف شد'}, status=200)
    
class ResumeGameView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, game_id):
        try:
            game = Game.objects.get(id=game_id)
        except Game.DoesNotExist:
            return Response({'error': 'بازی پیدا نشد'}, status=404)

        try:
            player_game = PlayerGame.objects.get(game=game, user=request.user)
        except PlayerGame.DoesNotExist:
            return Response({'error': 'شما عضوی از این بازی نیستید'}, status=403)


        if not player_game.is_turn:
            return Response({'error': 'نوبت شما نیست و نمی توانید بازی را متوقف کنید'}, status=403)

        if game.status != 'paused':
            return Response({'error': 'بازی متوقف نشده است'}, status=400)

        if game.paused_at is None:
            return Response({'error': 'باز یمتوقف نشده است'}, status=400)


        pause_duration = timezone.now() - game.paused_at
        if game.started_at:
            game.started_at += pause_duration

        game.paused_at = None
        game.status = 'active'
        game.save()

        return Response({'message': 'بازی با موفقیت متوقف شد'}, status=200)

class GameStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, game_id):
        try:
            game = Game.objects.get(id=game_id)
        except Game.DoesNotExist:
            return Response({'error': 'بازی پیدا نشد'}, status=404)

        try:
            PlayerGame.objects.get(game=game, user=request.user)
        except PlayerGame.DoesNotExist:
            return Response({'error': 'شما عضو این بازی نیستید'}, status=403)

        guesses = Guess.objects.filter(player_game__game=game).order_by('guessed_at')

        players = game.players.all()
        players_data = []
        default_avatar_url = request.build_absolute_uri(settings.MEDIA_URL + 'avatars/default_avatar.png')

        for pg in players:
            avatar_url = default_avatar_url
            if hasattr(pg.user, 'userprofile') and pg.user.userprofile.avatar:
                avatar_url = request.build_absolute_uri(pg.user.userprofile.avatar.url)

            players_data.append({
                'username': pg.user.username,
                'score': pg.score,
                'is_turn': pg.is_turn,
                'avatar': avatar_url,
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

        elapsed = (now() - game.started_at).total_seconds() / 60 if game.started_at else 0
        remaining = max(game.time_limit_minutes - elapsed, 0)

        data = {
            'game_id': game.id,
            'created_by': game.created_by.username,
            'word_length': len(game.word.word),
            'word_description': game.word.description,
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

        data = []
        for game in active_games:
            players_data = []

            for pg in game.players.all():
                if hasattr(pg.user, 'userprofile') and pg.user.userprofile.avatar:
                    avatar_url = request.build_absolute_uri(pg.user.userprofile.avatar.url)
                else:
                    avatar_url = request.build_absolute_uri(settings.MEDIA_URL + 'avatars/default_avatar.png')

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
                    'guesses': guesses_data,
                    'avatar': avatar_url  
                })

            data.append({
                'id': game.id,
                'difficulty': game.difficulty,
                'started_at': game.started_at,
                'status': game.status,
                'players': players_data,
                'is_turn': game.current_turn.user.username if game.current_turn else None
            })

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
            'created_by': game.created_by.username  
        } for game in waiting_games]

        return Response({'waiting_games': data})

class UseHintView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, game_id):
        hint_type = request.data.get('hint_type')
        position = request.data.get('position')

        if hint_type not in ['letter', 'hint']:
            return Response({'error': 'نوع راهنما نامعتبر است'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            game = Game.objects.get(id=game_id)
        except Game.DoesNotExist:
            return Response({'error': 'بازی پیدا نشد'}, status=status.HTTP_404_NOT_FOUND)

        try:
            player_game = PlayerGame.objects.get(game=game, user=request.user)
        except PlayerGame.DoesNotExist:
            return Response({'error': 'شما عضو این بازی نیستید'}, status=status.HTTP_403_FORBIDDEN)

        if not player_game.is_turn:
            return Response({'error': 'نوبت شما نیست'}, status=status.HTTP_403_FORBIDDEN)

        if player_game.hints_used >= 2:
            return Response({'error': 'شما از حداکثر تعداد راهنماها استفاده کرده‌اید'}, status=status.HTTP_403_FORBIDDEN)

        word_text = game.word.word.lower()

        if hint_type == 'letter':

            if player_game.score < 20:
                return Response({'error': 'امتیاز کافی برای استفاده از این راهنما را ندارید'}, status=status.HTTP_403_FORBIDDEN)

            if position is None:
                return Response({'error': 'برای راهنمای حرف باید جایگاه مشخص شود'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                position = int(position)
            except ValueError:
                return Response({'error': 'جایگاه باید عدد باشد'}, status=status.HTTP_400_BAD_REQUEST)

            if position < 0 or position >= len(word_text):
                return Response({'error': 'جایگاه وارد شده نامعتبر است'}, status=status.HTTP_400_BAD_REQUEST)

            if Guess.objects.filter(player_game=player_game, position=position, is_correct=True).exists():
                return Response({'error': 'حرف این جایگاه قبلاً درست حدس زده شده است'}, status=status.HTTP_400_BAD_REQUEST)

            hint_letter = word_text[position]

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

        else:  
            if player_game.hint_used:
                return Response({'error': 'شما قبلاً از راهنمای توضیحی استفاده کرده‌اید'}, status=status.HTTP_403_FORBIDDEN)

            if player_game.score < 30:
                return Response({'error': 'امتیاز کافی برای استفاده از این راهنما را ندارید'}, status=status.HTTP_403_FORBIDDEN)

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
