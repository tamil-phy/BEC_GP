import numpy as np
import trottersuzuki as ts
import math
import pickle
import os

from matplotlib import pyplot as plt
from tqdm import tqdm

from neuralbec import utils

logger = utils.get_logger(__name__)


def harmonic_potential(x, y):
  """ Harmonic Potential

      ( x^2 + y^2 ) / 2
  """
  return 0.5 * (x**2 + y**2)


def custom_potential_1(x, y):
  """ Custom Potential

      0.5x^2 + 24cos^2(x)
  """
  return 0.5 * (x**2) + 24 * (math.cos(x) ** 2)


def generate_varg(fn, num_samples, filename, g_low=0, g_high=500):
  """Create dataset based on data generated by `fn` by varying `g`

  Parameters
  ----------
  fn : function
    Data (Particle Density) generating function

  Returns
  -------
  dict
    A dictionary of datapoints and reference points

  """
  datapoints = []
  for g in tqdm(np.random.uniform(g_low, g_high, num_samples)):
    # generate particle density
    ref, psi = fn(g)
    datapoints.append((g, psi))
  datadict = ref
  datadict['data'] = datapoints
  # write to disk
  save(datadict, filename)
  return datadict


def particle_density_BEC1D(dim, radius, angular_momentum, time_step,
  coupling, iterations):
  """Estimate Particle Density of 1-dimensional BEC system

  Parameters
  ----------
  dim : int
    dimensions of lattice
  radius : float
    physical radius
  angular_momentum : float
    quantum number
  time_step : float
    time steps
  coupling : float
    coupling strength (g)
  iterations : int
    number of iterations of trotter-suzuki

  Returns
  -------
  dict, numpy.ndarray
    reference points, particle density of evolved system
  """
  # Set up lattice
  grid = ts.Lattice1D(dim, radius, False, "cartesian")
  # initialize state
  state = ts.State(grid, angular_momentum)
  state.init_state(lambda r : 1. / np.sqrt(radius))  # constant state
  # init potential
  potential = ts.Potential(grid)
  potential.init_potential(harmonic_potential)  # harmonic potential
  # build hamiltonian with coupling strength `g`
  hamiltonian = ts.Hamiltonian(grid, potential, 1., coupling)
  # setup solver
  solver = ts.Solver(grid, state, hamiltonian, time_step)
  # Evolve the system
  solver.evolve(iterations, True)
  # Compare the calculated wave functions w.r.t. groundstate function
  psi = np.sqrt(state.get_particle_density()[0])
  # psi / psi_max
  psi = psi / max(psi)

  return { 'x' : grid.get_x_axis()}, psi


def plot_wave_function(x, psi, fontsize=16, title=None, save_to=None):
  """ Plot Wave Function """
  # set title
  if title:
    plt.title(title)
  # settings
  plt.plot(x, psi, 'o', markersize=3)
  plt.xlabel('x', fontsize=fontsize)
  plt.ylabel(r'$\psi$', fontsize=fontsize)
  # save figure
  if save_to:
    plt.savefig(save_to)
    logger.info('Figure saved to {}'.format(save_to))
  # disply image
  plt.show()


def load(name, path='data/'):
  datadump = pickle.load(open('{}/{}.data'.format(path, name), 'rb'))
  inputs = [ g for g, density in datadump['data'] ]
  outputs = [ density for g, density in datadump['data'] ]
  reference = { 'x' : datadump['x'] }
  return inputs, outputs, reference


def save(datadict, name, path='data/'):
  """Save Data Dictionary to disk

  Parameters
  ----------
  datadict : dict
    data dictionary { 'x' : [ ... ], 'data' : [ (.., ..), .. ] }
  name : str
    file name to save data
  path : str
    path to file
  """
  filename = os.path.join(path, name)
  pickle.dump(datadict, open(filename, 'wb'))
  logger.info('Saved to {}'.format(filename))
