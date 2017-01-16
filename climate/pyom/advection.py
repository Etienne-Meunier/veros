import numpy as np


def adv_flux_2nd(adv_fe,adv_fn,adv_ft,var,pyom):
    """
    2th order advective tracer flux
    """
    # integer, intent(in) :: is_,ie_,js_,je_,nz_
    # real*8, intent(inout) :: adv_fe(is_:ie_,js_:je_,nz_), adv_fn(is_:ie_,js_:je_,nz_)
    # real*8, intent(inout) :: adv_ft(is_:ie_,js_:je_,nz_),    var(is_:ie_,js_:je_,nz_)
    # integer :: i,j,k

    for k in xrange(pyom.nz): # k = 1,nz
        for j in xrange(pyom.js_pe,pyom.je_pe):
            for i in xrange(pyom.is_pe-1,pyom.ie_pe):
                adv_fe[i,j,k] = 0.5*(var[i,j,k] + var[i+1,j,k])*pyom.u[i,j,k,pyom.tau]*pyom.maskU[i,j,k]

    for k in xrange(pyom.nz): # k = 1,nz
        for j in xrange(pyom.js_pe-1,pyom.je_pe):
            for i in xrange(pyom.is_pe,pyom.ie_pe):
                adv_fn[i,j,k] = pyom.cosu[j]*0.5*(var[i,j,k] + var[i,j+1,k])*pyom.v[i,j,k,pyom.tau]*pyom.maskV[i,j,k]

    for k in xrange(pyom.nz-1): # k = 1,nz-1
        for j in xrange(pyom.js_pe,pyom.je_pe):
            for i in xrange(pyom.is_pe,pyom.ie_pe):
                adv_ft[i,j,k] = 0.5*(var[i,j,k] + var[i,j,k+1])*pyom.w[i,j,k,pyom.tau]*pyom.maskW[i,j,k]

    adv_ft[:,:,pyom.nz-1] = 0.0

