
#+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+//
#                                                                                                                                       //
# fractal.py                                                                                                                            //
#                                                                                                                                       //
# D. C. Groothuizen Dijkema - January, 2020                                                                                             //
#+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+//

# Helper function file to produce visualisations of fractals


# change is CUDA library dll has not been produced
CUDA_ENABLED=True

import ctypes as ct
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.colors import ListedColormap

from huygens.interf import c_matrix,c_vector,c_pointer

__all__=['sample_mandelbrot','plot_mandelbrot','sample_newton','sample_newton_cuda','plot_newton','plot_newton_roots'
  ,'plot_newton_iteration']

# load the lib
_libc=ct.cdll.LoadLibrary('./bin/fractal.dll')

# extract the functions
_sample_mandelbrot=getattr(_libc,'?sample_mandelbrot@@YAHPEAPEAHHHHHNNNN_N@Z')
_sample_newton=getattr(_libc,'?sample_newton@@YAHPEAPEAN0PEAPEAHPEANHHHHHNNNN_N@Z')
_assign_roots=getattr(_libc,'?assign_roots@@YAXQEAHQEBN111HHH@Z')

# assign arg and return types
_sample_mandelbrot.argtypes=[ct.POINTER(ct.POINTER(ct.c_int)),ct.c_int,ct.c_int,ct.c_int,ct.c_int,ct.c_double
  ,ct.c_double,ct.c_double,ct.c_double,ct.c_bool]
_sample_mandelbrot.restype=ct.c_int
_sample_newton.argtypes=[ct.POINTER(ct.POINTER(ct.c_double)),ct.POINTER(ct.POINTER(ct.c_double)),ct.POINTER(ct.POINTER(ct.c_int))
  ,ct.POINTER(ct.c_double),ct.c_int,ct.c_int,ct.c_int,ct.c_int,ct.c_int,ct.c_double,ct.c_double,ct.c_double,ct.c_double,ct.c_bool]
_sample_newton.restype=ct.c_int
_assign_roots.argtypes=[ct.POINTER(ct.c_int),ct.POINTER(ct.c_double),ct.POINTER(ct.c_double),ct.POINTER(ct.c_double)
    ,ct.POINTER(ct.c_double),ct.c_int,ct.c_int,ct.c_int]
_assign_roots.restype=None

if CUDA_ENABLED:
  # load the cuda lib
  _libc_cuda=ct.cdll.LoadLibrary('./bin/cufractal.dll')

  # extract the functions
  _sample_mandelbrot_cuda=getattr(_libc_cuda,'?sample_mandelbrot@@YAHQEAHHHHNNNN_N@Z')
  _sample_julia_cuda=getattr(_libc_cuda,'?sample_julia@@YAHQEAHNNHHHNNNN_N@Z')
  _sample_newton_cuda=getattr(_libc_cuda,'?sample_newton@@YAHQEAN0QEAHQEBNHHHHNNNN_N@Z')
  _assign_roots_cuda=getattr(_libc_cuda,'?assign_roots@@YAXQEAHQEBN111HHH@Z')

  # assign arg and return types
  _sample_mandelbrot_cuda.argtypes=[ct.POINTER(ct.c_int),ct.c_int,ct.c_int,ct.c_int,ct.c_double,ct.c_double,ct.c_double,ct.c_double
    ,ct.c_bool]
  _sample_mandelbrot_cuda.restype=ct.c_int
  _sample_julia_cuda.argtypes=[ct.POINTER(ct.c_int),ct.c_double,ct.c_double,ct.c_int,ct.c_int,ct.c_int,ct.c_double,ct.c_double,ct.c_double
    ,ct.c_double,ct.c_bool]
  _sample_julia_cuda.restype=ct.c_int
  _sample_newton_cuda.argtypes=[ct.POINTER(ct.c_double),ct.POINTER(ct.c_double),ct.POINTER(ct.c_int),ct.POINTER(ct.c_double),ct.c_int
    ,ct.c_int,ct.c_int,ct.c_int,ct.c_double,ct.c_double,ct.c_double,ct.c_double,ct.c_bool]
  _sample_newton_cuda.restype=ct.c_int
  _assign_roots_cuda.argtypes=[ct.POINTER(ct.c_int),ct.POINTER(ct.c_double),ct.POINTER(ct.c_double),ct.POINTER(ct.c_double)
    ,ct.POINTER(ct.c_double),ct.c_int,ct.c_int,ct.c_int]
  _assign_roots_cuda.restype=None

