#!/bin/python
# -*- coding: utf-8 -*-

import numpy as np
from .stuff import *
from econsieve import TEnKF, KalmanFilter, ipas
from econsieve.stats import logpdf


def create_obs_cov(self, scale_obs=0.1):

    if not hasattr(self, 'Z'):
        raise LookupError('No time series of observables provided')
    else:
        sig_obs = np.var(self.Z, axis=0)*scale_obs**2

        obs_cov = np.diagflat(sig_obs)

    return obs_cov


def create_filter(self, P=None, R=None, N=None, linear=False, random_seed=None):

    if N is None:
        N = 500

    if linear:
        self.linear_filter = True
    else:
        self.linear_filter = False

    if not hasattr(self, 'data'):
        warnings.warn('No time series of observables provided')
    else:
        self.Z = np.array(self.data)

    if random_seed is not None:
        np.random.seed(random_seed)

    if linear:
        f = KalmanFilter(dim_x=len(self.vv), dim_z=self.ny)
        f.F = self.linear_representation()
        f.H = self.hx
    else:
        f = TEnKF(N=N, dim_x=len(self.vv), dim_z=self.ny,
                  fx=self.t_func, hx=self.o_func, model_obj=self)

    if P is not None:
        f.P = P
    elif hasattr(self, 'P'):
        f.P = self.P
    else:
        f.P *= 1e1
    f.init_P = f.P

    if R is not None:
        f.R = R

    f.eps_cov = self.QQ(self.par)

    CO = self.SIG @ f.eps_cov

    f.Q = CO @ CO.T

    self.filter = f

    return f


def get_ll(self, verbose=False):

    if verbose:
        st = time.time()

    if self.linear_filter:
        ll = self.filter.batch_filter(self.Z)[2]
    else:
        ll = self.filter.batch_filter(self.Z, calc_ll=True, verbose=verbose)

    if np.isnan(ll):
        ll = -np.inf

    self.ll = ll

    if verbose:
        print('[get_ll:]'.ljust(15, ' ')+'Filtering done in %s seconds. Likelihood is %s.' %
              (np.round(time.time()-st, 3), ll))

    return self.ll


def run_filter(self, use_rts=True, rcond=1e-14, verbose=False):

    if verbose:
        st = time.time()

    if self.linear_filter:
        X1, cov, ll = self.filter.batch_filter(self.Z)

        if use_rts:
            X1, cov, _, _ = self.filter.rts_smoother(X1, cov)

    else:
        # set approximation level
        self.filter.fx = lambda x: self.t_func(x)

        X1, cov = self.filter.batch_filter(self.Z, store=use_rts, verbose=verbose)

        if use_rts:
            X1, cov = self.filter.rts_smoother(X1, cov, rcond=rcond)

    if verbose:
        print('[run_filter:]'.ljust(15, ' ')+'Filtering done in ' +
              str(np.round(time.time()-st, 3))+'seconds.')

    self.filtered_X = X1
    self.filtered_cov = cov

    return X1, cov


def extract(self, pmean=None, cov=None, method=None, penalty=50, return_flag=False, itype=(0, 1), presmoothing=None, min_options=None, show_warnings=True, verbose=True):

    self.filter.fx = lambda x, noise: self.t_func(x, noise)

    if pmean is None:
        pmean = self.filtered_X.copy()

    if cov is None:
        cov = self.filtered_cov.copy()

    T1 = self.linear_representation()
    T1, T2 = self.hx[0] @ T1, self.hx[0] @ T1 @ self.SIG
    T3 = self.hx[1]
    mod_objs = (T1, T2, T3), self.SIG

    means, cov, res, flag = ipas(self.filter, pmean, cov, method, penalty, show_warnings=show_warnings,
                                 itype=itype, presmoothing=presmoothing, objects=mod_objs, min_options=min_options, return_flag=True, verbose=verbose)

    self.res = res

    if return_flag:
        return means, cov, res, flag

    return means, cov, res
