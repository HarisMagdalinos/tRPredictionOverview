"""
This code is used to train retention time predictors and store
predictions from a CV procedure for further analysis.

Library versions:

Python 2.7.13
xgboost.__version__ = '0.6'
sklearn.__version__ = '0.19.0'
scipy.__version__ = '0.19.1'
numpy.__version__ = '1.13.3'
pandas.__version__ = '0.20.3'

This project was made possible by MASSTRPLAN. MASSTRPLAN received funding 
from the Marie Sklodowska-Curie EU Framework for Research and Innovation 
Horizon 2020, under Grant Agreement No. 675132.
"""

__author__ = "Robbin Bouwmeester"
__copyright__ = "Copyright 2017"
__credits__ = ["Robbin Bouwmeester","Prof. Lennart Martens","Sven Degroeve"]
__license__ = "Apache License, Version 2.0"
__version__ = "1.0"
__maintainer__ = "Robbin Bouwmeester"
__email__ = "Robbin.bouwmeester@ugent.be"

# Native imports
import pickle

# Machine learning imports
from sklearn.cross_validation import cross_val_predict
from sklearn.metrics import mean_absolute_error
from sklearn.cross_validation import KFold
from sklearn.preprocessing import maxabs_scale
from sklearn.base import clone
from sklearn.grid_search import RandomizedSearchCV

from sklearn.linear_model import Lasso
from sklearn.ensemble import AdaBoostRegressor
from sklearn.svm import SVR
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ARDRegression
from sklearn.linear_model import BayesianRidge
from sklearn.neural_network import MLPRegressor

import xgboost as xgb

# Data analysis imports
from scipy.stats import randint
from scipy.stats import uniform
from scipy.stats import expon
from numpy import logspace
import numpy as np

import pandas as pd

class RandIntMatrix(object):
    def __init__(self, low, high, shape=(1)):
        self.low = low
        self.high = high
        self.shape = shape

    def rvs(self, random_state=None):
        np.random.seed(random_state)
        return np.random.randint(self.low, self.high, self.shape)


def train_model(X,y,params,model,scale=False,nfolds=10,n_jobs=8,cv = None,n_params=100):
    """
    Function that trains a regression model

    Parameters
    ----------
    X : pandas DF
        feature matrix
    y : pandas series
        target values to predict
        
    Returns
    -------
    object
        object that contains the trained regression model
    preds
        list of cv predictions
    """
    
    # Do we need to scale the feature?
    if scale: X = maxabs_scale(X)
    else: X = X.apply(lambda x: pd.to_numeric(x, errors='coerce'))
    
    # Make sure we make a hardcopy; so that it is just not a reference between crossv_mod and ret_mod
    crossv_mod = clone(model)
    ret_mod = clone(model)

    grid = RandomizedSearchCV(model, params,cv=cv,scoring='mean_absolute_error',verbose=0,n_jobs=n_jobs,n_iter=n_params,refit=False)
    grid.fit(X,y)
    print "Parameters chosen:"
    print grid.best_params_
    print "Best score:"
    print grid.best_score_

    # Use the same parameters for the training set to get CV predictions
    cv_pred = cv
    crossv_mod.set_params(**grid.best_params_)
    preds = cross_val_predict(crossv_mod, X=X, y=y, cv=cv_pred, n_jobs=n_jobs, verbose=0)

    # Train the final model
    ret_mod.set_params(**grid.best_params_)
    ret_mod.fit(X,y)

    return(ret_mod,preds)

