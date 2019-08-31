#!/bin/python
# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
from .parser import DSGE
from .stats import summary
from .engine import preprocess
from .stuff import *
from .filtering import *
from .estimation import *
from .plots import *
from .processing import *

def write_yaml(self, filename):

    if filename[-5:] is not '.yaml':
        filename = filename + '.yaml'

    f = open(filename, "w+")

    f.write(self.raw_yaml)
    f.close()

    print("Model written to '%s.'" %filename)

    return 


def save_meta(self, filename=None):
    
    if filename is None:
        if 'dfile' in self.fdict.keys():
            filename = self.fdict['dfile']
        elif hasattr(self, 'path') and hasattr(self, 'name'):
            filename = self.path + self.name + '_meta'
        elif hasattr(self, 'path') and hasattr(self, 'mod_name'):
            filename = self.path + self.mod_name + '_meta'
        else:
            raise KeyError("'filename' must be given.")
    else:
        self.fdict['dfile'] = filename

    objs = 'description', 'data', 'backend_file', 'tune', 'name'

    for o in objs:
        if hasattr(self, o):
            exec('self.fdict[o] = self.'+str(o))

    if hasattr(self, 'filter'):
        self.fdict['filter_R'] = self.filter.R
        self.fdict['filter_P'] = self.filter.P

    np.savez(filename, **self.fdict)

    return


def set_path(self, path):

    import os

    if not path[-1] == os.sep:
        path = path + os.sep
    
    self.path = path

    return


def get_chain(self, backend_file=None):
    
    if backend_file is None:

        if hasattr(self, 'sampler'):
            return self.sampler.get_chain()

        else:
            if hasattr(self, 'backend_file'):
                backend_file = self.backend_file
            elif 'backend_file' in self.fdict.keys():
                backend_file = str(self.fdict['backend_file'])
            else:
                raise NameError("Neither a backend nor a sampler could be found.")

    reader = emcee.backends.HDFBackend(backend_file)

    return reader.get_chain()


def traceplot_m(self, **args):

    if hasattr(self, 'tune'):
        tune = self.tune
    else:
        tune = self.fdict['tune']

    return traceplot(self.get_chain(), varnames=self.fdict['prior_names'], tune=tune, priors=self.fdict['frozen_priors'], **args)


def posteriorplot_m(self, **args):

    if hasattr(self, 'tune'):
        tune = self.tune
    else:
        tune = self.fdict['tune']

    return posteriorplot(self.get_chain(), varnames=self.fdict['prior_names'], tune=tune, **args)


def summary_m(self, **args):

    if hasattr(self, 'tune'):
        tune = self.tune
    else:
        tune = self.fdict['tune']

    return summary(self.get_chain(), tune, self['__data__']['estimation']['prior'])

def info_m(self, **args):

    if hasattr(self, 'tune'):
        tune = self.tune
    else:
        tune = self.fdict['tune']

    if hasattr(self, 'name'):
        name = self.name
    else:
        name = self.fdict['name']

    if hasattr(self, 'description'):
        description = self.description
    else:
        description = self.fdict['description']

    cshp = self.get_chain().shape

    info_str = 'Title: %s (description: %s). Last %s of %s samples in %s chains with %s parameters.' %(name, description, cshp[0] - tune, cshp[0], cshp[1], cshp[2])

    return info_str

def get_data(self, csv_file, sep=None, start=None, end=None):

    if csv_file[-4:] != '.csv':
        raise TypeError('data format must be `.csv`.')

    d0 = pd.read_csv(csv_file, sep=sep).dropna()

    for o in self['observables']:
        if str(o) not in d0.keys():
            raise KeyError('%s is not in the data!' %o)

    dates = pd.date_range(str(int(d0['year'][0])), periods=d0.shape[0], freq='Q')

    d0.index = dates

    self.obs = [str(o) for o in self['observables']]
    d1 = d0[self.obs]

    if start is not None:
        start = str(start)

    if end is not None:
        end = str(end)

    d2 = d1.loc[start:end]

    self.data = d2
    self.fdict['data'] = d2
    self.fdict['obs'] = self.obs

    return d2

DSGE.t_func = t_func
DSGE.set_path = set_path
DSGE.linear_representation = linear_representation
DSGE.o_func = o_func
DSGE.get_sys = get_sys
DSGE.irfs = irfs
DSGE.simulate = simulate
DSGE.simulate_series = simulate_series
DSGE.create_filter = create_filter
DSGE.run_filter = run_filter
DSGE.get_ll = get_ll
DSGE.get_iv = get_iv
DSGE.prep_estim = prep_estim
DSGE.bay_estim = bay_estim
DSGE.pmdm = pmdm
DSGE.epstract = epstract
DSGE.sampled_sim = sampled_sim
DSGE.sampled_irfs = sampled_irfs
DSGE.extract = extract
DSGE.create_obs_cov = create_obs_cov
DSGE.posterior_sample = posterior_sample
DSGE.preprocess = preprocess
DSGE.mask = mask
DSGE.save = save_meta
DSGE.get_chain = get_chain
DSGE.traceplot = traceplot_m
DSGE.posteriorplot = posteriorplot_m
DSGE.summary = summary_m
DSGE.info = info_m
DSGE.get_data = get_data

## old stuff, left to be integrated
"""
def chain_masker(self):
    iss = np.zeros(len(self.prior_names), dtype=bool)
    for v in self.prior_names:
        iss = iss | (self.prior_names == v)
    return iss

def means(self):
    x = self.par_fix

    x[self.prior_arg] = chain[self.tune:].mean(axis=(0, 1))
    return list(x)

def medians(self):
    x = self.par_fix
    x[self.prior_arg] = np.median(self.chain[self.tune:], axis=(0, 1))
    return list(x)

"""
