"""
Tools to draw a chord diagram in python
"""

from collections.abc import Sequence

import matplotlib.patches as patches

from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.colors import ColorConverter
from matplotlib.path import Path

import numpy as np
import scipy.sparse as ssp

from .gradient import gradient
from .utilities import _get_normed_line, dist, polar2xy


LW = 0.3


def chord_diagram(mat, outer_circle=None, names=None, order=None, width=0.1, pad=2., gap=0.03,
                  chordwidth=0.7, ax=None, colors=None, cmap=None, alpha=0.7,
                  use_gradient=False, chord_colors=None, show=False, name_images=None, **kwargs):
    """
    Plot a chord diagram.

    Parameters
    ----------
    mat : square matrix
        Flux data, mat[i, j] is the flux from i to j
    names : list of str, optional (default: no names)
        Names of the nodes that will be displayed (must be ordered as the
        matrix entries).
    order : list, optional (default: order of the matrix entries)
        Order in which the arcs should be placed around the trigonometric
        circle.
    width : float, optional (default: 0.1)
        Width/thickness of the ideogram arc.
    pad : float, optional (default: 2)
        Distance between two neighboring ideogram arcs. Unit: degree.
    gap : float, optional (default: 0)
        Distance between the arc and the beginning of the cord.
    chordwidth : float, optional (default: 0.7)
        Position of the control points for the chords, controlling their shape.
    ax : matplotlib axis, optional (default: new axis)
        Matplotlib axis where the plot should be drawn.
    colors : list, optional (default: from `cmap`)
        List of user defined colors or floats.
    cmap : str or colormap object (default: viridis)
        Colormap that will be used to color the arcs and chords by default.
        See `chord_colors` to use different colors for chords.
    alpha : float in [0, 1], optional (default: 0.7)
        Opacity of the chord diagram.
    use_gradient : bool, optional (default: False)
        Whether a gradient should be use so that chord extremities have the
        same color as the arc they belong to.
    chord_colors : str, RGB tuple, list, optional (default: None)
        Specify color(s) to fill the chords differently from the arcs.
        When the keyword is not used, chord colors default to the colomap given
        by `colors`.
        Possible values for `chord_colors` are:
         * a single color or RGB tuple, e.g. "red" or ``(1, 0, 0)``; all chords
           will have this color
         * a list of colors, e.g. ``["red","green","blue"]``, one per node.
           Each chord will get its color from its associated source node, or
           from both nodes if `use_gradient` is True.
    show : bool, optional (default: False)
        Whether the plot should be displayed immediately via an automatic call
        to `plt.show()`.
    **kwargs : keyword arguments
        Available kwargs are "fontsize" and "sort" (either "size" or
        "distance"), "zero_entry_size" (in degrees, default: 0.5),
        "rotate_names" (a bool or list of bools) to rotate (some of) the
        names by 90°.
    """
    import matplotlib.pyplot as plt
    from matplotlib.backend_bases import MouseButton

    def OnHover(event):
        if event.inaxes == ax:
            #upon hovering over an outer shell
            outer_flag = False
            secondary_outer_patch = None
            for i in outer_patches:
                cont, ind = outer_patches[i].contains(event)
                if cont:
                    outer_flag = True
                    if i != selected_outer_patch:
                        secondary_outer_patch = i

            if outer_flag == True:
                for si in self_patches:
                    if si != selected_outer_patch:
                        if si == secondary_outer_patch:
                            self_patches[si].set_zorder(1-mat[secondary_outer_patch, secondary_outer_patch])
                            self_patches[si].set_visible(True)
                        else:
                            self_patches[si].set_visible(False)
                for ci, cj in connector_patches:
                    if ci != selected_outer_patch and cj != selected_outer_patch:
                        if ci == secondary_outer_patch:
                            connector_patches[(ci,cj)][0].set_zorder((1-mat[secondary_outer_patch, cj]))
                            connector_patches[(ci,cj)][0].set_visible(True)
                        elif cj == secondary_outer_patch:
                            connector_patches[(ci,cj)][0].set_zorder((1-mat[secondary_outer_patch, ci]))
                            connector_patches[(ci,cj)][0].set_visible(True)
                        else:
                            connector_patches[(ci,cj)][0].set_visible(False)
                            connector_annots[(ci,cj)].set_visible(False)
                            connector_annots[(cj,ci)].set_visible(False)
            _.canvas.draw_idle()

    def OnClick(event):
        if event.inaxes == ax:
            #controls whether to turn annottions on or off
            target_patch = None
            target_zorder = -1
            for i in self_patches:
                cont, ind = self_patches[i].contains(event)
                if cont and self_patches[i].get_visible():
                    if target_zorder < self_patches[i].get_zorder():
                        target_patch = i
                        target_zorder = self_patches[i].get_zorder()
            for i, j in connector_patches:
                cont, ind = connector_patches[(i,j)][0].contains(event)
                if cont and (connector_patches[(i,j)][0].get_visible() or connector_patches[(i,j)][1].get_visible()):
                    if target_zorder < connector_patches[(i,j)][0].get_zorder():
                        target_patch = (i, j)
                        target_zorder = connector_patches[(i,j)][0].get_zorder()
            if target_patch is not None:
               ToggleChordAnnotations(target_patch)
            
            #controls setting topic as primary or not
            for i in outer_patches:
                cont, ind = outer_patches[i].contains(event)
                if cont:
                    nonlocal selected_outer_patch
                    if selected_outer_patch != i:
                        SelectArc(i)
        for i in outer_names:
            name_cont, ind = outer_names[i].contains(event)
            if name_cont and i in outer_images and outer_images[i].get_visible() is False:
                outer_images[i].set_visible(True)
                _.canvas.draw_idle()
            elif name_cont and i in outer_images and outer_images[i].get_visible():
                outer_images[i].set_visible(False)
                _.canvas.draw_idle()
            elif i in outer_images:
                image_cont, ind = outer_images[i].contains(event)
                if image_cont and outer_images[i].get_visible():
                    outer_images[i].set_visible(False)
                    _.canvas.draw_idle()
    
    def ToggleChordAnnotations(chord):
        if isinstance(chord, tuple):
            if connector_annots[chord].get_visible():
                connector_annots[(chord[0], chord[1])].set_visible(False)
                connector_annots[(chord[1], chord[0])].set_visible(False)
            else:
                connector_annots[(chord[0], chord[1])].set_visible(True)
                connector_annots[(chord[0], chord[1])].set_zorder(connector_patches[chord][0].get_zorder()*10000)
                connector_annots[(chord[1], chord[0])].set_visible(True)
                connector_annots[(chord[1], chord[0])].set_zorder(connector_patches[chord][0].get_zorder()*10000)
        elif chord is not None:
            if self_annots[chord].get_visible() and self_patches[chord].get_visible():
                self_annots[chord].set_visible(False)
            elif self_patches[chord].get_visible():
                self_annots[chord].set_visible(True)
                self_annots[chord].set_zorder(self_patches[chord].get_zorder()*10000)
        _.canvas.draw_idle()
    
    def SelectArc(new_arc):
        nonlocal selected_outer_patch
        #turn off old selected patch and reset chords and annotations to default
        outer_patches[selected_outer_patch].set_facecolor('darkgray')
        for si in self_patches:
            #self chord
            self_patches[si].set_visible(False)
            self_patches[si].set_zorder(0)
            self_patches[si].set_facecolor('darkgray')
            self_patches[si].set_edgecolor('black')
            #self annotation
            self_annots[si].set_visible(False)
            self_annots[si].set_zorder(0)
        for ci, cj in connector_patches:
            #non-gradient chord
            connector_patches[(ci,cj)][0].set_visible(False)
            connector_patches[(ci,cj)][0].set_zorder(0)
            connector_patches[(ci,cj)][0].set_facecolor('darkgray')
            connector_patches[(ci,cj)][0].set_edgecolor('black')
            #gradient chord
            connector_patches[(ci,cj)][1].set_visible(False)
            connector_patches[(ci,cj)][1].set_zorder(0)
            #both annotations
            connector_annots[(ci, cj)].set_visible(False)
            connector_annots[(ci, cj)].set_zorder(0)
            connector_annots[(cj, ci)].set_visible(False)
            connector_annots[(ci, cj)].set_zorder(0)
        #turn on new selected patch
        selected_outer_patch = new_arc
        outer_patches[selected_outer_patch].set_facecolor(colors[selected_outer_patch])
        #for self chord
        if new_arc in self_patches:
            self_patches[selected_outer_patch].set_visible(True)
            self_patches[selected_outer_patch].set_facecolor(colors[selected_outer_patch])
            self_patches[selected_outer_patch].set_edgecolor(colors[selected_outer_patch])
            self_patches[selected_outer_patch].set_zorder((1-mat[new_arc,new_arc])*100)
        #show connector chords with weighted zorder
        for ci, cj in connector_patches:
            if ci == new_arc:
                connector_patches[(ci,cj)][0].set_visible(True)
                connector_patches[(ci,cj)][0].set_facecolor(colors[selected_outer_patch])
                connector_patches[(ci,cj)][0].set_zorder((1-mat[new_arc, cj])*100)
            elif cj == new_arc:
                connector_patches[(ci,cj)][0].set_visible(True)
                connector_patches[(ci,cj)][0].set_facecolor(colors[selected_outer_patch])
                connector_patches[(ci,cj)][0].set_zorder((1-mat[new_arc, ci])*100)
        _.canvas.draw_idle()


    if ax is None:
        _, ax = plt.subplots()
    else:
        _ = ax.figure

    # copy matrix and set a minimal value for visibility of zero fluxes
    is_sparse = ssp.issparse(mat)

    if is_sparse:
        mat = mat.tocsr(copy=True)
        if outer_circle is not None:
            outer_circle = outer_circle.tocsr(copy=True)
    else:
        mat = np.array(mat, copy=True)
        if outer_circle is not None:
            outer_circle = np.array(outer_circle, copy=True)
    
    orig_mat = np.copy(mat)
    if outer_circle is not None:
        orig_outer_circle = np.copy(outer_circle)

    # mat[i, j]:  i -> j
    num_nodes = mat.shape[0]

    # set entry size for zero entries that have a nonzero reciprocal
    min_deg  = kwargs.get("zero_entry_size", 0.5)
    min_deg *= mat.sum() / (360 - num_nodes*pad)


    if is_sparse:
        nnz = mat.nonzero()

        for i, j in zip(*nnz):
            if mat[j, i] == 0:
                mat[j, i] = min_deg
        
        nnz = outer_circle.nonzero()

        for i,j in zip(*nnz):
            if outer_circle[i,j] == 0:
                outer_circle[i,j] = min_deg
    else:
        zeros = np.argwhere(mat == 0)

        for (i, j) in zeros:
            if mat[j, i] != 0:
                mat[i, j] = min_deg
                mat[i, j] = 0
        
        zeros = np.argwhere(outer_circle == 0)

        for i in zeros:
            if outer_circle[i] != 0:
                outer_circle[i] = min_deg

    # check name rotations
    rotate_names = kwargs.get("rotate_names", False)

    if isinstance(rotate_names, Sequence):
        assert len(rotate_names) == num_nodes, \
            "Wrong number of entries in 'rotate_names'."
    else:
        rotate_names = [rotate_names]*num_nodes

    # check order
    if order is not None:
        mat = mat[order][:, order]

        rotate_names = [rotate_names[i] for i in order]

        if names is not None:
            names = [names[i] for i in order]

    # sum over rows
    if outer_circle is None:
        x = mat.sum(axis=1).A1 if is_sparse else mat.sum(axis=1)
    else:
        x = outer_circle.A1 if is_sparse else outer_circle

    # configure colors
    if colors is None:
        colors = np.linspace(0, 1, num_nodes)

    if cmap is None:
        cmap = "viridis"

    if isinstance(colors, (Sequence, np.ndarray)):
        assert len(colors) == num_nodes, "One color per node is required."

        # check color type
        first_color = colors[0]

        if isinstance(first_color, (int, float, np.integer)):
            cm = plt.get_cmap(cmap)
            colors = cm(colors)[:, :3]
        else:
            colors = [ColorConverter.to_rgb(c) for c in colors]
    else:
        raise ValueError("`colors` should be a list.")

    if chord_colors is None:
       chord_colors = colors
    else:
        try:
            chord_colors = [ColorConverter.to_rgb(chord_colors)] * num_nodes
        except ValueError:
            assert len(chord_colors) == num_nodes, \
                "If `chord_colors` is a list of colors, it should include " \
                "one color per node (here {} colors).".format(num_nodes)

    # find position for each start and end
    y = x / np.sum(x).astype(float) * (360 - pad*len(x))

    pos = {}
    arc = []
    nodePos = []
    rotation = []
    start = 0

    # compute all values and optionally apply sort
    for i in range(num_nodes):
        end = start + y[i]
        arc.append((start, end))
        angle = 0.5*(start+end)

        if -30 <= angle <= 180:
            angle -= 90
            rotation.append(False)
        else:
            angle -= 270
            rotation.append(True)

        nodePos.append(
            tuple(polar2xy(1.05, 0.5*(start + end)*np.pi/180.)) + (angle,))

        z = _get_normed_line(mat, i, x, start, end, is_sparse)

        # sort chords
        ids = None

        if kwargs.get("sort", "size") == "size":
            ids = np.argsort(z)
        elif kwargs["sort"] == "distance":
            remainder = 0 if num_nodes % 2 else -1

            ids  = list(range(i - int(0.5*num_nodes), i))[::-1]
            ids += [i]
            ids += list(range(i + int(0.5*num_nodes) + remainder, i, -1))

            # put them back into [0, num_nodes[
            ids = np.array(ids)
            ids[ids < 0] += num_nodes
            ids[ids >= num_nodes] -= num_nodes
        else:
            raise ValueError("Invalid `sort`: '{}'".format(kwargs["sort"]))

        z0 = start

        for j in ids:
            pos[(i, j)] = (z0, z0 + z[j])
            #z0 += z[j]

        start = end + pad

    # plot
    outer_patches = {}
    self_patches = {}
    self_annots = {}
    connector_patches = {}
    connector_annots = {}

    outer_names = {}
    outer_images = {}
    

    for i in range(len(x)):
        color = colors[i]

        # plot the arcs
        start, end = arc[i]

        outer_patches[i] = ideogram_arc(start=start, end=end, radius=1.0, color=color,
                                        width=width, alpha=alpha, ax=ax)

        chord_color = chord_colors[i]

        

        # plot self-chords
        if mat[i, i] > 0:
            self_start, self_end = pos[(i, i)]

            start = end-(self_end-self_start)

            self_patches[i] = self_chord_arc(start, end, radius=1 - width - gap,
                                             chordwidth=0.7*chordwidth, color=chord_color,
                                             alpha=alpha, ax=ax)
            
            #mean = (start + end) /2
            mean = start
            offset_x = 20
            offset_y = 20
            if 90 < mean and mean < 270:
                offset_x *= -1
            if 180 < mean and mean < 360:
                offset_y *= -1
            
            mean *= np.pi/180.
            x, y = polar2xy(1 - width - (gap), mean)
            
            self_annots[i] = ax.annotate(str(int(orig_mat[i, i]*100))+"%", xy=(x,y), xytext=(offset_x,offset_y),textcoords="offset points",
                                         bbox=dict(boxstyle="round", fc="w"),
                                         arrowprops=dict(arrowstyle="->"))
            self_annots[i].set_visible(False)

        # plot all other chords
        for j in range(i):
            cend = chord_colors[j]

            start1, end1 = pos[(i, j)]
            start2, end2 = pos[(j, i)]

            if mat[i, j] > 0 or mat[j, i] > 0:
                connector_patches[(i, j)] = chord_arc(start1, end1, start2, end2, radius=1 - width - gap,
                                                      chordwidth=chordwidth, color=chord_color, cend=cend,
                                                      alpha=alpha, ax=ax, use_gradient=use_gradient)
                rotate = rotate_names[i]
                if rotate:
                    angle  = np.average(arc[i])
                    rotate = 90
                    if 90 < angle < 180 or 270 < angle:
                        rotate = -90

                #mean1 = (start1 + end1) /2
                mean1 = end1
                offset_x1 = 20
                offset_y1 = 20
                if 90 < mean1 and mean1 < 270:
                    offset_x1 *= -1
                if 180 < mean1 and mean1 < 360:
                    offset_y1 *= -1

                mean1 *= np.pi/180.
                x1, y1 = polar2xy(1 - width - (gap), mean1)
                
                connector_annots[i,j] = ax.annotate(str(int(orig_mat[i, j]*100))+"%", xy=(x1,y1), xytext=(offset_x1,offset_y1),textcoords="offset points",
                                        bbox=dict(boxstyle="round", fc="w"),
                                        arrowprops=dict(arrowstyle="->"))
                connector_annots[i,j].set_visible(False)

                #mean2 = (start2 + end2) /2
                mean2 = end2
                offset_x2 = 20
                offset_y2 = 20
                if 90 < mean2 and mean2 < 270:
                    offset_x2 *= -1
                if 180 < mean2 and mean2 < 360:
                    offset_y2 *= -1
                
                mean2 *= np.pi/180.
                x2, y2 = polar2xy(1 - width - (gap), mean2)

                connector_annots[j,i] = ax.annotate(str(int(orig_mat[j,i]*100))+"%", xy=(x2,y2), xytext=(offset_x2,offset_y2),textcoords="offset points",
                                            bbox=dict(boxstyle="round", fc="w"),
                                            arrowprops=dict(arrowstyle="->"))
                connector_annots[j,i].set_visible(False)

    # add names if necessary
    if names is not None:
        assert len(names) == num_nodes, "One name per node is required."

        prop = {
            "fontsize": kwargs.get("fontsize", 16*0.8),
            "ha": "center",
            "va": "center",
            "rotation_mode": "anchor"
        }

        for i, (pos, name, r) in enumerate(zip(nodePos, names, rotation)):
            rotate = rotate_names[i]
            pp = prop.copy()

            if rotate:
                angle  = np.average(arc[i])
                rotate = 90

                if 90 < angle < 180 or 270 < angle:
                    rotate = -90

                if 90 < angle < 270:
                    pp["ha"] = "left"
                else:
                    pp["ha"] = "right"
            elif r:
                pp["va"] = "bottom"
            else:
                pp["va"] = "top"

            outer_names[i] = ax.text(pos[0], pos[1], name, rotation=pos[2] + rotate, **pp)

            if name_images is not None and name_images[i] is not None:
                mean = (arc[i][0] + arc[i][1]) /2
                mean *= np.pi/180.
                if pos[0] < 0:
                    x = pos[0] + abs(pos[0])*0.5-1
                else:
                    x = pos[0] + 1-pos[0]*0.5
                y = pos[1]
                outer_images[i] = ax.add_artist( #ax can be added image as artist.
                                                AnnotationBbox(
                                                    OffsetImage(name_images[i], zoom=0.3)
                                                    , xy=(pos[0], pos[1])
                                                    , xybox=(x, y)
                                                    , arrowprops=dict(arrowstyle="->")
                                                    , frameon=False, annotation_clip=False)
                                                )
                if arc[i][1] - arc[i][0] < 15:
                    outer_images[i].set_visible(False)

            if outer_circle is not None:
                prop = {
                            "fontsize": kwargs.get("fontsize", 16*0.8),
                            "ha": "center",
                            "va": "center",
                            "rotation_mode": "anchor"
                        }
                pp = prop.copy()
                mean = (arc[i][0] + arc[i][1]) /2
                mean *= np.pi/180.
                x, y = polar2xy(1-(width/3), mean)
                ax.text(x, y, orig_outer_circle[i], rotation=pos[2], **pp)

    # configure axis
    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-1.1, 1.1)

    ax.set_aspect(1)
    ax.axis('off')

    plt.tight_layout()

    selected_outer_patch = 0
    SelectArc(0)
    

    _.canvas.mpl_connect('button_press_event', OnClick)
    _.canvas.mpl_connect('motion_notify_event', OnHover)

    if show:
        plt.show()

    return nodePos


