###############################################################################
#
# Copyright (C) 2012
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

"""Test logging utilities
   
* Provide logging with standardized prefixes:
  . time                     : self, if notime = 0
  . verbosity level          : self, if noVLevel = 0
  . test case ID             : self, if noTestId = 0
  . message text             : argument msgString, the actual text to log
* All append_log statements that have verbosity level equal or lower than the
  test case verbosity level will get logged.
* The logging gets output to the stdio and to a file if a file name is provided.
* It is also possible to append other files to the test logging file.
* Best practise is to use the following verbosity levels for the append_log
  argument:

  -v 0  Log test result
  -v 1  Log test title
  -v 2  Log errors
  -v 3  Log info
  -v 4  Log error details
  -v 5  Log info details
  -v 6  Log debug
  -v 7  Log debug details
"""

################################################################################
# System imports
import sys
import time
import common as cm

################################################################################
# Functions

class Testlog:
  
    V_RESULT        = 0
    V_TITLE         = 1
    V_ERRORS        = 2
    V_INFO          = 3
    V_ERROR_DETAILS = 4
    V_INFO_DETAILS  = 5
    V_DEBUG         = 6
    V_DEBUG_DETAILS = 7

    _logName=None

    def __init__(self, verbosity=11, testId='', sectionId='', logName=None):
        self.verbosity = verbosity                 # Verbosity threshold used by append_log() to decide whether to log the input string or not
        self._testId = testId                      # Test ID that optionally gets used as prefix in append_log line
        self._sectionId = sectionId                # Section ID that optionally gets used as prefix in append_log line
        self._logName = logName                    # Name for the file that will contain the append_log 
        if self._logName != None:
            try:
                self._logFile = open(self._logName,'w')
            except IOError:
                print('ERROR : Can not open log file %s' % self._logName)
                
    def __del__(self):
        if self._logName != None:
            self.close_log()
      
    def close_log(self):
        if self._logName != None:
            self._logFile.close()
    
    # The testId can should remain fixed at __init__, but the user can change the sectionId during the execution
    def set_section_id(self, sectionId):
        self._sectionId = sectionId
        
    def verbose_levels(self):
        return "0=result; 1=title; 2=errors; 3=info; 4=error details; 5=info details; 6=debug; 7=debug details"

    # Print the message string and append it to the test log file in the Testlog style
    def append_log(self, vLevel, msgString, noTime=0, noVLevel=0, noTestId=0, noSectionId=0):
        if vLevel <= self.verbosity:
            txt = ''
            if noTime == 0:
                t = time.localtime()
                txt = txt + '[%d:%02d:%02d %02d:%02d:%02d]' % (t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)
            if noVLevel == 0:
                txt = txt + ' - (%d) ' % vLevel
            if noTestId == 0:
                txt = txt + self._testId
            if noSectionId == 0:
                txt = txt + self._sectionId
            txt = txt + msgString
            print(txt)
            #sys.stdout.flush()
            if self._logName != None:
                self._logFile.write(txt + '\n')
    
    # Print the repeat message string at regular intervals and append it to the test log file in the Testlog style
    def append_log_rep(self, vLevel, rep, nofRep, nofLog=5, noTime=0, noVLevel=0, noTestId=0, noSectionId=0):
        if nofRep < nofLog:
            logInterval = 1
        else:
            logInterval = nofRep//nofLog
        if rep%logInterval==0 or rep==nofRep-1:
            self.append_log(3, 'Rep-%d' % rep)


    # Print the contents of an array to the test log file
    def append_log_data(self, vLevel, prefixStr, data, radix='dec', dataWidth=8, nofColumns=16, rulers=False, noTime=0, noVLevel=0, noTestId=0, noSectionId=0):
        if vLevel <= self.verbosity:
            r = 0
            columnWidth = dataWidth + 1  # use 1 space between columns
            if rulers:
                rowStr = 'Col:'
                for i in range(nofColumns):
                    rowStr += '%*d' % (columnWidth, i)
                self.append_log(vLevel, prefixStr + rowStr, noTime, noVLevel, noTestId, noSectionId)
                self.append_log(vLevel, prefixStr + 'Row:', noTime, noVLevel, noTestId, noSectionId)
                rowStr = prefixStr + ('%-4d' % r)
            else:
                rowStr = prefixStr
                
            k = 0

            # Make sure data is a list, otherwise the following fails
            if cm.depth(data)==0:
                data=cm.listify(data)

            n = len(data)
            for i in range(n):
                if radix=='uns': rowStr += ' %*d' % (dataWidth, data[i])
                if radix=='dec': rowStr += ' %*d' % (dataWidth, data[i])
                if radix=='hex': rowStr += ' %0*x' % (dataWidth, data[i])
                if k < nofColumns-1:
                    k = k + 1
                else:
                    self.append_log(vLevel, prefixStr + rowStr, noTime, noVLevel, noTestId, noSectionId)
                    rowStr = prefixStr
                    r = r + 1
                    if rulers:
                        rowStr += ('%-4d' % r)
                    k = 0
            if k!=0:
                self.append_log(vLevel, prefixStr + rowStr, noTime, noVLevel, noTestId, noSectionId)
        
    
    def data_to_string(self, data, dataWidth=4, dataLeft=False, fractionWidth=2, fractionExponent=False):
        """Print data to string with length dataWidth + 1 white space
        
        Default print the data as %s string to support any type
        If the data is float or complex then print it using fraction notation when
        fractionExponent=False or using exponent notation when fractionExponent=True.
        The fractionWidth specifies the width of the floating point value.
        The data is printed left or right aligned dependent on dataLeft.
        For all data types the returned data string has length dataWidth + 1 for a
        white space such that it can be used as a fixed size element string when 
        printing a row of data on a line.

        . data             = the data, can be float complex or other e.g. int, string, tuple
        . dataWidth        = width of the printed data string
        . dataLeft         = when True then left align the data in the printed data string, else right align
        . fractionWidth    = width of the fraction in case of float data
        . fractionExponent = when True print exponent in case of float data, else only print fraction
        """
        if isinstance(data, float):
            # Log in float format
            if fractionExponent:
                dataStr = '%.*e' % (fractionWidth, data)   # log data as float with exponent
            else:
                dataStr = '%.*f' % (fractionWidth, data)   # log data as float
        elif isinstance(data, complex):
            # Log in complex float format
            if fractionExponent:
                dataStr = '%.*e,' % (fractionWidth, data.real)   # log data real part as float with exponent
                dataStr += '%.*ej' % (fractionWidth, data.imag)  # log data imag part as float with exponent
            else:
                dataStr = '%.*f,' % (fractionWidth, data.real)   # log data real part as float
                dataStr += '%.*fj' % (fractionWidth, data.imag)  # log data imag part as float
        else:
            # Default log data as string
            dataStr = '%s' % str(data)  # the data can be any type that fits %s e.g. int, string, tuple
                                        # the explicite conversion by str() is needed for tuple
        # Left or right align the dataStr within dataWidth
        if dataLeft:
            dataStr = '%-*s ' % (dataWidth, dataStr)
        else:
            dataStr = '%*s ' % (dataWidth, dataStr)
        return dataStr
                
        
    def append_log_one_dimensional_list(self, vLevel, name, L, prefixStr='', dataWidth=4, dataLeft=False, fractionWidth=0, fractionExponent=False, colIndices=None):
        """Log list L[col] in one row with index labels
        
        . vLevel           = verbosity level
        . name             = name, title of the list
        . L                = the one dimensional list
        . prefixStr        = prefix string that is printed before every line, can e.g. be used for grep
        . dataWidth        = of data in column, see self.data_to_string
        . dataLeft         = of data in column, see self.data_to_string
        . fractionWidth    = of data in column, see self.data_to_string
        . fractionExponent = of data in column, see self.data_to_string
        . colIndices       = when None then log counter index, else use index from list
        
        Remarks:
        . This append_log_one_dimensional_list is similar to using append_log_data with nofColumns=len(L)
        . This append_log_one_dimensional_list is similar to append_log_two_dimensional_list with 1 row.
        """
        if vLevel <= self.verbosity:
            self.append_log(vLevel, '')   # start with newline
            self.append_log(vLevel, prefixStr + '%s:' % name)
            nof_cols = len(L)
            # Print row with column indices
            if colIndices == None:
                colIndices = list(range(nof_cols))
            col_index_str = '. index : '
            for col in colIndices:
                col_index_str += '%*d ' % (dataWidth, col)
            self.append_log(vLevel, prefixStr + col_index_str)
            # Print row with data
            line_str = '. value : '
            uniqueL = cm.unique(L)
            if len(uniqueL)==1:
                line_str += 'all ' + self.data_to_string(uniqueL[0], dataWidth, dataLeft, fractionWidth, fractionExponent)
            else:
                for col in range(nof_cols):
                    line_str += self.data_to_string(L[col], dataWidth, dataLeft, fractionWidth, fractionExponent)
            self.append_log(vLevel, prefixStr + '%s' % line_str)
            self.append_log(vLevel, '')   # end with newline
        

    def append_log_two_dimensional_list(self, vLevel, name, A, prefixStr='', transpose=False, reverseCols=False, reverseRows=False,
                                        dataWidth=4, dataLeft=False, fractionWidth=0, fractionExponent=False, colIndices=None, rowIndices=None):
        """
        Log two dimensional list A[row][col] per row with index labels
        
        . vLevel           = verbosity level
        . name             = name, title of the list
        . A                = the two dimensional list
        . prefixStr        = prefix string that is printed before every line, can e.g. be used for grep
        . transpose        = when true transpose(A) to log rows as columns and columns as rows
        . reverseCols      = when true reverse the order of the columns
        . reverseRows      = when true reverse the order of the rows
        . dataWidth        = of data in column, see self.data_to_string
        . dataLeft         = of data in column, see self.data_to_string
        . fractionWidth    = of data in column, see self.data_to_string
        . fractionExponent = of data in column, see self.data_to_string
        . colIndices       = when None then log counter index, else use index from list
        . rowIndices       = when None then log counter index, else use index from list (can be text index)
        
        Remarks:
        . The example recipy for making a two dimensional list of the form A[rows][cols] is:
          A = [], row=[], row.append(element) for all cols, A.append(row) for all rows
          or use cm.create_multidimensional_list([Number of rows][Number of cols])
        """
        if vLevel <= self.verbosity:
            self.append_log(vLevel, '')   # start with newline
            self.append_log(vLevel, prefixStr + '%s:' % name)
            if transpose:
                #print name, transpose
                A = cm.transpose(A)
            if reverseRows:
                A = cm.reverse_rows_ud(A)
            if reverseCols:
                A = cm.reverse_cols_lr(A)
            nof_rows = len(A)
            nof_cols = len(A[0])
            self.append_log(vLevel, prefixStr + 'col :')
            # Print row with column indices
            if colIndices == None:
                colIndices = list(range(nof_cols))
            if rowIndices == None:
                rowIndices = list(range(nof_rows))
                rowIndexLength = 6                          # default row_str prefix length
            else:
                rowIndexLength = 3 + len(str(rowIndices[-1]))  # use last row index string for row_str prefix length
            col_index_str = ' ' * rowIndexLength
            for col in colIndices:
                col_index_str += '%*d ' % (dataWidth, col)
            self.append_log(vLevel, prefixStr + col_index_str)
            self.append_log(vLevel, prefixStr + 'row :')
            # For each row print row index and row with data
            for ri,row in enumerate(rowIndices):
                row_str = '%3s : ' % row   # row index, log index as string to support also text index
                uniqueRow = cm.unique(A[ri])
                if len(uniqueRow)==1:
                    row_str += 'all ' + self.data_to_string(uniqueRow[0], dataWidth, dataLeft, fractionWidth, fractionExponent)
                else:
                    for col in range(nof_cols):
                        row_str += self.data_to_string(A[ri][col], dataWidth, dataLeft, fractionWidth, fractionExponent)
                self.append_log(vLevel, prefixStr + '%s' % row_str)
            self.append_log(vLevel, '')  # end with newline


    # Read the contents of a file and append that to the test log file
    def append_log_file(self, vLevel, fileName):
        try:
            appFile = open(fileName,'r')
            self.append_log(vLevel,appFile.read(),1,1,1,1)
            appFile.close()
        except IOError:
            self.append_log(vLevel,'ERROR : Can not open file %s' % fileName)
