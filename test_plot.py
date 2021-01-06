###############################################################################
#
# Copyright (C) 2017
# ASTRON (Netherlands Institute for Radio Astronomy) <http://www.astron.nl/>
# P.O.Box 2, 7990 AA Dwingeloo, The Netherlands
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

"""Test plot utilities
   
"""

################################################################################
# System imports
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import common as cm

################################################################################
# Functions

class Testplot:
  
    def __init__(self, verbosity=11):
        self.verbosity = verbosity                 # Verbosity threshold used to decide whether to show the plot or not
        self.figNr = 1
        
    def _represent_array(self, arr, representation='', offset=0):
        """Represent arr conform representation.
        
        For dB* representations optionally add offset > 0 to avoid log(0).
        """
        if representation=='dB':
            arr = 10*np.log10(np.abs(arr)+offset)
        elif representation=='dBvolt':
            arr = 20*np.log10(np.abs(arr)+offset)
        elif representation=='real':
            arr = arr.real
        elif representation=='imag':
            arr = arr.imag
        elif representation=='abs':
            arr = np.abs(arr)
        elif representation=='rad':
            arr = np.angle(arr)
        elif representation=='deg':
            arr = np.angle(arr, deg=True)
        return arr
        

    def plot_one_dimensional_list(self, vLevel, L, Lx=None, representation='', offset=0, Title='', Xlabel='', Ylabel='', Xlim=None, Ylim=None, lineFormat=None):
        """Plot list L[col] with labels
        
        . vLevel         = verbosity level, only show plot if vLevel <= self.verbosity
        . L              = the list
        . Lx             = when None then use L index as x-axis, else use Lx to define points on x-axis
        . representation = define data representation
        . offset         = use offset>0 to avoid log(0) in dB* representations
        . lineFormat     = format string for line color, line style and line marker, see help(plt.plot)
        """
        if vLevel <= self.verbosity:
            if Lx is None:
                Lx = np.arange(len(L))
            Ly = np.array(L)
            Ly = self._represent_array(Ly, representation, offset)
            plt.figure(self.figNr)
            if lineFormat==None:
                plt.plot(Lx, Ly)
            else:
                plt.plot(Lx, Ly, lineFormat)
            if Xlim!=None:
                plt.xlim(Xlim)
            if Ylim!=None:
                plt.ylim(Ylim)
            plt.title(Title)
            plt.xlabel(Xlabel)
            if representation == '':
                plt.ylabel(Ylabel)
            else:
                plt.ylabel(Ylabel + ' (%s)' % representation)
            plt.grid(True)
            plt.draw()   # Call draw to fix e.g. colormap settings for this figure, independent of other figures
            self.figNr += 1
        
        
    def plot_two_dimensional_list(self, vLevel, A, Alegend=None, Lx=None, representation='', offset=0, Title='', Xlabel='', Ylabel='', Xlim=None, Ylim=None, lineFormats=None):
        """Plot two dimensional list A[row][col] as one line per row, with labels
        
        . vLevel         = verbosity level, only show plot if vLevel <= self.verbosity
        . A              = the two dimensional list
        . Alegend        = when None then no legend, else list of line label strings per row A
        . Lx             = when None then use A col index as x-axis, else use Lx to define points on x-axis
        . representation = define data representation
        . offset         = use offset>0 to avoid log(0) in dB* representations
        . lineFormats    = list of format strings for line color, line style and line marker, see help(plt.plot)
        """
        if vLevel <= self.verbosity:
            Ay = np.array(A)
            Ay = self._represent_array(Ay, representation, offset)
            plt.figure(self.figNr)
            for li,Ly in enumerate(Ay):
                if Lx is None:
                    Lx = np.arange(len(Ly))
                if lineFormats==None:
                    if Alegend==None:
                        plt.plot(Lx, Ly)
                    else:
                        plt.plot(Lx, Ly, label=Alegend[li])
                else:
                    if Alegend==None:
                        plt.plot(Lx, Ly, lineFormats[li])
                    else:
                        plt.plot(Lx, Ly, lineFormats[li], label=Alegend[li])
                li += 1
            if Xlim!=None:
                plt.xlim(Xlim)
            if Ylim!=None:
                plt.ylim(Ylim)
            plt.title(Title)
            plt.xlabel(Xlabel)
            if representation == '':
                plt.ylabel(Ylabel)
            else:
                plt.ylabel(Ylabel + ' (%s)' % representation)
            if Alegend!=None:
                plt.legend(loc='best')
            plt.grid(True)
            plt.draw()   # Call draw to fix e.g. colormap settings for this figure, independent of other figures
            self.figNr += 1
            

    def plot_three_dimensional_list(self, vLevel, M, Aindices=None, Lx=None, representation='', offset=0, order='', Title='', Xlabel='', Ylabel='', Xlim=None, Ylim=None):
        """Plot a list of two dimensional lists into a list of subplots
        
        M[a][row][col] is a list of two dimensional lists A and image each A[row][col] per row in a subplot, with labels and colorbar
        
        . vLevel         = verbosity level, only show plot if vLevel <= self.verbosity
        . M              = the three dimensional list, which is a list of two dimensional lists A
        . Aindices       = indices of A in M
        . Lx             = when None then use A col index as x-axis, else use Lx to define points on x-axis
        . representation = define data representation
        . offset         = use offset>0 to avoid log(0) in dB* representations
        . order          = order of the subplots: 'rightleft', 'leftright', 'bottomup' or default 'topdown'
        
        Remarks:
        . The subplot number counts from 1 instead of from 0
        . For example subplot(number of rows = 3, number of colums = 2 , subplot number) yields subplot numbers:
              1   2 
              3   4
              5   6
        """
        if vLevel <= self.verbosity:
            Ma = np.array(M)
            Na = len(M)
            if Aindices == None:
                Aindices = list(range(Na))
            plt.figure(self.figNr)
            
            for ai, Ay in enumerate(Ma):
                Ay = self._represent_array(Ay, representation, offset)
                
                aI = ai + 1
                if order=='rightleft':   
                    plt.subplot(1, Na, Na-ai)
                elif order=='leftright':
                    plt.subplot(1, Na, aI)
                elif order=='bottomup':
                    plt.subplot(Na, 1, Na-ai)
                else:  # default: 'topdown':
                    plt.subplot(Na, 1, aI)
                    
                for Ly in Ay:
                    if Lx is None:
                        Lx = np.arange(len(Ly))
                    plt.plot(Lx, Ly)
                if Xlim!=None:
                    plt.xlim(Xlim)
                if Ylim!=None:
                    plt.ylim(Ylim)
                plt.title(Title + ' [%s]' % Aindices[ai])
                plt.xlabel(Xlabel)
                if representation == '':
                    plt.ylabel(Ylabel)
                else:
                    plt.ylabel(Ylabel + ' (%s)' % representation)
                plt.grid(True)
                
            plt.draw()   # Call draw to fix e.g. colormap settings for this figure, independent of other figures
            self.figNr += 1

            
    def _imshow_with_colorbar(self, plt, A, cmap, extent=None):
        showIt = len(cm.unique(cm.flatten(A))) > 1  # Somehow plt.colorbar() in Python 2.7.6 gives RuntimeWarning when all elements in A are equal, therefore only plot A if it has a different values
        #showIt = True                               # or just ignore the RuntimeWarning
        if showIt:
            if False:
                # with aspect='auto' the image fills the figure and the colorbar has the same size, so no need to use make_axes_locatable()
                plt.imshow(A, origin='lower', interpolation='none', aspect='auto', cmap=cmap, extent=extent)
                plt.colorbar()
            else:
                # with fixed aspect ratio, the colorbar size can be matched to the image height using make_axes_locatable()
                ax = plt.gca()    # gca = get current axes
                im = ax.imshow(A, origin='lower', interpolation='none', aspect='auto', cmap=cmap, extent=extent)
                divider = make_axes_locatable(ax)
                cax = divider.append_axes("right", size='5%', pad=0.1)
                plt.colorbar(im, cax=cax)
        
            
    def image_two_dimensional_list(self, vLevel, A, representation='', offset=0, transpose=False, grid=False, cmap='jet', Title='', Xlabel='', Ylabel='', extent=None):
        """Image two dimensional list A[row][col] per row, with labels and colorbar
        
        . vLevel         = verbosity level, only show plot if vLevel <= self.verbosity
        . A              = the two dimensional list
        . representation = define data representation
        . offset         = use offset>0 to avoid log(0) in dB* representations
        . transpose      = when True plot transpose of A
        . cmap           = colormap, default 'jet', use e.g. 'gray' or reverse 'gray_r' for on/off data
        . extent         = use extent [left, right, bottom, top] as X and Y range of list A, or use extent=None to show the index ranges of list A
        """
        if vLevel <= self.verbosity:
            Ay = np.array(A)
            if transpose:
                Ay = np.transpose(Ay)
            Ay = self._represent_array(Ay, representation, offset)
            plt.figure(self.figNr)
            plt.title(Title)
            plt.xlabel(Xlabel)
            if representation == '':
                plt.ylabel(Ylabel)
            else:
                plt.ylabel(Ylabel + ' (%s)' % representation)
            plt.grid(grid)
            self._imshow_with_colorbar(plt, Ay, cmap, extent)
            plt.draw()   # Call draw to fix e.g. colormap settings for this figure, independent of other figures
            self.figNr += 1

         
    def image_three_dimensional_list(self, vLevel, M, Aindices=None, representation='', offset=0, transpose=False, order='', grid=False, cmap='jet', Title='', Xlabel='', Ylabel='', extent=None):
        """Image a list of two dimensional lists into a list of subplots
        
        M[a][row][col] is a list of two dimensional lists A and image each A[row][col] per row in a subplot, with labels and colorbar
        
        . vLevel         = verbosity level, only show plot if vLevel <= self.verbosity
        . M              = the three dimensional list, which is a list of two dimensional lists A
        . Aindices       = indices of A in M
        . representation = define data representation
        . offset         = use offset>0 to avoid log(0) in dB* representations
        . transpose      = when True plot transpose of A
        . order          = order of the subplots: 'rightleft', 'leftright', 'bottomup' or default 'topdown'
        . cmap           = colormap, default 'jet', use e.g. 'gray' or reverse 'gray_r' for on/off data
        . extent         = use extent [left, right, bottom, top] as X and Y range of list A, or use extent=None to show the index ranges of list A
        
        Remarks:
        . The subplot number counts from 1 instead of from 0
        . For example subplot(number of rows = 3, number of colums = 2 , subplot number) yields subplot numbers:
              1   2 
              3   4
              5   6
        """
        if vLevel <= self.verbosity:
            Ma = np.array(M)
            Na = len(M)
            if Aindices == None:
                Aindices = list(range(Na))
            plt.figure(self.figNr)
            
            for ai, Ay in enumerate(Ma):
                if transpose:
                    Ay = np.transpose(Ay)
                Ay = self._represent_array(Ay, representation, offset)
                
                aI = ai + 1
                if order=='rightleft':   
                    plt.subplot(1, Na, Na-ai)
                elif order=='leftright':
                    plt.subplot(1, Na, aI)
                elif order=='bottomup':
                    plt.subplot(Na, 1, Na-ai)
                else:  # default: 'topdown':
                    plt.subplot(Na, 1, aI)
                    
                plt.title(Title + ' [%s]' % Aindices[ai])
                plt.xlabel(Xlabel)
                if representation == '':
                    plt.ylabel(Ylabel)
                else:
                    plt.ylabel(Ylabel + ' (%s)' % representation)
                plt.grid(grid)
                
                self._imshow_with_colorbar(plt, Ay, cmap, extent)
                
            plt.tight_layout()   # not realy necessary, because there is sufficient space between subplots when figure is manually enlarged to full screen
            plt.draw()   # Call draw to fix e.g. colormap settings for this figure, independent of other figures
            self.figNr += 1

        
    def save_figure(self, figName, figNr=None):
        """Save figure to figName.png file
        
           Must call plt.savefig() before plt.show(), because otherwise the file is empty.
        """
        if figNr==None:
            plt.figure(self.figNr-1)   # plot last figure
        else:
            plt.figure(figNr)          # plot selected figure
        plt.savefig(figName)


    def plot_ion(self):
        """Equivalent to interactive mode plt.ion(). Shows plot immediately on the screen and keeps the plot while the script continues."""
        plt.ion()

    def plot_ioff(self):
        """Equivalent non-interactive mode plt.iof(). Requires using plt.show() to show plot on the screen. The script stalls until the user manually closes the plot."""
        plt.ioff()
            
    def show_plots(self):
        """Show all plots on the screen and wait until they are closed again manually."""
        plt.show()
         
    def close_plots(self):
        """Close all plots."""
        plt.close('all')
        

