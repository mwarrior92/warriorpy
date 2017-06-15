import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.ticker import FormatStrFormatter, ScalarFormatter, FuncFormatter

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