# ------------ #
# Subfunctions #
# ------------ #

def initial_path(start, end, radius, width, factor=4/3):
    ''' First 16 vertices and 15 instructions are the same for everyone '''
    if start > end:
        start, end = end, start

    start *= np.pi/180.
    end   *= np.pi/180.

    # optimal distance to the control points
    # https://stackoverflow.com/questions/1734745/
    # how-to-create-circle-with-b%C3%A9zier-curves
    # use 16-vertex curves (4 quadratic Beziers which accounts for worst case
    # scenario of 360 degrees)
    inner = radius*(1-width)
    opt   = factor * np.tan((end-start)/ 16.) * radius
    inter1 = start*(3./4.)+end*(1./4.)
    inter2 = start*(2./4.)+end*(2./4.)
    inter3 = start*(1./4.)+end*(3./4.)

    verts = [
        polar2xy(radius, start),
        polar2xy(radius, start) + polar2xy(opt, start+0.5*np.pi),
        polar2xy(radius, inter1) + polar2xy(opt, inter1-0.5*np.pi),
        polar2xy(radius, inter1),
        polar2xy(radius, inter1),
        polar2xy(radius, inter1) + polar2xy(opt, inter1+0.5*np.pi),
        polar2xy(radius, inter2) + polar2xy(opt, inter2-0.5*np.pi),
        polar2xy(radius, inter2),
        polar2xy(radius, inter2),
        polar2xy(radius, inter2) + polar2xy(opt, inter2+0.5*np.pi),
        polar2xy(radius, inter3) + polar2xy(opt, inter3-0.5*np.pi),
        polar2xy(radius, inter3),
        polar2xy(radius, inter3),
        polar2xy(radius, inter3) + polar2xy(opt, inter3+0.5*np.pi),
        polar2xy(radius, end) + polar2xy(opt, end-0.5*np.pi),
        polar2xy(radius, end)
    ]

    codes = [
        Path.MOVETO,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.LINETO,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.LINETO,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.LINETO,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
    ]

    return start, end, verts, codes


