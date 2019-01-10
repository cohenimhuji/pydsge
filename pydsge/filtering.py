#!/bin/python2
# -*- coding: utf-8 -*-

import numpy as np
from .stuff import *
import pydsge
# from econsieve import UnscentedKalmanFilter as UKF
# from econsieve import ScaledSigmaPoints as SSP
from econsieve import EnKF
from econsieve.stats import logpdf
from scipy.optimize import minimize as so_minimize

def create_obs_cov(self, scale_obs = 0.1):

    if not hasattr(self, 'Z'):
        warnings.warn('No time series of observables provided')
    else:
        sig_obs 	= np.var(self.Z, axis = 0)*scale_obs

        self.obs_cov   = np.diagflat(sig_obs)


def create_filter(self, P = None, R = None, N = None):

    np.random.seed(0)

    if not hasattr(self, 'Z'):
        warnings.warn('No time series of observables provided')

    if N is None:
        N   = 5*len(self.vv)

    enkf    = EnKF(N, model_obj = self)

    if P is not None:
        enkf.P 		= P
    else:
        enkf.P 		*= 1e1

    if R is not None:
        enkf.R 		= R
    elif hasattr(self, 'obs_cov'):
        enkf.R 		= self.obs_cov

    CO          = self.SIG @ self.QQ(self.par)

    enkf.Q 		= CO @ CO.T

    self.enkf    = enkf


def get_ll(self, info=False):

    if info == 1:
        st  = time.time()

    ll     = self.enkf.batch_filter(self.Z, calc_ll = True, info=info)[2]

    self.ll     = ll

    if info == 1:
        print('Filtering ll done in '+str(np.round(time.time()-st,3))+'seconds.')

    return self.ll


def run_filter(self, use_rts=True, info=False):

    if info == 1:
        st  = time.time()

    X1, cov, ll     = self.enkf.batch_filter(self.Z, store=use_rts, info=info)

    if use_rts:
        X1, cov     = self.enkf.rts_smoother(X1, cov)

    if info == 1:
        print('Filtering done in '+str(np.round(time.time()-st,3))+'seconds.')

    self.filtered_X      = X1
    self.filtered_cov    = cov
    
    return X1, cov


def extract(self, pmean = None, cov = None, method = None, converged_only = False, info = True):

    if pmean is None:
        pmean   = self.filtered_X

    if cov is None:
        cov = self.filtered_cov

    means, cov, res     = self.enkf.ipa(pmean, cov, method, converged_only, info)

    self.res            = res

    return means, cov, res
