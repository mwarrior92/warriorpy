import cPickle as pickle
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.ticker import FormatStrFormatter, ScalarFormatter, FuncFormatter
import numpy

def to_percent(y, position):
    # Ignore the passed in position. This has the effect of scaling the default
    # tick locations.
    s = str(100 * y)

    # The percent symbol needs escaping in latex
    if mpl.rcParams['text.usetex'] is True:
        return s + r'$\%$'
    else:
        return s + '%'


def x_to_percent(ax):
        formatter = FuncFormatter(to_percent)
        ax.xaxis.set_major_formatter(formatter)


def y_to_percent(ax):
        formatter = FuncFormatter(to_percent)
        ax.yaxis.set_major_formatter(formatter)


def saveme(ax, fig, filename):
    pickle.dump(ax, open(filename+'.axp', 'w'))
    pickle.dump(fig, open(filename+'.figp', 'w'))
    fig.savefig(filename+'.png')
    fig.savefig(filename+'.pdf')


def to_percent(y, position):
    # Ignore the passed in position. This has the effect of scaling the default
    # tick locations.
    s = str(100 * y)

    # The percent symbol needs escaping in latex
    if mpl.rcParams['text.usetex'] is True:
        return s + r'$\%$'
    else:
        return s + '%'


def set_dim(fig, ax, xlim=None, ylim=None, xpadding=False, ypadding=False, xdim=6.5, ydim=3,
            percx=False, percy=False, ceilit=False, xlog=False, ylog=False, xnosci=False, ynosci=False):
    if xlim is None:
        ax.autoscale(axis='x', tight=True)
        xlim = ax.get_xlim()
    elif xlim[0] is None:
        a = ax.get_xlim()
        xlim = [a[0], xlim[1]]
        plt.xlim(xlim)
    elif xlim[1] is None:
        b = ax.get_xlim()
        xlim = [xlim[0], b[1]]
        plt.xlim(xlim)
    else:
        plt.xlim(xlim)
    if xpadding:
        xlim = ax.get_xlim()
        if ceilit:
            padding = numpy.ceil((xlim[1]-xlim[0])*0.05)
        else:
            padding = (xlim[1] - xlim[0]) * 0.05
        if xlim[0] == 0:
            plt.xlim([xlim[0], xlim[1]+padding])
        else:
            plt.xlim([xlim[0]-padding, xlim[1]+padding])
    if ylim is None:
        ax.autoscale(axis='y', tight=True)
        ylim = ax.get_ylim()
    elif ylim[0] is None:
        a = ax.get_ylim()
        ylim = [a[0], ylim[1]]
        plt.ylim(ylim)
    elif ylim[1] is None:
        b = ax.get_ylim()
        ylim = [ylim[0], b[1]]
        plt.ylim(ylim)
    else:
        plt.ylim(ylim)
    if ypadding:
        ylim = ax.get_ylim()
        if ceilit:
            padding = numpy.ceil((ylim[1]-ylim[0])*0.05)
        else:
            padding = (ylim[1] - ylim[0]) * 0.05
        if ylim[0] == 0:
            plt.ylim([ylim[0], ylim[1]+padding])
        else:
            plt.ylim([ylim[0]-padding, ylim[1]+padding])
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    if percx:
        plt.xlim([0, xlim[1]])
        formatter = FuncFormatter(to_percent)
        ax.xaxis.set_major_formatter(formatter)
        ax.xaxis.set_ticks(numpy.arange(0, xlim[1], 1))
    if percy:
        plt.ylim([0, ylim[1]])
        formatter = FuncFormatter(to_percent)
        ax.yaxis.set_major_formatter(formatter)
        ax.yaxis.set_ticks(numpy.arange(0, ylim[1], 0.1))
    if xlog:
        ax.set_xscale('log')
    if ylog:
        ax.set_yscale('log')
    if xnosci:
        ax.xaxis.set_major_formatter(FormatStrFormatter('%.0f'))
    if ynosci:
        ax.yaxis.set_major_formatter(FormatStrFormatter('%.0f'))
    fig.set_figheight(ydim)
    fig.set_figwidth(xdim)


def legend_setup(ax, numcol=1, legendpos='', outside=False, handlelen=3):
    loc = 4
    if not outside:
        if 'left' in legendpos:
            if 'top' in legendpos:
                loc = 2
            elif 'bottom' in legendpos or 'lower' in legendpos:
                loc = 3
            else:
                loc = 6
        elif 'right' in legendpos:
            if 'top' in legendpos or 'upper' in legendpos:
                loc = 1
            elif 'bottom' in legendpos or 'lower' in legendpos:
                loc = 4
            else:
                loc = 7
        elif 'bottom' in legendpos or 'lower' in legendpos:
            loc = 8
        elif 'top' in legendpos or 'upper' in legendpos:
            loc = 9
        elif 'center' in legendpos or 'middle' in legendpos:
            loc = 10
        else:
            loc = 0
    else:
        if 'left' in legendpos:
            loc = 7
            h = -0.05
            v = 0.5
        elif 'right' in legendpos:
            loc = 6
            h = 1.035
            v = 0.5
        elif 'bottom' in legendpos or 'lower' in legendpos:
            loc = 9
            h = 0.5
            v = -0.1
        elif 'top' in legendpos or 'upper' in legendpos:
            loc = 8
            h = 0.5
            v = 1.035

    line_handles, line_labels = ax.get_legend_handles_labels()
    if outside:
        return ax.legend(line_handles, line_labels, ncol=numcol, loc=loc, bbox_to_anchor=(h, v), numpoints=1, scatterpoints=1,
                  framealpha=0.5, handlelength=handlelen)
    else:
        return ax.legend(line_handles, line_labels, ncol=numcol, loc=loc, numpoints=1, framealpha=0.5, handlelength=handlelen,
                  scatterpoints=1)