def ideogram_arc(start, end, radius=1., width=0.2, color="r", alpha=0.7,
                 ax=None):
    '''
    Draw an arc symbolizing a region of the chord diagram.

    Parameters
    ----------
    start : float (degree in 0, 360)
        Starting degree.
    end : float (degree in 0, 360)
        Final degree.
    radius : float, optional (default: 1)
        External radius of the arc.
    width : float, optional (default: 0.2)
        Width of the arc.
    ax : matplotlib axis, optional (default: not plotted)
        Axis on which the arc should be plotted.
    color : valid matplotlib color, optional (default: "r")
        Color of the arc.

    Returns
    -------
    verts, codes : lists
        Vertices and path instructions to draw the shape.
    '''
    start, end, verts, codes = initial_path(start, end, radius, width)

    opt    = 4./3. * np.tan((end-start)/ 16.) * radius
    inner  = radius*(1-width)
    inter1 = start*(3./4.) + end*(1./4.)
    inter2 = start*(2./4.) + end*(2./4.)
    inter3 = start*(1./4.) + end*(3./4.)

    verts += [
        polar2xy(inner, end),
        polar2xy(inner, end) + polar2xy(opt*(1-width), end-0.5*np.pi),
        polar2xy(inner, inter3) + polar2xy(opt*(1-width), inter3+0.5*np.pi),
        polar2xy(inner, inter3),
        polar2xy(inner, inter3),
        polar2xy(inner, inter3) + polar2xy(opt*(1-width), inter3-0.5*np.pi),
        polar2xy(inner, inter2) + polar2xy(opt*(1-width), inter2+0.5*np.pi),
        polar2xy(inner, inter2),
        polar2xy(inner, inter2),
        polar2xy(inner, inter2) + polar2xy(opt*(1-width), inter2-0.5*np.pi),
        polar2xy(inner, inter1) + polar2xy(opt*(1-width), inter1+0.5*np.pi),
        polar2xy(inner, inter1),
        polar2xy(inner, inter1),
        polar2xy(inner, inter1) + polar2xy(opt*(1-width), inter1-0.5*np.pi),
        polar2xy(inner, start) + polar2xy(opt*(1-width), start+0.5*np.pi),
        polar2xy(inner, start),
        polar2xy(radius, start),
    ]

    codes += [
        Path.LINETO,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.LINETO,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.LINETO,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.LINETO,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.CLOSEPOLY,
    ]

    if ax is not None:
        path  = Path(verts, codes)
        patch = patches.PathPatch(path, facecolor=color, alpha=alpha,
                                  edgecolor=color, lw=LW)
        ax.add_patch(patch)

    return patch


