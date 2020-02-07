
//+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+//
//                                                                                                                                       //
// linalg.cpp                                                                                                                            //
//                                                                                                                                       //
// D. C. Groothuizen Dijkema - February, 2020                                                                                            //
//+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+//

// Linear algebra routines for fractals


#include <fractal.hpp>

template <typename T>
eigenpair<T>::eigenpair(const size_t size) : size(size), vector(new T[size])
{
}

template <typename T>
eigenpair<T>::eigenpair(const T value, const size_t size) : eigenpair(size), value(value)
{
}

template <typename T>
eigenpair<T>::~eigenpair()
{
  delete[] vector;
}

template <typename T>
[[nodiscard]] T &eigenpair<T>::operator[](size_t idx)
{
  if (idx>=size)
  {
    std::ostringstream err_message;
    err_message << idx << " is not in range for an eigenvector of size " << this->size;
    throw std::out_of_range(err_message.str());
  }
  return *(vector+idx)
}

template <typename T>
[[nodiscard]] const T &eigenpair<T>::operator[](const size_t idx)
{
  return (*this)[const_cast<size_t>(idx)]
}


double **initialise_companion_matrix(const int degree)
{
  if (degree<2) { throw std::invalid_argument("`degree` must be greater than or equal to 2"); }
  double **mat=new double*[degree];
  for (int itr=0;itr<degree;++itr)
  {
    *(mat+itr)=new double[degree];
    std::fill(*(mat+itr),*(mat+itr)+degree,0.);
  }
  for (int itr=1,jtr=0;itr<degree,jtr<degree-1;++itr,++jtr) { *(*(mat+itr)+jtr)=1.; }
  return mat;
}

void assign_companion_matrix(double * const * const mat, double const * const coeffs, const int degree)
{
  for (int itr=0;itr<degree;++itr) { *(*(mat+itr)+degree-1)=*(coeffs+itr); }
}

void __declspec(dllexport) roots(double const * const coeffs, double * const roots_re, double * const roots_im, const int degree)
{
}
