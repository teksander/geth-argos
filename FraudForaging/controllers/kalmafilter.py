import math

import LinearAlgebraPurePython as la
from copy import deepcopy

class KalmanFilter(object):
    def __init__(self, dim_x, dim_z, dim_u):
        if dim_x < 1:
            raise ValueError('dim_x must be 1 or greater')
        if dim_z < 1:
            raise ValueError('dim_z must be 1 or greater')
        if dim_u < 0:
            raise ValueError('dim_u must be 0 or greater')

        self.dim_x = dim_x
        self.dim_z = dim_z
        self.dim_u = dim_u

        self.x = la.zeros_matrix(dim_x, 1)  # state
        self.P = la.eye_matrix(dim_x)  # uncertainty covariance
        self.Q = la.eye_matrix(dim_x)  # process uncertainty
        self.B = la.eye_matrix(dim_x)  # control transition matrix
        self.F = la.eye_matrix(dim_x)  # state transition matrix
        self.H = la.eye_matrix(dim_z)  # Measurement function
        self.R = la.eye_matrix(dim_z)  # state uncertainty
        self._alpha_sq = 1.  # fading memory control
        self.M = la.zeros_matrix(dim_z, dim_z)  # process-measurement cross correlation
        self.z = la.zeros_matrix(self.dim_z, 1)

        self.K = la.zeros_matrix(dim_x, dim_z)  # kalman gain
        self.y = la.zeros_matrix(dim_z, 1)
        self.S = la.zeros_matrix(dim_z, dim_z)  # system uncertainty
        self.SI = la.zeros_matrix(dim_z, dim_z)  # inverse system uncertainty

        # identity matrix. Do not alter this.
        self._I = la.eye_matrix(dim_x)

        # these will always be a copy of x,P after predict() is called
        self.x_prior = self.x.copy()
        self.P_prior = self.P.copy()

        # these will always be a copy of x,P after update() is called
        self.x_post = self.x.copy()
        self.P_post = self.P.copy()

        # Only computed only if requested via property

        self.inv = la.getMatrixInverse
    def setSpeed(self, s):
        self.B = la.eye_matrix(self.dim_x)
        self.B = la.matrix_multiply_scalar(self.B,s)

    def setState(self, _x):
        for idx, item in enumerate(_x):
            self.x[idx][0]=item
    def predict(self, _u):
        #u: normalized direction vector
        u=la.zeros_matrix(self.dim_u, 1)
        for idx, item in enumerate(_u):
            u[idx][0] = item
        #print('u for prediction ', u)
        B = self.B
        F = self.F
        Q = self.Q

        # x = Fx + Bu
        #print('x bafore ', self.x, la.matrix_multiply(F, self.x), la.matrix_multiply(B, u))
        self.x = la.matrix_addition(la.matrix_multiply(F, self.x), la.matrix_multiply(B, u))
        #print('x after ', self.x)
        # P = FPF' + Q
        self.P = la.matrix_addition(la.matrix_multiply(la.matrix_multiply(F, self.P), la.transpose(F)), Q)

        # save prior
        self.x_prior = self.x.copy()
        self.P_prior = self.P.copy()

    def update(self, _z):
        """
        Add a new measurement (z) to the Kalman filter.

        If z is None, nothing is computed. However, x_post and P_post are
        updated with the prior (x_prior, P_prior), and self.z is set to None.

        Parameters
        ----------
        z : (dim_z, 1): array_like
            measurement for this update. z can be a scalar if dim_z is 1,
            otherwise it must be convertible to a column vector.

        R : np.array, scalar, or None
            Optionally provide R to override the measurement noise for this
            one call, otherwise  self.R will be used.

        H : np.array, or None
            Optionally provide H to override the measurement function for this
            one call, otherwise self.H will be used.
        """
        z = la.zeros_matrix(self.dim_z, 1)
        z[0][0] = _z.x
        z[1][0] = _z.y



        R = self.R
        H = self.H

        # y = z - Hx
        # error (residual) between measurement and prediction
        self.y = la.matrix_subtraction(z, la.matrix_multiply(H, self.x))
        # common subexpression for speed
        PHT = la.matrix_multiply(self.P, la.transpose(H))

        # S = HPH' + R
        # project system uncertainty into measurement space

        self.S = la.matrix_addition(la.matrix_multiply(H, PHT), R)
        self.SI = self.inv(self.S)
        # K = PH'inv(S)
        # map system uncertainty into kalman gain
        self.K = la.matrix_multiply(PHT, self.SI)

        # x = x + Ky
        # predict new x with residual scaled by the kalman gain
        self.x = la.matrix_addition(self.x, la.matrix_multiply(self.K, self.y))

        # P = (I-KH)P(I-KH)' + KRK'
        # This is more numerically stable
        # and works for non-optimal K vs the equation
        # P = (I-KH)P usually seen in the literature.

        I_KH = la.matrix_subtraction(self._I, la.matrix_multiply(self.K, H))
        self.P = la.matrix_addition(la.matrix_multiply(la.matrix_multiply(I_KH, self.P), la.transpose(I_KH)),
                                    la.matrix_multiply(la.matrix_multiply(self.K, R), la.transpose(self.K)))

        # save measurement and posterior state
        self.z = deepcopy(z)
        self.x_post = self.x.copy()
        self.P_post = self.P.copy()
    def get_residual_modulo(self):
        x = self.y[0][0]
        y = self.y[1][0]
        return math.sqrt(x**2+y**2)