def train_func(sets,
                  names=["Cake.lie","Cake.lie1","Cake.lie2","Cake.lie3","Cake.lie4","Cake.lie5","Cake.lie6","Cake.lie7"],
                  adds=["","","","","","","",""],
                  nfolds=10, cv = None,n_params=100,debug=True):
    """
    Function that trains seven different regression models

    Parameters
    ----------
    sets : pandas DF
        feature matrix also including the columns "time", "IDENTIFIER" and "system"
    names : list
        strings with additive names
    nfolds : int
        number of folds used for hyper parameter optimization
    cv : object
        sklearn cv object to use for the hyper parameter optimization
    n_params : int
        number of parameters to try
    debug : boolean
        print some extra information while training
        
    Returns
    -------
    pandas DF
        predictions from the CV
    """
    
    ret_preds = []

    model = MLPRegressor()

    hls = list(zip(np.random.random_integers(20, 200, 100),np.random.random_integers(1, 1, 100)))

    params = {
	    "alpha" : logspace(-6.0,-2.0),
	    #"activation" : ["identity"],
	    "solver" : ["lbfgs"],
	    #"hidden_layer_sizes" : hls,
	    "max_iter" : randint(25,100),
	    "learning_rate" : ["adaptive"],
	    "hidden_layer_sizes" : randint(5,100)
	}

    if debug: print("Training mlp...")

    model,preds = train_model(sets.drop(["time","IDENTIFIER","system"],axis=1, errors='ignore'),
                                             sets["time"],params,model,
                                             n_jobs=8,cv = cv,n_params=n_params)

    if debug: print("Done training mlp...")
    
    outfile = open("preds/%s_mlp%s.txt" % (names[6],adds[6]),"w")
    for val in zip(list(sets["IDENTIFIER"]),list(sets["time"]),preds):
        outfile.write("%s,%s,%s\n" % val)
    outfile.close()


    with open('mods/%s_mlp_orig%s.pickle' % (names[6],adds[6]), "w") as f: 
           pickle.dump(model, f)

    ret_preds.append(preds)
    
    model = MLPRegressor()

    hls = list(zip(np.random.random_integers(5, 50, 100),np.random.random_integers(2, 2, 100)))

    params = {
	    "alpha" : logspace(-6.0,-2.0),
	    #"activation" : ["identity"],
	    "solver" : ["lbfgs"],
	    "hidden_layer_sizes" : hls,
	    "max_iter" : randint(25,100),
	    "learning_rate" : ["adaptive"],
	}

    if debug: print("Training mlp...")

    model,preds = train_model(sets.drop(["time","IDENTIFIER","system"],axis=1, errors='ignore'),
                                             sets["time"],params,model,
                                             n_jobs=8,cv = cv,n_params=n_params)

    if debug: print("Done training mlp...")
    
    outfile = open("preds/%s_mlp_deep%s.txt" % (names[6],adds[6]),"w")
    for val in zip(list(sets["IDENTIFIER"]),list(sets["time"]),preds):
        outfile.write("%s,%s,%s\n" % val)
    outfile.close()


    with open('mods/%s_mlp_deep%s.pickle' % (names[6],adds[6]), "w") as f: 
           pickle.dump(model, f)

    ret_preds.append(preds)
    
    model = MLPRegressor()

    hls = list(zip(np.random.random_integers(5, 50, 100),np.random.random_integers(5, 5, 100)))

    params = {
	    "alpha" : logspace(-6.0,-2.0),
	    #"activation" : ["identity"],
	    "solver" : ["lbfgs"],
	    "hidden_layer_sizes" : hls,
	    "max_iter" : randint(25,100),
	    "learning_rate" : ["adaptive"],
	}

    if debug: print("Training mlp...")

    model,preds = train_model(sets.drop(["time","IDENTIFIER","system"],axis=1, errors='ignore'),
                                             sets["time"],params,model,
                                             n_jobs=8,cv = cv,n_params=n_params)

    if debug: print("Done training mlp...")
    
    outfile = open("preds/%s_mlp_deeper%s.txt" % (names[6],adds[6]),"w")
    for val in zip(list(sets["IDENTIFIER"]),list(sets["time"]),preds):
        outfile.write("%s,%s,%s\n" % val)
    outfile.close()


    with open('mods/%s_mlp_deeper%s.pickle' % (names[6],adds[6]), "w") as f: 
           pickle.dump(model, f)

    ret_preds.append(preds)

    ret_preds = pd.DataFrame(ret_preds).transpose()
    
    ret_preds.columns = [
                 "%s_MLP_orig%s" % (names[0],adds[0]),
                 "%s_MLP_deep%s"  % (names[1],adds[1]),
                 "%s_MLP_deeper%s"  % (names[2],adds[2])]


    return(ret_preds)