if __name__ == '__main__':
    tc = Testplot()
     
    Nx = 20
    Lx = list(range(Nx))
    L = cm.create_multidimensional_list([Nx], 0)    # = [0] * Nx
    for x in Lx:
        L[x] = x * x

    Ny = 10
    A = cm.create_multidimensional_list([Ny, Nx], 0)
    for y in range(Ny):
        for x in Lx:
            A[y][x] = (y+1)*x*x

    Na = 4
    M = cm.create_multidimensional_list([Na, Ny, Nx], 0)
    Aindices = []
    for a in range(Na):
        Aindices.append(a*a)
        for y in range(Ny):
            for x in Lx:
                M[a][y][x] = (y+1)*x*x + a*x
    
    Xlim = None
    Ylim = None # [0, 1000]
    
    # Single line plot
    tc.plot_one_dimensional_list(3, L, Title='Plot 1-D list', Xlabel='Index', Ylabel='Data', Xlim=Xlim, Ylim=Ylim, lineFormat='b--')

    # Multi line plot
    tc.plot_two_dimensional_list(3, A, Title='Plot 2-D list', Xlabel='Index', Ylabel='Data', Xlim=Xlim, Ylim=Ylim)

    # Single 2-D image plot
    grid = False  # optional image grid
    
    tc.image_two_dimensional_list(3, A, grid=grid, Title='Image 2-D list with default colormap', Xlabel='Index', Ylabel='Data') 
    tc.image_two_dimensional_list(3, A, grid=grid, representation='dB', cmap='gray_r', Title='Image 2-D list with reverse gray colormap', Xlabel='Index', Ylabel='Data')
    
    # Multi 2-D image subplots
    tc.image_three_dimensional_list(3, M, Aindices=Aindices, order='topdown', grid=grid, Title='Image 3-D top-down', Xlabel='Index', Ylabel='Data')
    tc.image_three_dimensional_list(3, M, Aindices=Aindices, order='leftright', grid=grid, Title='Image 3-D left-right', Xlabel='Index', Ylabel='Data')
    tc.image_three_dimensional_list(3, M, Aindices=Aindices, representation='dB', order='bottomup', grid=grid, Title='Image 3-D bottom-up', Xlabel='Index', Ylabel='Data')
    tc.image_three_dimensional_list(3, M, Aindices=Aindices, order='rightleft', grid=grid, Title='Image 3-D right-left', Xlabel='Index', Ylabel='Data')
    
    # Save figure
    tc.save_figure('test_plot_1.png', 1)   # first figure
    tc.save_figure('test_plot_last.png')   # last figure
    
    # Plot all figures
    tc.show_plots()

