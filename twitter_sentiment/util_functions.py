# Import basic packages
# from sklearn.model_selection import GridSearchCV
from sklearn.base import BaseEstimator
# from sklearn.pipeline import Pipeline
# from sklearn.ensemble import RandomForestClassifier
# from sklearn.neighbors import KNeighborsClassifier
# from sklearn.linear_model import SGDClassifier, Perceptron, LogisticRegression
# from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import SVC
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.metrics import confusion_matrix, classification_report, roc_curve, auc
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Import other relevant packages
import re
import string
# from wordcloud import WordCloud, STOPWORDS

# Import and download NLP functions
# import nltk
# from nltk.corpus import stopwords
# from nltk.corpus import wordnet as wn
# from nltk.tokenize import word_tokenize
# nltk.download('punkt')
# nltk.download('stopwords')
# nltk.download('wordnet')
# nltk.download('averaged_perceptron_tagger')

# Import sklearn functions

# Import estimators

# Import streamlined methodology methods


def print_balance(df, col='senti'):
    if type(df) == pd.DataFrame:
        counts = df[col].value_counts(normalize=True)
    else:
        labels, counts = np.unique(y_test, return_counts=True)
        counts = dict(zip(labels, counts / len(y_test)))

    print('This dataset contains {0} negative tweets ({1:.1%})'.format(
        int(counts[0]*len(df)), counts[0]))
    print('This dataset contains {0} neutral tweets ({1:.1%})'.format(
        int(counts[2]*len(df)), counts[2]))
    print('This dataset contains {0} positive tweets ({1:.1%})'.format(
        int(counts[4]*len(df)), counts[4]))
    return counts


def balance(df, col='senti', weights=(1, 1, 1)):
    # Get the number of observations with each classification
    counts = df[col].value_counts(normalize=True)

    # Get the smallest number of observations for a sentiment label
    minNum = int(counts.min() * len(df))

    # Split the observations by sentiment and keep the same number of observations for each
    df_neg = df[df.senti == 0].iloc[:int(minNum*weights[0]), :]
    df_neu = df[df.senti == 2].iloc[:int(minNum*weights[1]), :]
    df_pos = df[df.senti == 4].iloc[:int(minNum*weights[2]), :]

    # Combine observations back into one dataframe
    df_bal = pd.concat([df_neg, df_neu, df_pos])
    return df_bal


def clean_sentiment(s):
    '''
    This function cleans the sentiment label for tweets in the Sanders Analytics dataset.

    Inputs: string (sentiment label : {'negative', 'neutral', 'positive'})
    Outputs: integer (sentiment label : {0, 2, 4})
    '''
    if s == 'positive':
        return 4
    elif s == 'negative':
        return 0
    else:
        return 2


def preprocessTweets(text):
    text = str(text)
    text = text.translate(str.maketrans(
        '', '', string.punctuation))    # Remove punctuation
    text = re.sub('((www\.[^\s]+)|(https?://[^\s]+))',
                  'URL', text)     # Remove URLs
    # Remove usernames
    text = re.sub('@[^\s]+', 'AT_USER', text)
    return text


class ClfSwitcher(BaseEstimator):

    def __init__(self, estimator=SVC()):
        """
        A Custom BaseEstimator that can switch between classifiers.
        :param estimator: sklearn object - The classifier
        """

        self.estimator = estimator

    def fit(self, X, y=None, **kwargs):
        self.estimator.fit(X, y)
        return self

    def predict(self, X, y=None):
        return self.estimator.predict(X)

    def predict_proba(self, X):
        return self.estimator.predict_proba(X)

    def score(self, X, y):
        return self.estimator.score(X, y)