class CUDAWarning(Exception):
  '''
  An error to raise when a CUDA library doesn't exist
  '''
  pass

def plot_mandelbrot(iterations,limit,log=True,show_fig=False,save_fig=True,file_name='mandelbrot.pdf',fig_inches=(12,12),dpi=1200
  ,color_map=None):
  '''
  Produce a plot of the Mandelbrot Set, coloured by the number of iterations taken.
  
  Parameters
  ----------
  iterations : 2D numpy.ndarray
    - The number of iterations for a pixel to exceed the bound.
  limit : int
    - The value which represents the bound was not exceeded.
  log : bool, optional 
    - If the number of iterations should be logged.
  show_fig : bool, optional
    - If the visualisation should be shown.
  save_fig : bool, optional
    - If the visualisation should be saved.
  file_name : string, optional
    - The name of the output.
  fig_inches : tuple, optional
    - The size of the figure.
  dpi : int, optional
    - Plot resolution.
  color_map : matplotlib.colors.ListedColormap
    - The colours to use in the visualisation.

  '''
  _,ax=_plot_setup(fig_inches)

  if log:
    iterations=np.log(iterations)
    limit=np.log(limit)
  
  # black out where the limit could not be found (in the mandelbrot set)
  # and set color map
  masked_iterations=np.ma.masked_where(iterations==limit,iterations)
  if color_map is None:
    color_map=cm.Spectral_r
  color_map.set_bad(color='black')
  # produce the figure
  ax.imshow(masked_iterations,cmap=color_map)

  if show_fig:
    plt.show()
  if save_fig:
    plt.savefig(file_name,dpi=dpi)

def sample_mandelbrot(central_point,x_span,y_span,x_resolution,y_resolution,max_itr,num_threads=1,verbose=False):
  '''
  Produce a sample of the Mandelbrot Set.
  
  Parameters
  ----------
  central_point : 1D array-like
    - The centre of the area to visualise.
  x_span,y_span : int
    - The span across each axis, with half of the span on either side of the centre.
  x_resolution,y_resolution : int
    - The number of pizels to divide the x- and y-axes into.
  max_itr : int
    - The number of iterations to compute before considering a point to not converge.
  num_threads : int, optional
    - The number of threads to execute on.
  verbose : bool, optional.
    - For verbose output.

  Returns
  -------
  itr : 2D numpy.ndarray
    - The number of iterations for a pixel exceed the bound.
  limit : int
    - The value which represents the bound was not exceeded.

  '''
  # input setup
  startx=central_point[0]-x_span/2.
  starty=central_point[1]-y_span/2.
  endx=central_point[0]+x_span/2.
  endy=central_point[1]+y_span/2.
  # array to store the iteration count for each pixel
  tmp,act=c_matrix(ct.c_int,y_resolution,x_resolution)

  # call the library function
  limit=_sample_mandelbrot(
    tmp,ct.c_int(max_itr),ct.c_int(num_threads),ct.c_int(x_resolution),ct.c_int(y_resolution)
    ,ct.c_double(startx),ct.c_double(endx),ct.c_double(starty),ct.c_double(endy),ct.c_bool(verbose)
  )

  del tmp
  # flip the rows because [startx,stary] is stored in [0,0]
  return np.flipud(np.ctypeslib.as_array(act)),limit

