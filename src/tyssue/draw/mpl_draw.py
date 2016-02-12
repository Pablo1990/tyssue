"""
Matplotlib based plotting
"""

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, FancyArrow
from matplotlib.collections import PatchCollection
import pandas as pd
import numpy as np
from ..config.json_parser import load_default
from ..utils.utils import spec_updater

COORDS = ['x', 'y']


def sheet_view(sheet, coords=COORDS, **draw_specs_kw):
    """ Base view function, parametrizable
    through draw_secs
    """
    draw_specs = load_default('draw', 'sheet')
    spec_updater(draw_specs, draw_specs_kw)

    fig, ax = plt.subplots()
    jv_spec = draw_specs['jv']
    if jv_spec['visible']:
        ax = draw_jv(sheet, coords, ax, **jv_spec)

    je_spec = draw_specs['je']
    if je_spec['visible']:
        ax = draw_je(sheet, coords, ax, **je_spec)

    face_spec = draw_specs['face']
    if face_spec['visible']:
        ax = draw_face(sheet, coords, ax, **face_spec)

    ax.set_aspect('equal')
    ax.grid()
    return fig, ax

def draw_face(sheet, coords, ax, **draw_spec_kw):
    """Draws epithelial sheet polygonal faces in matplotlib
    Keyword values can be specified at the element
    level as columns of the sheet.face_df
    """

    draw_spec = load_default('draw', 'sheet')['face']
    draw_spec.update(**draw_spec_kw)

    polys = sheet.face_polygons(coords)
    patches = []
    for idx, poly in polys.items():
        patch = Polygon(poly,
                        fill=True,
                        closed=True)
        patches.append(patch)
    collection_specs = parse_face_specs(draw_spec)
    ax.add_collection(PatchCollection(patches, False,
                                      **collection_specs))
    return ax

def parse_face_specs(face_draw_specs):

    collection_specs = {}
    if "color" in face_draw_specs:
        collection_specs['facecolors'] = face_draw_specs['color']
    if "alpha" in face_draw_specs:
        collection_specs['alpha'] = face_draw_specs['alpha']
    if "zorder" in face_draw_specs:
        collection_specs['zorder'] = face_draw_specs['zorder']

    return collection_specs


def draw_jv(sheet, coords, ax, **draw_spec_kw):
    """Draw junction vertices in matplotlib
    """
    draw_spec = load_default('draw', 'sheet')['jv']
    draw_spec.update(**draw_spec_kw)

    x, y = coords
    ax.scatter(sheet.jv_df[x], sheet.jv_df[y], **draw_spec_kw)
    return ax

def draw_je(sheet, coords, ax, **draw_spec_kw):
    """
    """
    draw_spec = load_default('draw', 'sheet')['je']
    draw_spec.update(**draw_spec_kw)

    x, y = coords
    dx, dy = ('d'+c for c in coords)
    app_length = np.hypot(sheet.je_df[dx],
                          sheet.je_df[dy])

    patches = []
    arrow_specs, collections_specs = parse_je_specs(draw_spec)
    for idx, je in sheet.je_df[app_length > 1e-6].iterrows():
        srce  = int(je['srce'])
        arrow = FancyArrow(sheet.jv_df[x].loc[srce],
                           sheet.jv_df[y].loc[srce],
                           sheet.je_df[dx].loc[idx],
                           sheet.je_df[dy].loc[idx],
                            **arrow_specs)
        patches.append(arrow)

    ax.add_collection(PatchCollection(patches, True, **collections_specs))
    return ax


def parse_je_specs(je_draw_specs):

    arrow_keys = ['head_width',
                  'length_includes_head',
                  'shape']
    arrow_specs = {key: val for key, val in je_draw_specs.items()
                   if key in arrow_keys}
    collection_specs = {}
    if "color" in je_draw_specs:
        collection_specs['edgecolors'] = je_draw_specs['color']
    if "width" in je_draw_specs:
        collection_specs['linewidths'] = je_draw_specs['width']
    if "alpha" in je_draw_specs:
        collection_specs['alpha'] = je_draw_specs['alpha']
    return arrow_specs, collection_specs


def plot_forces(sheet, geom, model,
                coords, scaling,
                ax=None,
                approx_grad=None,
                **draw_specs_kw):
    """Plot the net forces at each vertex, with their amplitudes multiplied
    by `scaling`
    """
    draw_specs = load_default('draw', 'sheet')
    spec_updater(draw_specs, draw_specs_kw)
    gcoords = ['g'+c for c in coords]
    if approx_grad is not None:
        app_grad = approx_grad(sheet, geom, model)
        grad_i = pd.DataFrame(index=sheet.jv_idx,
                              data=app_grad.reshape((-1, len(sheet.coords))),
                              columns=sheet.coords) * scaling

    else:
        grad_i = model.compute_gradient(sheet, components=False) * scaling

    arrows = pd.DataFrame(columns=coords + gcoords,
                          index=sheet.jv_df.index)
    arrows[coords] = sheet.jv_df[coords]
    arrows[gcoords] = - grad_i[coords] # F = -grad E

    if ax is None:
        fig, ax = sheet_view(sheet, coords, **draw_specs)
    else:
        fig = ax.get_figure()

    for _, arrow in arrows.iterrows():
        ax.arrow(*arrow,
                 **draw_specs['grad'])
    return fig, ax


def plot_analytical_to_numeric_comp(sheet, model, geom,
                                    isotropic_model, nondim_specs):

    iso = isotropic_model
    fig, ax = plt.subplots(figsize=(8, 8))

    deltas = np.linspace(0.1, 1.8, 50)

    lbda = nondim_specs['je']['line_tension']
    gamma = nondim_specs['face']['contractility']

    ax.plot(deltas, iso.isotropic_energy(deltas, nondim_specs), 'k-',
            label='Analytical total')
    ax.plot(sheet.delta_o, iso.isotropic_energy(sheet.delta_o, nondim_specs), 'ro')
    ax.plot(deltas, iso.elasticity(deltas), 'b-',
            label='Analytical volume elasticity')
    ax.plot(deltas, iso.contractility(deltas, gamma), color='orange', ls='-',
            label='Analytical contractility')
    ax.plot(deltas, iso.tension(deltas, lbda), 'g-',
            label='Analytical line tension')

    ax.set_xlabel(r'Isotropic scaling $\delta$')
    ax.set_ylabel(r'Isotropic energie $\bar E$')

    energies = iso.isotropic_energies(sheet, model, geom,
                                      deltas, nondim_specs)
    # energies = energies / norm
    ax.plot(deltas, energies[:, 2], 'bo:', lw=2, alpha=0.8,
            label='Computed volume elasticity')
    ax.plot(deltas, energies[:, 0], 'go:', lw=2, alpha=0.8,
            label='Computed line tension')
    ax.plot(deltas, energies[:, 1], ls=':',
            marker='o', color='orange', label='Computed contractility')
    ax.plot(deltas, energies.sum(axis=1), 'ko:', lw=2, alpha=0.8,
            label='Computed total')

    ax.legend(loc='upper left', fontsize=10)
    ax.set_ylim(0, 1.2)


    print(sheet.delta_o, deltas[energies.sum(axis=1).argmin()])

    return fig, ax