def adv_flux_superbee(adv_fe,adv_fn,adv_ft,var,pyom):
    """
    from MITgcm
    Calculates advection of a tracer
    using second-order interpolation with a flux limiter:
    \begin{equation*}
    F^x_{adv} = U \overline{ \theta }^i
    - \frac{1}{2} \left([ 1 - \psi(C_r) ] |U|
       + U \frac{u \Delta t}{\Delta x_c} \psi(C_r)
                 \right) \delta_i \theta
    \end{equation*}
    where the $\psi(C_r)$ is the limiter function and $C_r$ is
    the slope ratio.
    """

    # integer, intent(in) :: is_,ie_,js_,je_,nz_
    # real*8, intent(inout) :: adv_fe(is_:ie_,js_:je_,nz_), adv_fn(is_:ie_,js_:je_,nz_)
    # real*8, intent(inout) :: adv_ft(is_:ie_,js_:je_,nz_),    var(is_:ie_,js_:je_,nz_)
    # integer :: i,j,k,km1,kp2
    # real*8 :: Rjp,Rj,Rjm,uCFL = 0.5,Cr

    # Statement function to describe flux limiter
    # Upwind        Limiter = lambda Cr: 0.
    # Lax-Wendroff  Limiter = lambda Cr: 1.
    # Suberbee      Limiter = lambda Cr: max(0.,max(min(1.,2*Cr),min(2.,Cr)))
    # Sweby         Limiter = lambda Cr: max(0.,max(min(1.,1.5*Cr),min(1.5.,Cr)))
    # real*8 :: Limiter
    Limiter = lambda Cr: max(0.,max(min(1.,2.*Cr), min(2.,Cr)))
    # ! Limiter = lambda Cr: max(0.,max(min(1.,1.5*Cr), min(1.5,Cr)))

    for k in xrange(pyom.nz): # k = 1,nz
        for j in xrange(pyom.js_pe,pyom.je_pe): # j = js_pe,je_pe
            for i in xrange(pyom.is_pe-1,pyom.ie_pe): # i = is_pe-1,ie_pe
                uCFL = abs(pyom.u[i,j,k,pyom.tau]*dt_tracer/(pyom.cost[j]*pyom.dxt[i]))
                Rjp = (var[i+2,j,k]-var[i+1,j,k])*pyom.maskU[i+1,j,k]
                Rj = (var[i+1,j,k]-var[i,j,k])*pyom.maskU[i,j,k]
                Rjm = (var[i,j,k]-var[i-1,j,k])*pyom.maskU[i-1,j,k]
                if Rj != 0.:
                    if pyom.u[i,j,k,pyom.tau] > 0:
                        Cr = Rjm/Rj
                    else:
                        Cr = Rjp/Rj
                else:
                    if pyom.u[i,j,k,pyom.tau] > 0:
                        Cr = Rjm*1e20
                    else:
                        Cr = Rjp*1e20
                Cr = Limiter(Cr)
                adv_fe[i,j,k] = pyom.u[i,j,k,pyom.tau]*(var[i+1,j,k]+var[i,j,k])*0.5 \
                                - abs(pyom.u[i,j,k,pyom.tau])*((1.-Cr)+uCFL*Cr)*Rj*0.5

    for k in xrange(pyom.nz-1): # k = 1,nz
        for j in xrange(pyom.js_pe-1,pyom.je_pe): # j = js_pe-1,je_pe
            for i in xrange(pyom.is_pe,pyom.ie_pe): # i = is_pe,ie_pe
                Rjp = (var[i,j+2,k]-var[i,j+1,k])*pyom.maskV[i,j+1,k]
                Rj = (var[i,j+1,k]-var[i,j,k])*pyom.maskV[i,j,k]
                Rjm = (var[i,j,k]-var(i,j-1,k))*pyom.maskV(i,j-1,k)
                uCFL = abs(pyom.cosu[j]*pyom.v[i,j,k,pyom.tau]*dt_tracer/(pyom.cost[j]*pyom.dyt[j]))
                if Rj != 0.:
                    if pyom.v[i,j,k,pyom.tau] > 0:
                        Cr = Rjm/Rj
                    else:
                        Cr = Rjp/Rj
                else:
                    if pyom.v[i,j,k,pyom.tau] > 0:
                        Cr = Rjm*1e20
                    else:
                        Cr = Rjp*1e20
                Cr = Limiter(Cr)
                adv_fn[i,j,k] = pyom.cosu[j]*pyom.v[i,j,k,pyom.tau]*(var[i,j+1,k]+var[i,j,k])*0.5   \
                                -abs(pyom.cosu[j]*pyom.v[i,j,k,pyom.tau])*((1.-Cr)+uCFL*Cr)*Rj*0.5

    for k in xrange(pyom.nz-1): # k = 1,nz-1
        kp2 = min(pyom.nz,k+2); #if (kp2>np) kp2 = 3
        km1 = max(0,k-1) #if (km1<1) km1 = np-2
        for j in xrange(pyom.js_pe,pyom.je_pe): # j = js_pe,je_pe
            for i in xrange(pyom.is_pe,pyom.ie_pe): # i = is_pe,ie_pe
                Rjp=(var[i,j,kp2]-var[i,j,k+1])*pyom.maskW[i,j,k+1]
                Rj =(var[i,j,k+1]-var[i,j,k])*pyom.maskW[i,j,k]
                Rjm=(var[i,j,k]-var[i,j,km1])*pyom.maskW[i,j,km1]
                uCFL = abs(pyom.w[i,j,k,pyom.tau]*dt_tracer/dzt[k])
                if Rj != 0.:
                    if pyom.w[i,j,k,pyom.tau] > 0:
                        Cr = Rjm/Rj
                    else:
                        Cr = Rjp/Rj
                else:
                    if pyom.w[i,j,k,pyom.tau] > 0:
                        Cr = Rjm*1e20
                    else:
                        Cr = Rjp*1e20
                Cr = Limiter(Cr)
                adv_ft[i,j,k] = pyom.w[i,j,k,pyom.tau]*(var[i,j,k+1]+var[i,j,k])*0.5 \
                                -abs(pyom.w[i,j,k,pyom.tau])*((1.-Cr)+uCFL*Cr)*Rj*0.5
    adv_ft[:,:,pyom.nz] = 0.0


