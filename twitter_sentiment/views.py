from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
# from .models import LeagueInfo
import os, sys


from .util_functions import *






# Create your views here.
def index(request):
    context = {
        'authenticated': 'False'
    }
    
    return HttpResponse(render(request, 'twitter_sentiment/index.html', context))

def query_input(request):
    q = request.POST.get('query', None)

    return redirect('query={}/'.format(q))

def query(request, q):
    # Initialize environment variables
    import environ
    env = environ.Env()
    environ.Env.read_env()

    # Developer keys
    consumer_key = env('TWITTER_CONSUMER_KEY')
    consumer_key_secret = env('TWITTER_CONSUMER_KEY_SECRET')

    # Secret token (not used anywhere)
    access_token_key = env('TWITTER_ACCESS_TOKEN_KEY')
    access_token_key_secret = env('TWITTER_ACCESS_TOKEN_KEY_SECRET')

    # Initialize api instance
    auth = tweepy.OAuthHandler(consumer_key, consumer_key_secret)
    auth.set_access_token(access_token_key, access_token_key_secret)
    twitter_api = tweepy.API(auth)
    print('Authorization successful:', twitter_api != None)

    # Load pre-trained model
    sys.modules['__main__'].ClfSwitcher = ClfSwitcher
    sys.modules['__main__'].TwitterSentimentModel = TwitterSentimentModel
    model_location = 'https://github.com/DesiPilla/twitter-sentiment-analysis/blob/master/code/trained_model.pickle?raw=true'
    model = load(urlopen(model_location))

    # Run query
    tweets = getTweets(twitter_api, search_term=q, num_tweets=250)
    # agg_sent, agg_unc = model.predict_agg(tweets, verbose=True)
    y_pred = model.predict(tweets)
    n_pos = (y_pred == 4).sum()
    n_neu = (y_pred == 2).sum()
    n_neg = (y_pred == 0).sum()
    agg_sent = ((y_pred - 2) / 2).mean()

    context = {
        'authenticated':twitter_api!=None,
        'tweets':tweets[:10],
        'perc_pos': n_pos / len(y_pred),
        'perc_neu': n_neu / len(y_pred),
        'perc_neg': n_neg / len(y_pred),
        'agg_sent': '{:.2%}'.format(agg_sent),
        'agg_unc': '{:.2%}'.format(model.agg_unc),
    }

    return HttpResponse(render(request, 'twitter_sentiment/index.html', context))