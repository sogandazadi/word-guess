from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import ActiveGamesView, CreateMultiPlayerGameView, CreateSinglePlayerGameView, FinishedGamesView, GameStatusView, JoinGameView, JoinableGamesView, LeaderboardView, LogoutView, MyProfileView, PauseGameView, PausedGamesView, ResumeGameView, UpdateAvatarView, UpdateEmailView, UpdatePasswordView, UpdateUsernameView, UseHintView, WaitingGamesView
from .views import GuessLetterView
from .views import PlayerGuessesView

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('games/create/multi-player', CreateMultiPlayerGameView.as_view(), name='create_multi_game'),
    path('games/create/single-player', CreateSinglePlayerGameView.as_view(), name='create_single_game'),
    path('games/<int:game_id>/join/', JoinGameView.as_view(), name='join_game'),
    path('games/<int:game_id>/guess/', GuessLetterView.as_view(), name='guess-letter'),
    path('games/<int:game_id>/guesses/', PlayerGuessesView.as_view(), name='player-guesses'),
    path('games/paused/', PausedGamesView.as_view(), name='paused_games'),
    path('games/finished/', FinishedGamesView.as_view(), name='finished_games'),
    path('games/<int:game_id>/status/', GameStatusView.as_view(), name='game-status'),
    path('games/<int:game_id>/pause/', PauseGameView.as_view(), name='pause-game'),
    path('games/<int:game_id>/resume/', ResumeGameView.as_view(), name='resume-game'),
    path('games/active/', ActiveGamesView.as_view(), name='active_games'),
    path('games/waiting/', WaitingGamesView.as_view(), name='waiting_games'),
    path('profile/', MyProfileView.as_view(), name='my-profile'),
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
    path('games/<int:game_id>/hint/', UseHintView.as_view(), name='use_hint'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/update-username/', UpdateUsernameView.as_view(), name='update-username'),
    path('profile/update-email/', UpdateEmailView.as_view(), name='update-email'),
    path('profile/update-password/', UpdatePasswordView.as_view(), name='update-password'),
    path('profile/update-avatar/', UpdateAvatarView.as_view(), name='update-avatar'),
    path('games/joinable/', JoinableGamesView.as_view(), name='joinable-games'),

]