def calculate_velocity_on_wgrid(pyom):
    """
    calculates advection velocity for tracer on W grid
    """
    #integer :: i,j,k
    #real*8 :: fxa,fxb

    # lateral advection velocities on W grid
    for k in xrange(pyom.nz-1): # k = 1,nz-1
        pyom.u_wgrid[:,:,k] = pyom.u[:,:,k+1,pyom.tau]*pyom.maskU[:,:,k+1]*0.5*dzt[k+1]/pyom.dzw[k] + pyom.u[:,:,k,pyom.tau]*pyom.maskU[:,:,k]*0.5*dzt[k]/pyom.dzw[k]
        pyom.v_wgrid[:,:,k] = pyom.v[:,:,k+1,pyom.tau]*pyom.maskV[:,:,k+1]*0.5*dzt[k+1]/pyom.dzw[k] + pyom.v[:,:,k,pyom.tau]*pyom.maskV[:,:,k]*0.5*dzt[k]/pyom.dzw[k]
    k = pyom.nz
    pyom.u_wgrid[:,:,k] = pyom.u[:,:,k,pyom.tau]*pyom.maskU[:,:,k]*0.5*dzt[k]/pyom.dzw[k]
    pyom.v_wgrid[:,:,k] = pyom.v[:,:,k,pyom.tau]*pyom.maskV[:,:,k]*0.5*dzt[k]/pyom.dzw[k]

    # redirect velocity at bottom and at topography
    k = 0 # k = 1
    pyom.u_wgrid[:,:,k] = pyom.u_wgrid[:,:,k] + pyom.u[:,:,k,pyom.tau]*pyom.maskU[:,:,k]*0.5*dzt[k]/pyom.dzw[k]
    pyom.v_wgrid[:,:,k] = pyom.v_wgrid[:,:,k] + pyom.v[:,:,k,pyom.tau]*pyom.maskV[:,:,k]*0.5*dzt[k]/pyom.dzw[k]
    for k in xrange(pyom.nz-1): # k = 1,nz-1
        for j in xrange(pyom.js_pe-pyom.onx,pyom.je_pe+pyom.onx): # j = js_pe-onx,je_pe+onx
            for i in xrange(pyom.is_pe-pyom.onx,pyom.ie_pe+pyom.onx-1): # i = is_pe-onx,ie_pe+onx-1
                if pyom.maskW[i,j,k]*pyom.maskW[i+1,j,k] == 0:
                    pyom.u_wgrid[i,j,k+1] = pyom.u_wgrid[i,j,k+1]+pyom.u_wgrid[i,j,k]*pyom.dzw[k]/pyom.dzw[k+1]
                    pyom.u_wgrid[i,j,k] = 0.

    for j in xrange(pyom.js_pe-pyom.onx,pyom.je_pe+pyom.onx-1): # j = js_pe-onx,je_pe+onx-1
        for i in xrange(pyom.is_pe-pyom.onx,pyom.ie_pe+pyom.onx): # i = is_pe-onx,ie_pe+onx
            if pyom.maskW[i,j,k]*pyom.maskW[i,j+1,k] == 0 :
                pyom.v_wgrid[i,j,k+1] = pyom.v_wgrid[i,j,k+1]+pyom.v_wgrid[i,j,k]*pyom.dzw[k]/pyom.dzw[k+1]
                pyom.v_wgrid[i,j,k] = 0.

    # vertical advection velocity on W grid from continuity
    k = 0 # k = 1
    pyom.w_wgrid[:,:,k] = 0.
    for k in xrange(pyom.nz): # k = 1,nz
        for j in xrange(pyom.js_pe-pyom.onx+1,pyom.je_pe+pyom.onx): # j = js_pe-onx+1,je_pe+onx
            for i in xrange(pyom.is_pe-pyom.onx+1,pyom.ie_pe+pyom.onx): # i = is_pe-onx+1,ie_pe+onx
                pyom.w_wgrid[i,j,k] = pyom.w_wgrid[i,j,max(1,k-1)]-pyom.dzw[k]* \
                    ((pyom.u_wgrid[i,j,k]-pyom.u_wgrid[i-1,j,k])/(pyom.cost[j]*pyom.dxt[i]) \
                    +(pyom.cosu[j]*pyom.v_wgrid[i,j,k]-pyom.cosu[j-1]*pyom.v_wgrid(i,j-1,k))/(pyom.cost[j]*pyom.dyt[j]))

 # test continuity
 #if  modulo(itt*dt_tracer,ts_monint) < dt_tracer .and. .false.:
 # fxa = 0;fxb = 0;
 # for j in xrange(js_pe,je_pe): # j = js_pe,je_pe
 #  for i in xrange(is_pe,ie_pe): # i = is_pe,ie_pe
 #    fxa = fxa + w_wgrid(i,j,nz) *area_t(i,j)
 #    fxb = fxb +   w(i,j,nz,tau) *area_t(i,j)
 #  enddo
 # enddo
 # call global_sum(fxa); call global_sum(fxb);
 # if (my_pe==0) print'(a,e12.6,a)',' transport at sea surface on t grid = ',fxb,' m^3/s'
 # if (my_pe==0) print'(a,e12.6,a)',' transport at sea surface on w grid = ',fxa,' m^3/s'