def chord_arc(start1, end1, start2, end2, radius=1.0, pad=2, chordwidth=0.7,
              ax=None, color="r", cend="r", alpha=0.7, use_gradient=False):
    '''
    Draw a chord between two regions (arcs) of the chord diagram.

    Parameters
    ----------
    start1 : float (degree in 0, 360)
        Starting degree.
    end1 : float (degree in 0, 360)
        Final degree.
    start2 : float (degree in 0, 360)
        Starting degree.
    end2 : float (degree in 0, 360)
        Final degree.
    radius : float, optional (default: 1)
        External radius of the arc.
    chordwidth : float, optional (default: 0.2)
        Width of the chord.
    ax : matplotlib axis, optional (default: not plotted)
        Axis on which the chord should be plotted.
    color : valid matplotlib color, optional (default: "r")
        Color of the chord or of its beginning if `use_gradient` is True.
    cend : valid matplotlib color, optional (default: "r")
        Color of the end of the chord if `use_gradient` is True.
    alpha : float, optional (default: 0.7)
        Opacity of the chord.
    use_gradient : bool, optional (default: False)
        Whether a gradient should be use so that chord extremities have the
        same color as the arc they belong to.

    Returns
    -------
    verts, codes : lists
        Vertices and path instructions to draw the shape.
    '''
    chordwidth2 = chordwidth

    dtheta1 = min((start1 - end2) % 360, (end2 - start1) % 360)
    dtheta2 = min((end1 - start2) % 360, (start2 - end1) % 360)

    start1, end1, verts, codes = initial_path(start1, end1, radius, chordwidth)

    start2, end2, verts2, _ = initial_path(start2, end2, radius, chordwidth)

    chordwidth2 *= np.clip(0.4 + (dtheta1 - 2*pad) / (15*pad), 0.2, 1)

    chordwidth *= np.clip(0.4 + (dtheta2 - 2*pad) / (15*pad), 0.2, 1)

    rchord  = radius * (1-chordwidth)
    rchord2 = radius * (1-chordwidth2)

    verts += [polar2xy(rchord, end1), polar2xy(rchord, start2)] + verts2

    verts += [
        polar2xy(rchord2, end2),
        polar2xy(rchord2, start1),
        polar2xy(radius, start1),
    ]

    codes += [
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.LINETO,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.LINETO,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.LINETO,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
    ]

    if ax is not None:
        path = Path(verts, codes)

        if use_gradient:
            # find the start and end points of the gradient
            points, min_angle = None, None

            if dtheta1 < dtheta2:
                points = [
                    polar2xy(radius, start1),
                    polar2xy(radius, end2),
                ]

                min_angle = dtheta1
            else:
                points = [
                    polar2xy(radius, end1),
                    polar2xy(radius, start2),
                ]

                min_angle = dtheta1

            # make the patch
            patch = patches.PathPatch(path, facecolor="none",
                                      edgecolor="none", lw=LW)
            ax.add_patch(patch)  # this is required to clip the gradient

            # make the grid
            x = y = np.linspace(-1, 1, 100)
            meshgrid = np.meshgrid(x, y)

            im = gradient(points[0], points[1], min_angle, color, cend, meshgrid,
                     patch, ax, alpha)
        else:
            patch = patches.PathPatch(path, facecolor=color, alpha=alpha,
                                      edgecolor=color, lw=LW)

            idx = 16

            ax.add_patch(patch)
            im = patch

    return (patch,im)


def self_chord_arc(start, end, radius=1.0, chordwidth=0.7, ax=None,
                   color=(1,0,0), alpha=0.7):
    start, end, verts, codes = initial_path(start, end, radius, chordwidth)

    rchord = radius * (1 - chordwidth)

    verts += [
        polar2xy(rchord, end),
        polar2xy(rchord, start),
        polar2xy(radius, start),
    ]

    codes += [
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
    ]

    if ax is not None:
        path  = Path(verts, codes)
        patch = patches.PathPatch(path, facecolor=color, alpha=alpha,
                                  edgecolor=color, lw=LW)
        ax.add_patch(patch)

    return patch
