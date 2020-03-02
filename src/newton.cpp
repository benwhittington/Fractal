
//+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+//
//                                                                                                                                       //
// newton.cpp                                                                                                                            //
//                                                                                                                                       //
// D. C. Groothuizen Dijkema - January, 2020                                                                                             //
//+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+//

// Producing Newton's fractals


#include <fractal.hpp>

std::pair<std::complex<double>,std::complex<double>> polynomial_and_deriv(const std::complex<double> &x, double const * const coeffs
  , const int degree)
{
  std::complex<double> p=*(coeffs+degree),p_prime=0;

  for (int itr=degree-1;itr>=0;--itr)
  {
    p_prime=x*p_prime+p;
    p=x*p+*(coeffs+itr);
  }

  return std::make_pair(p,p_prime);
}

std::complex<double> newton_root( double const * const coeffs, int * const itr_taken, std::complex<double> x, const int degree
  , const int max_itr, const double tol)
{
  std::complex<double> init=x; 
  for (int itr=0;itr<max_itr;++itr)
  {
    std::complex<double> f_x,g_x;
    std::tie(f_x,g_x)=polynomial_and_deriv(x,coeffs,degree);
    if (abs(f_x)<tol)
    {
      *itr_taken=itr;
      return x;
    }
    if (g_x==std::complex<double>(0.,0.))
    {
      std::cerr << "Zero deriavtive encountered when starting at " << init << std::endl;
      *itr_taken=std::numeric_limits<int>::max();
      return std::complex<double>(std::numeric_limits<double>::infinity(),std::numeric_limits<double>::infinity());
    }
    
    x-=f_x/g_x;
  }
  *itr_taken=std::numeric_limits<int>::max();
  return std::complex<double>(std::numeric_limits<double>::infinity(),std::numeric_limits<double>::infinity());
}

void compute_newton_range(double **re, double **im, int **iterations, double * const coeffs, const int max_itr, const int degree
  , const int xresolution, const int start_itr, const int end_itr, const double startx, const double starty, const double deltax
  , const double deltay, const int total, bool verbose)
{
  for (int itr=start_itr;itr<end_itr;++itr)
  {
    double imag=starty+deltay*itr;
    for (int jtr=0;jtr<xresolution;++jtr)
    {
      double real=startx+deltax*jtr;
      std::complex<double> root=newton_root(coeffs,(*(iterations+itr)+jtr),std::complex<double>(real,imag),degree,max_itr,1e-6);
      *(*(re+itr)+jtr)=root.real();
      *(*(im+itr)+jtr)=root.imag();
    }
    if (verbose&&itr%100==0&&itr!=0) { std::cout << "Processed " << itr*xresolution << " points of " << total << "." << std::endl; }
  }
}

void __declspec(dllexport) sample_newton(double **re, double **im, int **iterations, double *coeffs, const int max_itr
  , const int num_threads, const int degree, const int xresolution, const int yresolution, int * const limit, const double startx
  , const double endx, const double starty, const double endy, const bool verbose)
{
  const double deltax=(endx-startx)/xresolution,deltay=(endy-starty)/yresolution;
  const int total=xresolution*yresolution;

  const std::vector<int> increments=iteration_limits(num_threads,yresolution);

  std::vector<std::thread> threads;
  for (int itr=0;itr<increments.size()-1;++itr)
  {
    threads.push_back(std::thread(
      compute_newton_range,re,im,iterations,std::ref(coeffs),max_itr,degree,xresolution,increments[itr],increments[itr+1],startx,starty,deltax,deltay
        ,total,num_threads>1 ? false : verbose
    ));
  }

  if (verbose) { std::cout << "Processing " << total << " points." << std::endl; }

  std::chrono::time_point<std::chrono::steady_clock> start=std::chrono::high_resolution_clock::now();
  for (std::thread &th:threads) { th.join(); }
  std::chrono::time_point<std::chrono::steady_clock> finish=std::chrono::high_resolution_clock::now();

  std::chrono::duration<double> elapsed=finish-start;
  if (verbose) { std::cout << total << " points processed." << std::endl; }
  if (verbose) { std::cout << "Time taken: " << elapsed.count() << "s." << std::endl; }

  *limit=std::numeric_limits<int>::max();
}