#
#
#  fxa = 0;fxb = 0;
#  for j in xrange(js_pe,je_pe): # j = js_pe,je_pe
#   for i in xrange(is_pe,ie_pe): # i = is_pe,ie_pe
#     fxa = fxa + w_wgrid(i,j,nz)**2 *area_t(i,j)
#     fxb = fxb +   w(i,j,nz,tau)**2 *area_t(i,j)
#   enddo
#  enddo
#  call global_sum(fxa); call global_sum(fxb);
#  if (my_pe==0) print'(a,e12.6,a)',' w variance on t grid = ',fxb,' (m^3/s)^2'
#  if (my_pe==0) print'(a,e12.6,a)',' w variance on w grid = ',fxa,' (m^3/s)^2'

# endif


def adv_flux_superbee_wgrid(adv_fe,adv_fn,adv_ft,var,pyom):
    """
    Calculates advection of a tracer defined on Wgrid
    """
    # integer, intent(in) :: is_,ie_,js_,je_,nz_
    # real*8, intent(inout) :: adv_fe(is_:ie_,js_:je_,nz_), adv_fn(is_:ie_,js_:je_,nz_)
    # real*8, intent(inout) :: adv_ft(is_:ie_,js_:je_,nz_),    var(is_:ie_,js_:je_,nz_)
    # integer :: i,j,k,km1,kp2,kp1
    # real*8 :: Rjp,Rj,Rjm,uCFL = 0.5,Cr

    # Statement function to describe flux limiter
    # Upwind        Limiter = lambda Cr: 0.
    # Lax-Wendroff  Limiter = lambda Cr: 1.
    # Suberbee      Limiter = lambda Cr: max(0.,max(min(1.,2*Cr),min(2.,Cr)))
    # Sweby         Limiter = lambda Cr: max(0.,max(min(1.,1.5*Cr),min(1.5.,Cr)))
    # real*8 :: Limiter
    Limiter = lambda Cr: max(0.,max(min(1.,2.*Cr), min(2.,Cr)))
    # real*8 :: maskUtr,maskVtr,maskWtr
    maskUtr = lambda i,j,k: pyom.maskW[i+1,j,k]*pyom.maskW[i,j,k]
    maskVtr = lambda i,j,k: pyom.maskW[i,j+1,k]*pyom.maskW[i,j,k]
    maskWtr = lambda i,j,k: pyom.maskW[i,j,k+1]*pyom.maskW[i,j,k]

    for k in xrange(pyom.nz): # k = 1,nz
        for j in xrange(pyom.js_pe,pyom.je_pe): # j = js_pe,je_pe
            for i in xrange(pyom.is_pe-1,pyom.ie_pe): # i = is_pe-1,ie_pe
                uCFL = ABS(pyom.u_wgrid[i,j,k]*dt_tracer/(pyom.cost[j]*pyom.dxt[i]))
                Rjp = (var[i+2,j,k]-var[i+1,j,k])*maskUtr[i+1,j,k]
                Rj = (var[i+1,j,k]-var[i,j,k])*maskUtr[i,j,k]
                Rjm = (var[i,j,k]-var[i-1,j,k])*maskUtr[i-1,j,k]
                if Rj != 0.:
                    if pyom.u_wgrid[i,j,k] > 0:
                        Cr = Rjm/Rj
                    else:
                        Cr = Rjp/Rj
                else:
                    if pyom.u_wgrid[i,j,k] > 0:
                        Cr = Rjm*1e20
                    else:
                        Cr = Rjp*1e20
                Cr = Limiter(Cr)
                adv_fe[i,j,k] = pyom.u_wgrid[i,j,k]*(var[i+1,j,k]+var[i,j,k])*0.5   \
                                -abs(pyom.u_wgrid[i,j,k])*((1.-Cr)+uCFL*Cr)*Rj*0.5

    for k in xrange(pyom.nz): # k = 1,nz
        for j in xrange(pyom.js_pe-1,pyom.je_pe): # j = js_pe-1,je_pe
            for i in xrange(pyom.is_pe,pyom.ie_pe): # i = is_pe,ie_pe
                Rjp = (var[i,j+2,k]-var[i,j+1,k])*maskVtr[i,j+1,k]
                Rj = (var[i,j+1,k]-var[i,j,k])*maskVtr[i,j,k]
                Rjm = (var[i,j,k]-var(i,j-1,k))*maskVtr(i,j-1,k)
                uCFL = abs(pyom.cosu[j]*pyom.v_wgrid[i,j,k]*dt_tracer/(pyom.cost[j]*pyom.dyt[j]))
                if Rj != 0.:
                    if pyom.v_wgrid[i,j,k] > 0:
                        Cr = Rjm/Rj
                    else:
                        Cr = Rjp/Rj
                else:
                    if pyom.v_wgrid[i,j,k] > 0:
                        Cr = Rjm*1e20
                    else:
                        Cr = Rjp*1e20
                Cr = Limiter(Cr)
                adv_fn[i,j,k] = pyom.cosu[j]*pyom.v_wgrid[i,j,k]*(var[i,j+1,k]+var[i,j,k])*0.5   \
                                -abs(pyom.cosu[j]*pyom.v_wgrid[i,j,k])*((1.-Cr)+uCFL*Cr)*Rj*0.5

    for k in xrange(pyom.nz-1): # k = 1,nz-1
        kp1 = min(pyom.nz-1,k+1)
        kp2 = min(pyom.nz,k+2);
        km1 = max(1,k-1)
        for j in xrange(pyom.js_pe,pyom.je_pe): # j = js_pe,je_pe
            for i in xrange(pyom.is_pe,pyom.ie_pe): # i = is_pe,ie_pe
                Rjp = (var[i,j,kp2]-var[i,j,k+1])*maskWtr(i,j,kp1)
                Rj = (var[i,j,k+1]-var[i,j,k])*maskWtr[i,j,k]
                Rjm = (var[i,j,k]-var[i,j,km1])*maskWtr[i,j,km1]
                uCFL = abs(pyom.w_wgrid[i,j,k]*dt_tracer/pyom.dzw[k])
                if Rj != 0.:
                    if pyom.w_wgrid[i,j,k] > 0:
                        Cr = Rjm/Rj
                    else:
                        Cr = Rjp/Rj
                else:
                    if pyom.w_wgrid[i,j,k] > 0:
                        Cr = Rjm*1e20
                    else:
                        Cr = Rjp*1e20
                Cr = Limiter(Cr)
                adv_ft[i,j,k] = pyom.w_wgrid[i,j,k]*(var[i,j,k+1]+var[i,j,k])*0.5   \
                                -abs(pyom.w_wgrid[i,j,k])*((1.-Cr)+uCFL*Cr)*Rj*0.5
    adv_ft[:,:,pyom.nz] = 0.0


