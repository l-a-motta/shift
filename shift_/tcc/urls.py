from django.urls import path

from . import views

app_name = 'tcc'
urlpatterns = [
	path('', views.search, name='search'),
	path('tweet/', views.search, name='search'),
	path('tweet/search', views.search, name='search'),
	path('tweet/loading_user', views.loading_user, name='loading_user'),
	path('tweet/loading_results', views.loading_results, name='loading_results'),
	path('tweet/user_detail', views.collect_user, name='collect_user'),
	path('tweet/trends', views.collect_multiple_trends, name='collect_multiple_trends'),
	path('tweet/trend_detail', views.collect_trend, name='collect_trend'),
	path('tweet/retweets', views.collect_retweets, name='collect_retweets'),
	path('tweet/collect', views.collect, name='collect'),
	path('tweet/analyze_tweet', views.analyze_tweet, name='analyze_tweet'),
	path('tweet/analyze_user', views.analyze_user, name='analyze_user'),
	path('tweet/error', views.error, name='error'),
	path('tweet/user_protected', views.user_protected, name='user_protected'),
	path('tweet/nothing', views.nothing, name='nothing'),
]