def sample_mandelbrot_cuda(central_point,x_span,y_span,x_resolution,y_resolution,max_itr,verbose=False):
  '''
  Produce a sample of the Mandelbrot Set with CUDA acceleration.
  
  Parameters
  ----------
  central_point : 1D array-like
    - The centre of the area to visualise.
  x_span,y_span : int
    - The span across each axis, with half of the span on either side of the centre.
  x_resolution,y_resolution : int
    - The number of pizels to divide the x- and y-axes into.
  max_itr : int
    - The number of iterations to compute before considering a point to not converge.
  verbose : bool, optional.
    - For verbose output.

  Returns
  -------
  itr : 2D numpy.ndarray
    - The number of iterations for a pixel exceed the bound.
  limit : int
    - The value which represents the bound was not exceeded.

  '''
  if not CUDA_ENABLED: raise CUDAWarning('CUDA library has not been implemented.')
  # input setup
  startx=central_point[0]-x_span/2.
  starty=central_point[1]-y_span/2.
  endx=central_point[0]+x_span/2.
  endy=central_point[1]+y_span/2.
  # array to store the iteration count for each pixel
  itr=c_vector(ct.c_int,y_resolution*x_resolution)

  # call the library function
  limit=_sample_mandelbrot_cuda(
    itr,ct.c_int(max_itr),ct.c_int(x_resolution),ct.c_int(y_resolution)
    ,ct.c_double(startx),ct.c_double(endx),ct.c_double(starty),ct.c_double(endy),ct.c_bool(verbose)
  )

  # reshape into a 2D array and flip the rows because [startx,stary] is stored in [0,0]
  return np.flipud(np.reshape(np.ctypeslib.as_array(itr),(y_resolution,x_resolution))),limit

def sample_julia_cuda(c,central_point,x_span,y_span,x_resolution,y_resolution,max_itr,verbose=False):
  '''
  Produce a sample of the Julia set of a given complex number with CUDA acceleration.
  
  Parameters
  ----------
  c : complex
    - The complex number to find the julia set of.
  central_point : 1D array-like
    - The centre of the area to visualise.
  x_span,y_span : int
    - The span across each axis, with half of the span on either side of the centre.
  x_resolution,y_resolution : int
    - The number of pizels to divide the x- and y-axes into.
  max_itr : int
    - The number of iterations to compute before considering a point to not converge.
  verbose : bool, optional.
    - For verbose output.

  Returns
  -------
  itr : 2D numpy.ndarray
    - The number of iterations for a pixel exceed the bound.
  limit : int
    - The value which represents the bound was not exceeded.

  '''
  if not CUDA_ENABLED: raise CUDAWarning('CUDA library has not been implemented.')
  # input setup
  startx=central_point[0]-x_span/2.
  starty=central_point[1]-y_span/2.
  endx=central_point[0]+x_span/2.
  endy=central_point[1]+y_span/2.
  # array to store the iteration count for each pixel
  itr=c_vector(ct.c_int,y_resolution*x_resolution)

  # call the library function
  limit=_sample_julia_cuda(
    itr,ct.c_double(c.real),ct.c_double(c.imag),ct.c_int(max_itr),ct.c_int(x_resolution),ct.c_int(y_resolution)
    ,ct.c_double(startx),ct.c_double(endx),ct.c_double(starty),ct.c_double(endy),ct.c_bool(verbose)
  )

  # reshape into a 2D array and flip the rows because [startx,stary] is stored in [0,0]
  return np.flipud(np.reshape(np.ctypeslib.as_array(itr),(y_resolution,x_resolution))),limit