class TwitterSentimentModel():

    def __init__(self):
        pass

    def fit(self, X, y, classifier='all', cv=10, verbose=False):

        X = [preprocessTweets(t) for t in X]

        # Create the Pipeline object
        pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(lowercase=True,
                                      strip_accents='ascii',
                                      stop_words='english')),
            ('clf', ClfSwitcher())
        ])

        # this is where we define the values for GridSearchCV to iterate over
        parameters = [
            {  # For SVM, the best accuracy was 70.67% on the test data (71.36% on training data) -- runs in about 60 sec
                'clf__estimator': [SVC(random_state=637)],
                'tfidf__ngram_range': [(1, 1), (1, 2)],
                'tfidf__norm': ['l1', 'l2'],
                'clf__estimator__kernel': ['rbf', 'linear', 'sigmoid'],
            },
            {  # For Naive Bayes, the best accuracy was 68.30% on the test data (70.12% on training data) -- runs in about 5.1 sec
                'clf__estimator': [MultinomialNB()],
                'tfidf__ngram_range': [(1, 1), (1, 2)],
                'tfidf__norm': ['l1', 'l2'],
                'clf__estimator__fit_prior': [True, False],
                'clf__estimator__alpha': np.arange(0.1, 1.5, 16)
            },
            {  # For SGD, the best accuracy was 72.15% on the test data (72.74% on training data) -- runs in about 34.3 sec
                'clf__estimator': [SGDClassifier(random_state=637, n_jobs=-1)],
                'tfidf__ngram_range': [(1, 1), (1, 2)],
                'tfidf__norm': ['l1', 'l2'],
                'clf__estimator__loss': ['log', 'modified_huber'],
                'clf__estimator__penalty': ['l1', 'l2', 'elasticnet']
            },
            {  # For KNN, the best accuracy was 62.96% on the test data (64.25% on training data) -- runs in about 35.3 sec
                'clf__estimator': [KNeighborsClassifier()],
                'tfidf__ngram_range': [(1, 1), (1, 2)],
                'tfidf__norm': ['l1', 'l2'],
                'clf__estimator__leaf_size': [10, 30, 50],
                'clf__estimator__n_neighbors': [1, 5, 10, 20]
            },
            {  # For Random Forests, the best accuracy was 68.30% on the test data (69.13% on training data) -- runs in about 1.7 min (102 sec)
                'clf__estimator': [RandomForestClassifier(random_state=637, n_jobs=-1)],
                'tfidf__ngram_range': [(1, 1)],
                'tfidf__norm': ['l1', 'l2'],
                'clf__estimator__criterion': ['gini', 'entropy'],
                'clf__estimator__min_samples_leaf': [1, 5],
                'clf__estimator__max_depth': [5, 25, None]
            },
            {  # For Perceptron, the best accuracy was 69.93% on the test data (69.87% on training data) -- runs in about 11.2 sec
                'clf__estimator': [Perceptron(random_state=637, n_jobs=-1)],
                'tfidf__ngram_range': [(1, 1), (1, 2)],
                'tfidf__norm': ['l1', 'l2'],
                'clf__estimator__penalty': ['l1', 'l2', 'elasticnet']
            },
            {  # For Logistic Regression, the best accuracy was 69.48% on the test data (70.12% on training data) -- runs in about 14.1 sec
                'clf__estimator': [LogisticRegression(random_state=637, n_jobs=-1)],
                'tfidf__ngram_range': [(1, 1), (1, 2)],
                'tfidf__norm': ['l1', 'l2'],
                'clf__estimator__C': np.arange(0.5, 1.5, 11)
            }]

        param_dict = {'SVM': 0,
                      'Naive Bayes': 1,
                      'SGD': 2,
                      'KNN': 3,
                      'Random Forest': 4,
                      'Perceptron': 5,
                      'Logistic Regression': 6}

        if classifier != 'all':
            parameters = parameters[param_dict[classifier]]
        else:
            pass

        # do 10-fold cross validation for each of the combinations of the above params
        self.grid = GridSearchCV(
            pipeline, cv=cv, param_grid=parameters, n_jobs=-1, verbose=1)
        self.grid.fit(X, y)

        # summarize results
        print("\nBest Model: {0:.2%} using {1}".format(
            self.grid.best_score_, self.grid.best_params_))
        print('\n')
        self.compile_results(X, y)

    def compile_results(self, X, y):
        self.means = self.grid.cv_results_['mean_test_score']
        self.stds = self.grid.cv_results_['std_test_score']
        self.params = self.grid.cv_results_['params']

        # Define the estimator tested
        estimators = {SVC: 'SVC',
                      MultinomialNB: 'Naive Bayes',
                      SGDClassifier: 'SGD',
                      KNeighborsClassifier: 'KNN',
                      RandomForestClassifier: 'Random Forest',
                      Perceptron: 'Perceptron',
                      LogisticRegression: 'Logistic Regression'}

        # Organize the estimator performance into a data frame
        data = {'Estimator': [estimators[type(e['clf__estimator'])] for e in self.params],
                'score': self.means,
                'ngram_range': [e['tfidf__ngram_range'] for e in self.params],
                'tfidf__norm': [e['tfidf__norm'] for e in self.params],
                'computing_time': self.grid.cv_results_['mean_fit_time'],
                'estimator_obj': [e['clf__estimator'] for e in self.params]}

        self.all_results = pd.DataFrame(data=data)

        # Get the best performing model for each estimator
        idx = self.all_results.groupby(['Estimator'])['score'].transform(
            max) == self.all_results['score']
        self.results = self.all_results[idx]
        idx = self.results.groupby(['Estimator'])['computing_time'].transform(
            max) == self.results['computing_time']
        self.results = self.results[idx].set_index('Estimator')

    def set_uncertainty(self, X, y):
        # Find the standard error on aggregate sentiment scores
        print('Calculating uncertainty for aggregate sentiment scores...')
        self.agg_errs, self.agg_true_means, self.agg_pred_means = self.agg_sent_score(X, y,
                                                                                      n_bootstraps=1000,
                                                                                      bootstrap_size=1000,
                                                                                      verbose=True)
        # Mean average error in aggregated sentiment scores
        self.agg_me = self.agg_errs.mean()
        # Uncertainty in aggregated sentiment scores (95% confidence)
        self.agg_unc = model.agg_errs.std()*2
        print('Done! Aggregate sentiment uncertainty = {0:.4f}'.format(
            self.agg_unc))

    def print_all_results(self):
        for mean, stdev, param in zip(self.means, self.stds, self.params):
            param = param.copy()
            del param['clf__estimator']
            print("Mean: %f Stdev:(%f) with: %r" % (mean, stdev, param))

    def score(self, X, y, verbose=False):
        return self.grid.score(X, y)

    def predict(self, X, vebose=False):
        return self.grid.predict(X)

    def predict_proba(self, X):
        return self.grid.predict_proba(X)

    def predict_agg(self, X, verbose=False):
        agg_sent = ((self.grid.predict(X) - 2) / 2).mean()
        agg_unc = self.agg_unc * np.sqrt(1000 / len(X))
        if verbose:
            print(
                '(scale from -1 to 1) Aggregated sentiment score: {0:.2f} \u00B1 {1:.2f}\n'.format(agg_sent, agg_unc))
        return agg_sent, self.agg_unc

    def classification_report(self, X, y):
        y_preds = self.predict(X)
        print(classification_report(y, y_preds))

    def confusion_matrix(self, X, y):
        y_preds = self.predict(X)
        print('\nconfusion matrix: \n', confusion_matrix(y, y_preds), '\n')

    def estimator_performance(self, metric='score', ylim=(0.6, 0.75)):
        # Plot the performance
        fig, ax = plt.subplots(figsize=(7, 5))
        self.results.sort_values(by=metric, ascending=False).plot.bar(
            y=metric, ax=ax, rot=45, legend=False)
        ax.set_ylim(ylim)
        ax.set_title('Model Performance for Each Estimator',
                     fontsize='x-large')
        ax.set_xlabel('Estimator Type', fontsize='x-large')

        if metric == 'score':
            ax.set_ylabel('Max model accuracy', fontsize='x-large')
        elif metric == 'computing_time':
            ax.set_ylabel('Mean time to fit model (s)', fontsize='x-large')
        else:
            pass
        fig.show()
        return fig

    def sentiment_performance(self, X, y, ylim=0.5):
        # Get results
        report = classification_report(y, self.predict(X), output_dict=True)
        neg_results = list(report['0'].values())[:3]
        neu_results = list(report['2'].values())[:3]
        pos_results = list(report['4'].values())[:3]

        # Set position of bar on X axis
        barWidth = 0.25
        x1 = np.arange(len(neg_results))
        x2 = [x + barWidth for x in x1]
        x3 = [x + barWidth for x in x2]

        # Plot the performance
        fig, ax = plt.subplots(figsize=(7, 5))

        # Make the plot
        ax.bar(x1, neg_results, color='indianred', width=barWidth,
               edgecolor='white', label='Negative')
        ax.bar(x2, neu_results, color='sandybrown',
               width=barWidth, edgecolor='white', label='Neutral')
        ax.bar(x3, pos_results, color='mediumseagreen',
               width=barWidth, edgecolor='white', label='Postiive')
        ax.set_xticks(x2)
        ax.set_xticklabels(
            ('Precision', 'Recall', 'F1 Score'), fontsize='x-large')
        ax.set_ylim(0, 1)
        ax.set_title(
            'Best Estimator Performance on Different Sentiments', fontsize='x-large')

        ax.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
        fig.show()
        return report

    def plot_roc(self, X_test, y_test):
        y_score = self.predict_proba(X_test)

        # Reshape y_test
        ytest = []
        for i in y_test:
            if i == 0:
                ytest.append([1, 0, 0])
            elif i == 2:
                ytest.append([0, 1, 0])
            else:
                ytest.append([0, 0, 1])
        y_test = np.array(ytest)

        # Compute ROC curve and ROC area for each class
        fpr = dict()
        tpr = dict()
        roc_auc = dict()
        for i in range(3):
            fpr[i], tpr[i], _ = roc_curve(y_test[:, i], y_score[:, i])
            roc_auc[i] = auc(fpr[i], tpr[i])

        # Compute micro-average ROC curve and ROC area
        fpr["micro"], tpr["micro"], _ = roc_curve(
            y_test.ravel(), y_score.ravel())
        roc_auc["micro"] = auc(fpr["micro"], tpr["micro"])

        fig, ax = plt.subplots(figsize=(7, 7))
        for i, title in enumerate(['Negative', 'Neutral', 'Positive']):
            ax.plot(fpr[i], tpr[i], label=title +
                    ' tweets (AUC = %0.2f)' % roc_auc[i])
        ax.plot([0, 1], [0, 1], color='black', linestyle='--')
        ax.set_xlim([0.0, 1.0])
        ax.set_ylim([0.0, 1.0])
        ax.set_xlabel('False Negative Rate', fontsize='x-large')
        ax.set_ylabel('True Positive Rate', fontsize='x-large')
        ax.set_title('ROC Curve of Each Sentiment', fontsize='xx-large')
        ax.legend(loc="lower right")
        fig.show()
        return fig

    def agg_sent_score(self, X, y, n_bootstraps=1000, bootstrap_size=1000, verbose=False):
        np.random.seed(637)
        true_means, pred_means, errs = np.ones(n_bootstraps), np.ones(
            n_bootstraps), np.ones(n_bootstraps)
        for i in range(n_bootstraps):
            if verbose:
                if not (i+1) % (n_bootstraps//5):
                    print('{0:.0f}% done'.format((i+1)/(n_bootstraps//100)))
            ind = np.random.randint(0, len(X), int(bootstrap_size))
            X_boot = X[ind]
            y_boot = y[ind]
            y_pred = self.grid.predict(X_boot)

            # Standardize predictions to a -1 to 1 scale
            y_boot = (y_boot - 2) / 2
            y_pred = (y_pred - 2) / 2

            true_means.put(i, y_pred.mean())
            pred_means.put(i, y_boot.mean())
            errs.put(i, y_boot.mean() - y_pred.mean())

        self.mean_agg_error = errs.mean()
        return errs, true_means, pred_means

    def agg_sent_hist(self, X, y, n_bootstraps=1000, bootstrap_size=1000, verbose=False):
        errs, true_means, pred_means = self.agg_sent_score(
            X, y, n_bootstraps, bootstrap_size, verbose)
        fig, ax = plt.subplots(figsize=(7, 7))
        ax.hist(errs)
        plt.axvline(errs.mean(), color='k', linestyle='dashed')
        ax.set_xlabel('Aggregated Sentiment Error', fontsize='xx-large')
        ax.set_title('Sentiment Score Prediction Error', fontsize='xx-large')
        fig.show()
        return fig

    def agg_sent_plot(self, X, y, n_bootstraps=1000, bootstrap_size=1000, verbose=False):
        errs, true_means, pred_means = self.agg_sent_score(
            X, y, n_bootstraps, bootstrap_size, verbose)
        fig, ax = plt.subplots(figsize=(7, 7))
        ax.scatter(true_means, pred_means)
        ax.plot(true_means, true_means, color='red')
        ax.set_ylabel('Predicted Sentiment Score', fontsize='xx-large')
        ax.set_xlabel('Actual Sentiment Score', fontsize='xx-large')
        fig.show()
        return fig

    def word_cloud(self, tweets, labels=None, sentiment=None, showfig=True, mask=None, ngrams_range=(1, 2)):
        sent_dict = {'negative': 0,
                     'neutral': 2,
                     'positive': 4}

        tweets = [preprocessTweets(tweet) for tweet in tweets]
        if labels is None:
            labels = self.predict(tweets)

        # Get desired tweets
        if sentiment:
            tweets = [tweets[i]
                      for i in np.where(labels == sent_dict[sentiment])[0]]

        # Get vocabulary of tweets
        tfidf = TfidfVectorizer(lowercase=True,
                                strip_accents='ascii',
                                stop_words='english',
                                ngram_range=ngrams_range)
        tfidf.fit(tweets)

        vocabulary = tfidf.vocabulary_
        weights = tfidf.idf_
        weight_dict = {v: w for v, w, in zip(vocabulary, weights)}

        # Create Word Cloud
        word_cloud = WordCloud(width=2000,
                               height=1000,
                               max_font_size=200,
                               background_color="white",
                               max_words=100,
                               mask=mask,
                               contour_width=1,
                               stopwords=STOPWORDS.add('https'))
        word_cloud.generate_from_frequencies(weight_dict)

        # Plot the Word Cloud
        fig = plt.figure(figsize=(10, 10))
        plt.imshow(word_cloud, interpolation="hermite")
        plt.axis("off")
        if showfig:
            fig.show()
        return fig


def getTweets(twitter_api, search_term, num_tweets=1000, rts=False, date=None):
    if not rts:
        search_term += '-filter:retweets'       # Exclude retweets from search

    all_tweets = []
    idset = {}
    max_id = None
    while len(idset) < num_tweets:
        if date is not None:                            # Get tweets at or before a certain date
            fetched_tweets = twitter_api.search_tweets(
                q=search_term, count=num_tweets, lang='en', until=date, max_id=max_id, result_type='recent')
            if not fetched_tweets:                  # If certain date was more than a week ago
                fetched_tweets = twitter_api.search_tweets(
                    q=search_term, count=num_tweets, lang='en', max_id=max_id, result_type='recent')
        else:                                       # Get most recent tweets
            fetched_tweets = twitter_api.search_tweets(
                q=search_term, count=num_tweets, lang='en', max_id=max_id, result_type='recent')

        idlist = [status.id for status in fetched_tweets]
        idset = set(list(idset) + idlist)
        max_id = min(idset)
        all_tweets += list(fetched_tweets)

    print("Fetched {0} tweets about {1}".format(len(all_tweets), search_term))
    return [status.text for status in all_tweets]
