
//+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+//
//                                                                                                                                       //
// fractal.hpp                                                                                                                           //
//                                                                                                                                       //
// D. C. Groothuizen Dijkema - January, 2020                                                                                             //
//+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+//

// Header file for Fractal project


#pragma once

#ifndef FRACTAL_H__
#define FRACTAL_H__

#include <cmath>

#include <algorithm>
#include <chrono>
#include <complex>
#include <iostream>
#include <limits>
#include <thread>
#include <vector>

template <typename OutputIt>
inline OutputIt iteration_limits(const int num_threads, const int yresolution, OutputIt out)
{
  //
  // Produce a list of numbers which represent successive left-closed, right-open intervals across which a particular thread will sample
  // the complex plane
  //
  // parameters
  // ----------
  // num_threads : const int
  //  - the number of threads used in the sampling
  // yresolution : const int 
  //  - the resolution of the sampling in the y-axis
  // out : OutputIt
  //  - output iterator where the limits are written
  //
  // returns
  // -------
  // OutputIt
  //  - an iterator to the element past the last element added to out
  //
  // OutputIt must meet the requirements of LegacyOutputIterator
  //

  const int span=yresolution/num_threads;

  for (int itr=0;itr<num_threads;++itr) { *out++=span*itr; }
  // push yresolution so that the sampling always goes as far as intended; as such, the last interval may be bigger than the rest
  *out++=yresolution;

  return out;
}

template <typename InputIt, typename OutputIt>
inline OutputIt zip(InputIt first1, InputIt last1, InputIt first2, InputIt last2, OutputIt out)
{
  //
  // Produces a container of one type constructed from two ranges
  // The constructor of the value type of the container type of the output should take two parameters, the first of which comes from the 
  // first range and the second of which comes from the second range
  //
  // parameters
  // ----------
  // first1,last1 : InputIt
  //  - the range of the first set of items to zip
  // first2,last2 : InputIt
  //  - the range of the second set of items to zip
  // out : OutputIt
  //  - output iterator where the zipped items are written
  //
  // returns
  // -------
  // OutputIt
  //  - an iterator to the element past the last element added to out
  //
  // InputIt must meet the requirements of LegacyInputIterator
  // OutputIt must meet the requirements of LegacyOutputIterator
  //

  using scalar=std::decay_t<decltype(*first1)>;
  using zipped=OutputIt::container_type::value_type;

  // iteratre across both ranges, zip, and write out
  while (first1!=last1&&first2!=last2)
  {
    *out++=zipped(static_cast<scalar>(*first1++),static_cast<scalar>(*first2++));
  }

  return out;
}

template <typename It, typename Compare>
inline std::size_t argmin(It first, It last, Compare comp)
{
  //
  // Find the index of the minimum element of a range
  //
  // parameters
  // ----------
  // first,last : It
  //  - the range over which to find the argmin
  // comep : OutputIt
  //  - output iterator where the complex numbers are written
  //
  // returns
  // -------
  // size_t
  //  - the index of the minimum element of a range
  //
  // It must meet the requirements of LegacyForwardterator
  //
  
  return std::min_element(first,last,comp)-first;
}


int iterate(std::complex<double> x, const std::complex<double> &c, const int max_itr);
void compute_mandelbrot_range(int **iterations, const int max_itr, const int xresolution, const int start_itr, const int end_itr
  , const double startx, const double starty, const double deltax, const double deltay, const int total, bool verbose);
int __declspec(dllexport) sample_mandelbrot(int **iterations, const int max_itr, const int num_threads, const int xresolution
  , const int yresolution, const double startx, const double endx, const double starty, const double endy
  , const bool verbose);

std::pair<std::complex<double>,std::complex<double>> polynomial_and_deriv(const std::complex<double> &x, double const * const coeffs
  , const int degree);
std::complex<double> newton_root( double const * const coeffs, int * const itr_taken, std::complex<double> x, const int degree
  , const int max_itr, const double tol);
void compute_newton_range(double **re, double **im, int **iterations, double * const coeffs, const int max_itr, const int degree
  , const int xresolution, const int start_itr, const int end_itr, const double startx, const double starty, const double deltax
  , const double deltay, const int total, bool verbose);
int __declspec(dllexport) sample_newton(double **re, double **im, int **iterations, double *coeffs, const int max_itr
  , const int num_threads, const int degree, const int xresolution, const int yresolution, const double startx
  , const double endx, const double starty, const double endy, const bool verbose);
void __declspec(dllexport) assign_roots(int * const * const index, const double * const * const re, const double * const * const im
  , const double * const roots_re, const double * const roots_im, const int degree, const int xresolution, const int yresolution);

#endif // FRACTAL_H__