def plot_newton_roots(roots,show_fig=False,save_fig=True,file_name='newtons_fractal_roots.pdf',fig_inches=(12,12),dpi=1200
  ,color_map=None):
  '''
  Produce a plot of Newton's fractals, coloured by the root converged to.
  
  Parameters
  ----------
  roots : 2D numpy.ndarray
    - The approximation of the root which was found.
  show_fig : bool, optional
    - If the visualisation should be shown.
  save_fig : bool, optional
    - If the visualisation should be saved.
  file_name : string, optional
    - The name of the output.
  fig_inches : tuple, optional
    - The size of the figure.
  dpi : int, optional
    - Plot resolution.

  '''
  _,ax=_plot_setup(fig_inches)

  # black out where no root could be found and set color map
  masked_roots=np.ma.masked_where(roots==-1,roots)
  if color_map is None:
    color_map=cm.viridis
  color_map.set_bad(color='black')
  # produce the figure
  ax.imshow(masked_roots,cmap=color_map)

  if show_fig:
    plt.show()
  if save_fig:
    plt.savefig(file_name,dpi=dpi)

def plot_newton_iteration(iterations,limit,log=True,show_fig=False,save_fig=True,file_name='newtons_fractal_iterations.pdf'
  ,fig_inches=(12,12),dpi=1200,color_map=None):
  '''
  Produce a plot of Newton's fractals, coloured by the number of iterations taken.
  
  Parameters
  ----------
  iterations : 2D numpy.ndarray
    - The number of iterations for a pixel to converge to a root.
  limit : int
    - The value which represents no root was converged to.
  log : bool, optional 
    - If the number of iterations should be logged.
  show_fig : bool, optional
    - If the visualisation should be shown.
  save_fig : bool, optional
    - If the visualisation should be saved.
  file_name : string, optional
    - The name of the output.
  fig_inches : tuple, optional
    - The size of the figure.
  dpi : int, optional
    - Plot resolution.
  
  '''
  _,ax=_plot_setup(fig_inches)
  
  if log:
    iterations=np.log(iterations)
    limit=np.log(limit)

  # black out where no root could be found and set color map
  masked_iterations=np.ma.masked_where(iterations==limit,iterations)
  if color_map is None:
    color_map=cm.Spectral_r
  color_map.set_bad(color='black')
  # produce the figure
  ax.imshow(masked_iterations,cmap=color_map)

  if show_fig:
    plt.show()
  if save_fig:
    plt.savefig(file_name,dpi=dpi)

def plot_newton(roots,iterations,limit,colors,log=True,show_fig=False,save_fig=True,file_name='mandelbrot.pdf',fig_inches=(12,12),dpi=1200):
  '''
  Produce a plot of Newton's fractals, coloured by the root converged to and the number of iterations taken.
  
  Parameters
  ----------
  roots : 2D numpy.ndarray
    - The approximation of the root which was found.
  iterations : 2D numpy.ndarray
    - The number of iterations for a pixel to converge to a root.
  limit : int
    - The value which represents no root was converged to.
  colors : list
    - List of colour scales to use for each root.
  log : bool, optional 
    - If the number of iterations should be logged.
  show_fig : bool, optional
    - If the visualisation should be shown.
  save_fig : bool, optional
    - If the visualisation should be saved.
  file_name : string, optional
    - The name of the output.
  fig_inches : tuple, optional
    - The size of the figure.
  dpi : int, optional
    - Plot resolution.
  
  '''
  _,ax=_plot_setup(fig_inches)

  # find all unique roots by the index values, ignoring where no root was found
  unique_roots=np.unique(roots)
  unique_roots=np.delete(unique_roots,np.where(unique_roots==-1))

  if log:
    iterations=np.log(iterations)
    limit=np.log(limit)

  # mask where no roots could be found
  limit_bool=iterations!=limit
  # plot where no roots could be found as black
  no_root=np.ma.masked_array(iterations,limit_bool)
  ax.imshow(no_root,cmap=ListedColormap([0,0,0]))
  # for each root, mask it and plot it
  for itr,root in enumerate(unique_roots):
    masked_roots=np.ma.masked_array(iterations,roots!=root)
    ax.imshow(iterations*masked_roots,cmap=colors[itr])

  if show_fig:
    plt.show()
  if save_fig:
    plt.savefig(file_name,dpi=dpi)