def adv_flux_upwind_wgrid(adv_fe,adv_fn,adv_ft,var,pyom):
    """
    Calculates advection of a tracer defined on Wgrid
    """
    #  integer, intent(in) :: is_,ie_,js_,je_,nz_
    #  real*8, intent(inout) :: adv_fe(is_:ie_,js_:je_,nz_), adv_fn(is_:ie_,js_:je_,nz_)
    #  real*8, intent(inout) :: adv_ft(is_:ie_,js_:je_,nz_),    var(is_:ie_,js_:je_,nz_)
    #  integer :: i,j,k
    #  real*8 :: Rj
    #  real*8 :: maskUtr,maskVtr,maskWtr
    maskUtr[i,j,k] = pyom.maskW[i+1,j,k]*pyom.maskW[i,j,k]
    maskVtr[i,j,k] = pyom.maskW[i,j+1,k]*pyom.maskW[i,j,k]
    maskWtr[i,j,k] = pyom.maskW[i,j,k+1]*pyom.maskW[i,j,k]

    for k in xrange(pyom.nz): # k = 1,nz
        for j in xrange(pyom.js_pe,pyom.je_pe): # j = js_pe,je_pe
            for i in xrange(pyom.is_pe-1,pyom.ie_pe): # i = is_pe-1,ie_pe
                Rj = (var[i+1,j,k]-var[i,j,k])*maskUtr[i,j,k]
                adv_fe[i,j,k] = pyom.u_wgrid[i,j,k]*(var[i+1,j,k]+var[i,j,k])*0.5 - abs(pyom.u_wgrid[i,j,k])*Rj*0.5

    for k in xrange(pyom.nz): # k = 1,nz
        for j in xrange(pyom.js_pe-1,pyom.je_pe): # j = js_pe-1,je_pe
            for i in xrange(pyom.is_pe,pyom.ie_pe): # i = is_pe,ie_pe
                Rj = (var[i,j+1,k]-var[i,j,k])*maskVtr[i,j,k]
                adv_fn[i,j,k] = pyom.cosu[j]*pyom.v_wgrid[i,j,k]*(var[i,j+1,k]+var[i,j,k])*0.5 -ABS(pyom.cosu[j]*pyom.v_wgrid[i,j,k])*Rj*0.5

    for k in xrange(pyom.nz-1): # k = 1,nz-1
        for j in xrange(pyom.js_pe,pyom.je_pe): # j = js_pe,je_pe
            for i in xrange(pyom.is_pe,pyom.ie_pe): # i = is_pe,ie_pe
                Rj = (var[i,j,k+1]-var[i,j,k])*maskWtr[i,j,k]
                adv_ft[i,j,k] = pyom.w_wgrid[i,j,k]*(var[i,j,k+1]+var[i,j,k])*0.5 - abs(pyom.w_wgrid[i,j,k])*Rj*0.5

    adv_ft[:,:,pyom.nz] = 0.0