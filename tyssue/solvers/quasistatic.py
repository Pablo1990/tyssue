# /bin/env python
"""Quasistatic solver for vertex models

"""
import numpy as np
import logging

from scipy import optimize
from .. import config
from ..collisions import solve_collisions
from ..topology import auto_t1, auto_t3

log = logging.getLogger(__name__)


class QSSolver:
    """Quasistatic solver performing a gradient descent on a :class:`tyssue.Epithelium`
    object.

    Methods
    -------
    find_energy_min : energy minimization calling `scipy.optimize.minimize`
    approx_grad : uses `optimize.approx_fprime` to compute an approximated
      gradient.
    check_grad : compares the approximated gradient with the one provided
      by the model
    """

    def __init__(self, with_collisions=False, with_t1=False, with_t3=False):
        """Creates a quasistatic gradient descent solver with optional
        type1, type3 and collision detection and solving routines.

        Parameters
        ----------
        with_t1 : bool, default False
            whether or not to solve type 1 transitions at each
            iteration.
        with_t3 : bool, default False
            whether or not to solve type 3 transitions
            (i.e. elimnation of small triangular faces) at each
            iteration.
        with_collisions : bool, default False
            wheter or not to solve collisions

        Those corrections are applied in this order: first the type 1, then the
        type 3, then the collisions

        """
        self.set_pos = self._set_pos
        if with_collisions:
            self.set_pos = solve_collisions(self.set_pos)
        if with_t1:
            self.set_pos = auto_t1(self.set_pos)
        if with_t3:
            self.set_pos = auto_t3(self.set_pos)
        self.restart = True
        self.rearange = with_t1 or with_t3

    def find_energy_min(self, eptm, geom, model, **minimize_kw):
        """Energy minimization function.

        The epithelium's total energy is minimized by displacing its vertices.
        This is a wrapper around `scipy.optimize.minimize`

        Parameters
        ----------
        eptm : a :class:`tyssue.Epithlium` object
        geom : a geometry class
        geom must provide an `update_all` method that takes `eptm`
            as sole argument and updates the relevant geometrical quantities
        model : a model class
            model must provide `compute_energy` and `compute_gradient` methods
            that take `eptm` as first and unique positional argument.

        """
        log.info("initial number of vertices: %i", eptm.Nv)
        settings = config.solvers.quasistatic()
        settings.update(**minimize_kw)
        res = self._minimize(eptm, geom, model, **settings)
        log.info("final number of vertices: %i", eptm.Nv)

        return res

    def _minimize(self, eptm, geom, model, **kwargs):
        while True:

            pos0 = eptm.vert_df.loc[eptm.active_verts, eptm.coords].values.flatten()
            try:
                res = optimize.minimize(
                    self._opt_energy,
                    pos0,
                    args=(eptm, geom, model),
                    jac=self._opt_grad,
                    **kwargs
                )
                return res
            except TopologyChangeError as err:
                log.info(err)

    def _set_pos(self, eptm, geom, pos):
        ndims = len(eptm.coords)
        num_p = pos.size // ndims
        eptm.vert_df.loc[eptm.active_verts, eptm.coords] = pos.reshape((num_p, ndims))
        geom.update_all(eptm)

    def _opt_energy(self, pos, eptm, geom, model):
        if self.rearange and pos.size // len(eptm.coords) != eptm.active_verts.size:
            raise TopologyChangeError("Topology changed before energy evaluation")
        self.set_pos(eptm, geom, pos)
        return model.compute_energy(eptm)

    # The unused arguments bellow are legit, we need the same signature as _opt_energy
    def _opt_grad(self, pos, eptm, geom, model):
        if self.rearange and pos.size // len(eptm.coords) != eptm.active_verts.size:
            raise TopologyChangeError("Topology changed before gradient evaluation")
        grad_i = model.compute_gradient(eptm)
        return grad_i.loc[eptm.active_verts].values.ravel()

    def approx_grad(self, eptm, geom, model):
        pos0 = eptm.vert_df.loc[eptm.active_verts, eptm.coords].values.ravel()
        grad = optimize.approx_fprime(pos0, self._opt_energy, 1e-9, eptm, geom, model)
        return grad

    def check_grad(self, eptm, geom, model):
        pos0 = eptm.vert_df.loc[eptm.active_verts, eptm.coords].values.ravel()
        grad_err = optimize.check_grad(
            self._opt_energy, self._opt_grad, pos0.flatten(), eptm, geom, model
        )
        return grad_err


class TopologyChangeError(ValueError):
    """ Raised when trying to assign values without
    the correct length to an epithelium dataset
    """

    pass