def sample_newton(coeffs,central_point,x_span,y_span,x_resolution,y_resolution,max_itr,num_threads=1,verbose=False):
  '''
  Produce Newton's fractals for a given polynomial.
  
  Parameters
  ----------
  coeffs : 1D array-like
    - The coefficient of the polynomial, in order from lowest to highest degree.
  central_point : 1D array-like
    - The centre of the area to.
  x_span,y_span : int
    - The span across each axis, with half of the span on either side of the centre.
  x_resolution,y_resolution : int
    - The number of pizels to divide the x- and y-axes into.
  max_itr : int
    - The number of iterations to compute before considering a point to not converge.
  num_threads : int, optional
    - The number of threads to execute on.
  verbose : bool, optional
    - For verbose output.

  Returns
  -------
  roots : 2D numpy.ndarray
    - The approximation of the root which was found.
  ind : 2D numpy.ndarray
    - The root converged to.
  itr : 2D numpy.ndarray
    - The number of iterations for a pixel to converge to a root.
  limit : int
    - The value which represents no root was converged to.

  '''
  # input setup
  startx=central_point[0]-x_span/2.
  starty=central_point[1]-y_span/2.
  endx=central_point[0]+x_span/2.
  endy=central_point[1]+y_span/2.
  
  # arrays to store the real part of the root approached and the imaginary part of the root approached
  tmp_re,act_re=c_matrix(ct.c_double,y_resolution,x_resolution)
  tmp_im,act_im=c_matrix(ct.c_double,y_resolution,x_resolution)
  # array to store the iteration count to get to the root
  tmp_itr,act_itr=c_matrix(ct.c_int,y_resolution,x_resolution)
  # coefficients of the polynomial in library form
  poly_coeffs=c_vector(ct.c_double,len(coeffs),coeffs)
  poly_degree=len(coeffs)-1

  # call the library function
  limit=_sample_newton(
    tmp_re,tmp_im,tmp_itr,poly_coeffs,ct.c_int(max_itr),ct.c_int(num_threads),ct.c_int(poly_degree),ct.c_int(x_resolution)
    ,ct.c_int(y_resolution),ct.c_double(startx),ct.c_double(endx),ct.c_double(starty),ct.c_double(endy),ct.c_bool(verbose)
  )

  del tmp_itr
  del tmp_re
  del tmp_im
  # convert roots to a numpy array
  roots=1j*np.ctypeslib.as_array(act_im)
  roots+=np.ctypeslib.as_array(act_re)

  # determine the actual roots
  actuals=np.roots(np.flip(coeffs))
  # real and imaginary parts of the actual roots
  roots_re=c_vector(ct.c_double,len(actuals),np.real(actuals))
  roots_im=c_vector(ct.c_double,len(actuals),np.imag(actuals))
  # array to store which root the approximation is
  ind=c_vector(ct.c_int,y_resolution*x_resolution)
  
  # we can't use `act_re` and `act_im` because they're 2d and we need a 1d vector
  total=x_resolution*y_resolution
  re=c_vector(ct.c_double,total,np.real(roots.flatten()))
  im=c_vector(ct.c_double,total,np.imag(roots.flatten()))
  # call the library function
  _assign_roots(ind,re,im,roots_re,roots_im,ct.c_int(poly_degree),ct.c_int(x_resolution),ct.c_int(y_resolution))

  # reshape into a 2D array and flip the rows because [startx,stary] is stored in [0,0] 
  return np.flipud(roots) \
    ,np.flipud(np.reshape(np.ctypeslib.as_array(ind),(y_resolution,x_resolution))) \
    ,np.flipud(np.ctypeslib.as_array(act_itr)) \
    ,limit

def sample_newton_cuda(coeffs,central_point,x_span,y_span,x_resolution,y_resolution,max_itr,verbose=False):
  '''
  Produce Newton's fractals for a given polynomial with CUDA acceleration.
  
  Parameters
  ----------
  coeffs : 1D array-like
    - The coefficient of the polynomial, in order from lowest to highest degree.
  central_point : 1D array-like
    - The centre of the area to.
  x_span,y_span : int
    - The span across each axis, with half of the span on either side of the centre.
  x_resolution,y_resolution : int
    - The number of pizels to divide the x- and y-axes into.
  max_itr : int
    - The number of iterations to compute before considering a point to not converge.
  verbose : bool, optional
    - For verbose output.

  Returns
  -------
  roots : 2D numpy.ndarray
    - The approximation of the root which was found.
  ind : 2D numpy.ndarray
    - The root converged to.
  itr : 2D numpy.ndarray
    - The number of iterations for a pixel to converge to a root.
  limit : int
    - The value which represents no root was converged to.

  '''
  if not CUDA_ENABLED: raise CUDAWarning('CUDA library has not been implemented.')
  # input setup
  startx=central_point[0]-x_span/2.
  starty=central_point[1]-y_span/2.
  endx=central_point[0]+x_span/2.
  endy=central_point[1]+y_span/2.
  
  # arrays to store the real part of the root approached and the imaginary part of the root approached
  re=c_vector(ct.c_double,y_resolution*x_resolution)
  im=c_vector(ct.c_double,y_resolution*x_resolution)
  # array to store the iteration count to get to the root
  itr=c_vector(ct.c_int,y_resolution*x_resolution)
  # coefficients of the polynomial in library form
  poly_coeffs=c_vector(ct.c_double,len(coeffs),coeffs)
  poly_degree=len(coeffs)-1

  # call the library function
  limit=_sample_newton_cuda(
    re,im,itr,poly_coeffs,ct.c_int(max_itr),ct.c_int(poly_degree),ct.c_int(x_resolution),ct.c_int(y_resolution)
    ,ct.c_double(startx),ct.c_double(endx),ct.c_double(starty),ct.c_double(endy),ct.c_bool(verbose)
  )

  # convert roots to a numpy array
  roots=1j*np.ctypeslib.as_array(im)
  roots+=np.ctypeslib.as_array(re)

  # determine the actual roots
  actuals=np.roots(np.flip(coeffs))
  # real and imaginary parts of the actual roots
  roots_re=c_vector(ct.c_double,len(actuals),np.real(actuals))
  roots_im=c_vector(ct.c_double,len(actuals),np.imag(actuals))
  # array to store which root the approximation is
  ind=c_vector(ct.c_int,y_resolution*x_resolution)

  # call the library function
  _assign_roots_cuda(ind,re,im,roots_re,roots_im,ct.c_int(poly_degree),ct.c_int(x_resolution),ct.c_int(y_resolution))

  # reshape into a 2D array and flip the rows because [startx,stary] is stored in [0,0] 
  return np.flipud(np.reshape(roots,(y_resolution,x_resolution))) \
    ,np.flipud(np.reshape(np.ctypeslib.as_array(ind),(y_resolution,x_resolution))) \
    ,np.flipud(np.reshape(np.ctypeslib.as_array(itr),(y_resolution,x_resolution))) \
    ,limit

def _plot_setup(fig_inches):
  '''
  Internal function to produce a figure with a layout common to all visualisations.
  
  Parameters
  ----------
  fig_inches : string, optional
    - The size to make the figure.

  Returns
  -------
  fig : matplotlib.figure.Figure
    A blank Figure
  ax : matplotlib.axes.Axis
    The Axis of `fig`

  '''
  fig,ax=plt.subplots()
  # remove all borders
  fig.subplots_adjust(0,0,1,1)
  # remove all ticks and labels
  ax.set_xticks([])
  ax.set_yticks([])
  ax.set_xticklabels([])
  ax.set_yticklabels([])
  # scale
  fig.set_size_inches(fig_inches)

  return fig,ax
