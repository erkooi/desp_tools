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

"""Common definitions

"""

################################################################################
# System imports

import time
import math    # do not use numpy in common, to avoid making common to elaborate
import numpy as np
import operator
import inspect
import itertools 
import os
import os.path
from functools import reduce

################################################################################
# Constants

c_nibble_w       = 4
c_byte_w         = 8
c_halfword_w     = 16
c_word_w         = 32
c_longword_w     = 64

c_byte_sz        = 1
c_halfword_sz    = 2
c_word_sz        = 4
c_longword_sz    = 8

c_nibble_mod     = 2**c_nibble_w        # = 0x10
c_nibble_mask    = 2**c_nibble_w-1      # = 0x0F
c_byte_mod       = 2**c_byte_w          # = 0x100
c_byte_mask      = 2**c_byte_w-1        # = 0x0FF
c_halfword_mod   = 2**c_halfword_w      # = 0x10000
c_halfword_mask  = 2**c_halfword_w-1    # = 0x0FFFF
c_word_mod       = 2**c_word_w          # = 0x100000000
c_word_mask      = 2**c_word_w-1        # = 0x0FFFFFFFF
c_word_sign      = 2**(c_word_w-1)      # = 0x010000000
c_longword_mod   = 2**c_longword_w      # = 0x10000000000000000
c_longword_mask  = 2**c_longword_w-1    # = 0x0FFFFFFFFFFFFFFFF
c_longword_sign  = 2**(c_longword_w-1)  # = 0x01000000000000000

c_nof_complex    = 2


################################################################################
# Functions

def greatest_common_div(A, B):
    """
    Find the greatest common divisor of A and B.
    """
    while B != 0:
        rem = A % B
        A = B
        B = rem
    return A

def ceil_div(num, den):
    """ Return integer ceil value of num / den """
    return int(math.ceil( num / float(den) ) )
    
def ceil_log2(num):
    """ Return integer ceil value of log2(num) """
    return int(math.ceil(math.log(int(num), 2) ) )

def ceil_pow2(num):
    """ Return power of 2 value that is equal or greater than num """
    return 2**ceil_log2(num)
    
def sel_a_b(sel, a, b):
    if sel==True:
        return a
    else:
        return b

def smallest(a, b):
    if a<b:
        return a
    else:
        return b
        
def largest(a, b):
    if a>b:
        return a
    else:
        return b
        
def signed32(v):
    if v < c_word_sign:
        return v
    else:
        return v-c_word_mod
        
def signed64(v):
    if v < c_longword_sign: 
        return v
    else:
        return v-c_longword_mod

def int_clip(inp, w, symmetric=False):
    # Purpose : Clip an integer value to w bits
    # Input:
    # - inp      = Integer value
    # - w        = Output width in number of bits
    # Description: Output range -2**(w-1) to +2**(w-1)-1
    # Return:
    # - outp     = Clipped value
    outp=0
    if w>0:
        clip_p= 2**(w-1)-1
        if symmetric:
            clip_n=-2**(w-1)+1
        else:
            clip_n=-2**(w-1)
        if inp > clip_p:
            outp=clip_p
        elif inp < clip_n:
            outp=clip_n
        else:
            outp=inp
    return outp

def int_wrap(inp, w):
    # Purpose: Wrap an integer value to w bits
    # Input:
    # - inp      = Integer value
    # - w        = Output width in number of bits
    # Description: Remove MSbits, output range -2**(w-1) to +2**(w-1)-1
    # Return:
    # - outp     = Wrapped value
    outp=0
    if w>0:
        wrap_mask=2**(w-1)-1
        wrap_sign=2**(w-1)
        if (inp & wrap_sign) == 0:
            outp=inp & wrap_mask
        else:
            outp=(inp & wrap_mask) - wrap_sign
    return outp

def int_round(inp, r, direction="HALF_AWAY", clip=False, outp_w=0):
    # Purpose : Round the r LSbits of an integer value
    # Input:
    # - inp       = Integer value, signed value
    # - r         = Number of LSbits to round
    # - direction = "HALF_AWAY", "HALF_UP", "HALF_EVEN"
    # - clip, outp_w = When clip is True then clip output to fit in outp_w bits if output
    #                  otherwise would wrap due to rounding
    # Description:
    #   direction = "HALF_AWAY" --> Round half away from zero so +0.5 --> 1, -0.5 --> -1.
    #   direction = "HALF_UP"   --> Round half to +infinity   so +0.5 --> 1, -0.5 --> 0.
    #   direction = "HALF_EVEN" --> Round half to even        so +0.5 --> 0, -0.5 --> 0,
    #                                                            +1.5 --> 2, -1.5 --> -2.
    #   half down       : y = ceil(x - 0.5)
    #   half up         : y = floor(x + 0.5)
    #   integer division: x // y = floor(x / y)
    # Return:
    # - outp     = Rounded integer value
    outp=inp
    if r>0:
        round_factor=2**r
        round_p = 2**(r-1)   # = 0.5, = half
        round_n = 2**(r-1)-1
        if direction == "HALF_UP":
            outp = (inp + round_p) // round_factor
        elif direction == "HALF_AWAY":
            if inp >= 0:
                outp = (inp + round_p) // round_factor   # Round half up for positive
            else:
                outp = (inp + round_n) // round_factor   # Round half down for negative
        elif direction == "HALF_EVEN":
            outp = (inp + round_p) // round_factor  # Round to nearest using floor(x/y + 0.5)
            if inp % round_factor == round_p:
                if outp % 2 == 1:  # Round half to even, so when odd subtract 1
                    outp -= 1      # to make outp even
        else:
            print('int_round: Error: unsupported round direction')
        if clip:
            clip_max = 2**(outp_w-1)-1  # signed max
            if outp > clip_max:
                outp = clip_max
    return outp


def uint_round(inp, r, direction="HALF_UP", clip=False, outp_w=0):
    # Purpose : Round the r LSbits of an natural value
    # Input:
    # - inp       = Natural value, unsigned value
    # - r         = Number of LSbits to round
    # - direction = "HALF_UP", "HALF_EVEN"
    # - clip, outp_w = When clip is True then clip output to fit in outp_w bits if output
    #                  otherwise would wrap due to rounding
    # Description:
    #   Note for unsigned "HALF_AWAY" is same as "HALF_UP"
    #   direction = "HALF_UP"   --> Round half to +infinity   so +0.5 --> 1
    #   direction = "HALF_EVEN" --> Round half to even        so +0.5 --> 0
    #                                                            +1.5 --> 2
    # Return:
    # - outp     = Rounded natural value
    if inp >= 0:
        return int_round(inp, r, direction, clip, outp_w+1)
    else:
        print('uint_round: Error: unsigned inp must be >= 0')


def int_truncate(inp, r, direction=''):
    # Purpose : Truncate the r LSbits of an integer value
    # Input:
    # - inp      = Integer value
    # - r        = Number of LSbits to truncate
    # Description: Remove LSBits.
    #   Default truncate behaves asymmetric like in HDL by removing the r lsbits using shift right >> r
    #   If direction is SYMMETRIC then inp < 0 is -truncate(-inp)
    # Return:
    # - outp     = Truncated value
    # Usage example at Python prompt after import as cm:
    #  [cm.int_truncate(d,1) for d in range(-8,8)]
    #  [cm.int_truncate(d,1,'') for d in range(-8,8)]
    #  [cm.int_truncate(d,2) for d in range(-8,8)]
    #  [cm.int_truncate(d,2,'') for d in range(-8,8)]
    outp=inp
    if r>0:
        if direction == "SYMMETRIC":
            if inp >= 0:
                outp=inp>>r
            else:
                outp=-((-inp)>>r)
        else:
            outp=inp>>r
    return outp
        

def int_requantize(inp, inp_w, outp_w, lsb_w=0, lsb_round=False, msb_clip=False, gain_w=0):
    # Purpose : Requantize integer value similar as common_requantize.vhd
    # Input:
    # - inp       = Integer value
    # - inp_w     = Input data width
    # - outp_w    = Output data width
    # - lsb_w     = Number of LSbits to truncate
    # - lsb_round = when true round else truncate the input LSbits
    # - msb_clip  = when true clip else wrap the input MSbits
    # - gain_w    = Output gain in number of bits
    # Description: First round or truncate the LSbits, then clip or wrap the MSbits and then apply optional output gain
    # Return:
    # - outp     = Requantized value
    
    # Input width
    r = int_wrap(inp, inp_w)
    # Remove LSBits using ROUND or TRUNCATE
    if lsb_round:
        r = int_round(r, lsb_w)
    else:
        r = int_truncate(r, lsb_w)
    # Remove MSBits using CLIP or WRAP
    if msb_clip:
        r = int_clip(r, outp_w)
    else:
        r = int_wrap(r, outp_w)
    # Output gain
    r = r<<gain_w
    outp = int_wrap(r, outp_w)
    return outp

  
def flatten(x):
    """
    Flatten lists of lists of any depth. Preserves tuples.
    """
    result = []
    for el in x:
        if hasattr(el, "__iter__") and not isinstance(el, str) and type(el)!=tuple and not issubclass(type(el), tuple):
            result.extend(flatten(el))
        else:
            result.append(el)
    return result

def do_until(method, val, op=operator.eq, ms_retry=10, s_timeout=4, **kwargs):
    """
    Default: DO [method] UNTIL [method==val] 
    Example: do_until( self.read_status, 0) will execute self.read_status() until all 
    elements in the returned list equal 0.
    Use **kwargs to pass keyworded arguments to the input method;
    Use ms_retry to set the time in milliseconds before rerunning the method;
    Use s_timeout to set the time in seconds before timeout occurs (returns 1). Use
    s_timeout<0 to disable the time out
    All standard Python operators (see operator class) are supported, the default
    is eq (equal to).
    """
    list_ok = 0
    start = time.time()
    while list_ok == 0:
        if s_timeout>=0:
            if time.time() - start >= s_timeout:
                print('do_until: Timeout occured!')
                return 'Timeout'
        data = []
        if len(kwargs) > 0:
            data.append(method(**kwargs))
        else:
            data.append(method())
        flat_data = flatten(data)
        list_ok = 1
        for i in range(0, len(flat_data)):
            if not op(flat_data[i], val):
                list_ok = 0
        if list_ok == 0:
            time.sleep(ms_retry/1000.0)
    if list_ok == 1:
        #dur = time.time() - start
        #print 'do_until:', dur
        return flat_data[0]

def do_until_lt(method, val, ms_retry=1, s_timeout=4, **kwargs): return do_until(method, val, operator.lt, ms_retry, s_timeout, **kwargs)
def do_until_le(method, val, ms_retry=1, s_timeout=4, **kwargs): return do_until(method, val, operator.le, ms_retry, s_timeout, **kwargs)
def do_until_eq(method, val, ms_retry=1, s_timeout=4, **kwargs): return do_until(method, val, operator.eq, ms_retry, s_timeout, **kwargs)
def do_until_ne(method, val, ms_retry=1, s_timeout=4, **kwargs): return do_until(method, val, operator.ne, ms_retry, s_timeout, **kwargs)
def do_until_ge(method, val, ms_retry=1, s_timeout=4, **kwargs): return do_until(method, val, operator.ge, ms_retry, s_timeout, **kwargs)
def do_until_gt(method, val, ms_retry=1, s_timeout=4, **kwargs): return do_until(method, val, operator.gt, ms_retry, s_timeout, **kwargs)

def reverse_byte(byte):
    """
    Fast way to reverse a byte on 64-bit platforms.
    """
    #return (byte * 0x0202020202L & 0x010884422010L) % 1023
    return(byte * 0x0202020202 & 0x010884422010) % 1023  # PD: check

def reverse_word(word):
    """
    Fast way to reverse a word on 64-bit platforms.
    """
    B0 = (word & 0xFF)
    B1 = (word & 0xFF00) >> 8
    B2 = (word & 0xFF0000) >> 16
    B3 = (word & 0xFF000000) >> 24
    reversed_word = (reverse_byte(B0) << 24) | (reverse_byte(B1) << 16) | (reverse_byte(B2) << 8) | (reverse_byte(B3))
    return reversed_word

def add_list(aList, bArg):
    """
    Element by element add list b to list a or add value b to each element in list a 
    """
    aLen  = len(aList)
    bList = listify(bArg)
    if len(bList)==1:
        bList = bList[0]*aLen
    s = []
    for i in range(aLen):
        s.append(aList[i] + bList[i])
    return s
    
def add_list_elements(in_list):
    """
    Add list elements together, e.g. [1,2,3,4,5,6] -> 1+2+3+4+5+6=21

    Note: Guido van Rossum prefers using list comprehension instead of reduce, lambda (https://www.python-course.eu).
    """
    return reduce(lambda x, y: x+y, in_list)

def abs_list(in_list):
    """
    Return abs() of each element in in_list, e.g. [2, 3+4j, -6] -> [2, 5, 6]
    """
    return [abs(x) for x in in_list]

def is_complex_list(in_list):
    """
    Return True if at least one element in in_list is complex, else return False
    """
    isComplex = [isinstance(x, complex) for x in in_list]
    if True in isComplex:
        return True
    else:
        return False

def mean_list_elements(in_list):
    """
    Return mean of list elements, e.g. [2,3,5] -> 1.0* (2 + 3 + 5) / 3 =  3.333 = numpy.mean([2,3,5]

    Note: this method is ok, but in general better use numpy.mean()
    """
    return 1.0 * sum(in_list) / len(in_list)

def std_list_elements(in_list, populationSet=True):
    """
    Return standard deviation of list elements, e.g. [2,5] -> math.sqrt(((2-3.5)**2.0 + (5-3.5)**2.0) / 2) = numpy.std([2,5])
    
    When population is True divide by len(in_list) to get the standard deviation of a complete set,
    else divide by len(in_list)-1 to get the standard deviation for a sample of a set.
    
    Note: this method is ok, but in general better use numpy.std()
    """
    m = mean_list_elements(in_list)
    if populationSet:
        return math.sqrt(sum([abs(x-m)**2.0 for x in in_list]) / len(in_list))
    else:
        return math.sqrt(sum([abs(x-m)**2.0 for x in in_list]) / (len(in_list)-1))

def rms_list_elements(in_list, populationSet=True):
    """
    Return root mean square of list elements.
    
    Note: rms = sqrt(mean**2 + std**2), so rms() = std() if mean() = 0.
    """
    return math.sqrt(sum([abs(x)**2.0 for x in in_list]) / len(in_list))

def pwr_list_elements(in_list, populationSet=True):
    """
    Return mean power of list elements (= mean**2 + std**2)
    
    When population is True divide by len(in_list) to get the standard deviation of a complete set,
    else divide by len(in_list)-1 to get the standard deviation for a sample of a set.
    """
    if populationSet:
        return math.sqrt(sum([abs(x)**2.0 for x in in_list]) / len(in_list))
    else:
        return math.sqrt(sum([abs(x)**2.0 for x in in_list]) / (len(in_list)-1))
        
def calculate_list_data_statistics(data_list):
    """Calculate several single value statistics for the data in data_list
    
    Returns mean, std, rms, max abs, max and min of real part, max and min of imag part
    
    The data_list can be a list of:
    - real values that were read with read_data_buffer() and then converted to signed integers using to_signed().
    - complex values that were read with read_data_buffer() and then converted into complex data using unconcat_complex().
    
    For a real data list the max abs is max([max real, -min real])
    For a real data list the max and min of the imag part are 0.
    """
    mean = mean_list_elements(data_list)
    std = std_list_elements(data_list)
    rms = rms_list_elements(data_list)
    maxAbs = max(abs_list(data_list))
    if is_complex_list(data_list):
        realData, imagData = split_complex(data_list)
        maxReal = max(realData)
        minReal = min(realData)
        maxImag = max(imagData)
        minImag = min(imagData)
    else:
        maxReal = max(data_list)
        minReal = min(data_list)
        maxImag = 0
        minImag = 0
    return mean, std, rms, maxAbs, maxReal, minReal, maxImag, minImag

def subtract_list(aList, bArg):
    """
    Element by element subract list b from list a or subract value b from each element in list a 
    """
    aLen  = len(aList)
    bList = listify(bArg)
    if len(bList)==1:
        bList = bList[0]*aLen   
    s = []
    for i in range(aLen):
        s.append(aList[i] - bList[i])
    return s
    
def multiply_list(aList, bArg):
    """
    Element by element multiply list b with list a or multiply value b with each element in list a 
    """
    aLen  = len(aList)
    bList = listify(bArg)
    if len(bList)==1:
        bList = bList[0]*aLen
    s = []
    for i in range(aLen):
        s.append(aList[i] * bList[i])
    return s
    
def multiply_list_elements(in_list):
    """
    Multiply list elements together, e.g. [1,2,3,4,5,6] -> 1*2*3*4*5*6=720.
    """
    return reduce(lambda x, y: x*y, in_list)
    
def divide_list(aList, bArg):
    """
    Element by element divide list a by list b or divide each element in list a by value b
    """
    aLen  = len(aList)
    bList = listify(bArg)
    if len(bList)==1:
        bList = bList[0]*aLen
    for i in range(aLen):
        s.append(aList[i] / bList[i])   # assume float division
    return s
    
def split_list(source_list, split_size=None, sublist_items=None, nof_output_lists=None):
    """
    Splits a list based on split_size. Optionally, the indices passed in sublist_items 
    are extracted from each sublist.
    """
    if split_size==None:
        split_size=len(source_list)//nof_output_lists
    sublists = [source_list[i:i+split_size] for i in range(0, len(source_list), split_size)]
    if sublist_items==None:
        return sublists
    else:
        if len(listify(sublist_items))==1:
            return [listify(operator.itemgetter(*listify(sublist_items))(sl)) for sl in sublists]
        else:
            return [list(operator.itemgetter(*listify(sublist_items))(sl)) for sl in sublists]

def extend_list(aList, aLength, aElement=None):
    """If necessary extend copy of aList to aLenght by appending aElement one or more times.
    
       Returns the extended copy eList of aList, so aList is not affected.
    """
    eList = list(aList)   # list() copy is necessary, because otherwise the input aList is also affected
    listLen = len(eList)
    if listLen<aLength:
        eList += (aLength - listLen) * [aElement]
    return eList

def extend_list_dim2(aList, aLength, aElement=None):
    """If necessary extend the rows in copy of 2-dimensional aList to aLenght by appending aElement one or more times.
    
       Returns the extended copy eList of aList, so aList is not affected.
    """
    eList = list(aList)   # list() copy is necessary, because otherwise the input aList is also affected
    for row in range(len(aList)):
        eList[row] = extend_list(eList[row], aLength, aElement)
    return eList
    
def remove_elements_from_list(aList, aElement, condition=operator.eq):
    """Remove elements from copy of aList that match the condition value. The aElement can be a single value or a list.
    
       Returns copy of aList with the aElements removed.
       
       Condition operators from import operator are e.g. 
         operator.eq : ==
         operator.ne : !=
         operator.lt : <
         operator.le : <=
         operator.gt : >
         operator.ge : >=
    """
    rList = list(aList)      # list() copy is not strictly necessary, because the list comprehension below creates a copy anyway
    for el in listify(aElement):
        rList = [x for x in rList if not condition(x, el)]
    return rList

def remove_elements_from_list_eq(aList, aElement): return remove_elements_from_list(aList, aElement, condition=operator.eq)
def remove_elements_from_list_ne(aList, aElement): return remove_elements_from_list(aList, aElement, condition=operator.ne)
def remove_elements_from_list_lt(aList, aElement): return remove_elements_from_list(aList, aElement, condition=operator.lt)
def remove_elements_from_list_le(aList, aElement): return remove_elements_from_list(aList, aElement, condition=operator.le)
def remove_elements_from_list_gt(aList, aElement): return remove_elements_from_list(aList, aElement, condition=operator.gt)
def remove_elements_from_list_ge(aList, aElement): return remove_elements_from_list(aList, aElement, condition=operator.ge)

def create_multidimensional_list(shape, element=None):
    """Creating a multidimensional list
    
       The recusion using list comprehension was obtained from create_empty_array_of_shape()
       at stackoverflow. Erko added element and the possibility to let element be a list.
       
       For example shape = [2, 3] returns [[None, None, None], [None, None, None]]

       Remarks:
       . The advantage of using lists instead of numpy arrays is that the elements in the
         list can be of any type.
       . Uses list() to take copy of element in case element is a list, to ensure that all
         elements in the multidimensional list will be unique. Without using list() all
         elements in the multidimensional list would relate and apply to a single element,
         due to how Python treats list instances.
    """
    # Implementation scheme A is much faster than the scheme B, therefore scheme B is
    # only kept in comment for comparison.
    
    # Scheme A recurses and then creates lowest dimensions with the elements first:
    if len(shape)>0:
        return [create_multidimensional_list(shape[1:], element) for i in range(shape[0])]
    elif isinstance(element, list):
        return list(element)  # take copy to ensure unique element
    else:
        return element

    # Scheme B recurses and then creates highest dimensions first:
    #if len(shape)>1:
    #    aList = shape[0] * [[]]
    #    for i in range(shape[0]):
    #        aList[i] = create_multidimensional_list(shape[1:], element)
    #else:
    #    if isinstance(element, list):
    #        aList = []
    #        for i in range(shape[0]):
    #            aList.append(list(element))  # take copy to ensure unique element
    #    else:
    #        aList = shape[0] * [element]
    #return aList

def create_multidimensional_dlist(shape, element=0):
    """Creating a multidimensional array with numpy and return it as a list
    
       For example shape = [2, 3] returns [[None, None, None], [None, None, None]]

       Remarks:
       . The advantage of using lists instead of numpy arrays is that the elements in the
         list can be of any type.
       . Uses list() to take copy of element in case element is a list, to ensure that all
         elements in the multidimensional list will be unique. Without using list() all
         elements in the multidimensional list would relate and apply to a single element,
         due to how Python treats list instances.
    """
    if type(element) in [int, float, complex, bool]:
        if len(shape) > 0:
            _dlist = np.zeros(shape, type(element))
            _dlist.fill(element)
            return _dlist.tolist()
    # if not numpy type or shape is a single element then default to general list      
    return create_multidimensional_list(shape, element)
       

def index_a_in_b(a, b, duplicates=False):
    """
    Find the elements of list a in list b and return their indices (relative to b).
    Does not return duplicates by default.
    """
    if duplicates==False:
        return [i for i,item in enumerate(b) if item in a]
    else:
        hits = []
        for item_in_a in a:
            hits.append( [i for i,item in enumerate(b) if item == item_in_a] )
        return flatten(hits)

def index_a_in_multi_b(a, b):
    """
    Find a in multi-dimensional list b. Returns first hit only.
    """
    if a == b: return []
    try:
        for i,e in enumerate(b):
            r = index_a_in_multi_b(a,e)
            if r is not None: 
                r.insert(0,i)
                return r
    except TypeError:
        pass
    return None

def exist_all_elements_from_a_in_b(a, b):
    """Return True if all elements in a are also in list b, else return False.
       
       Both a and b can be a one dimensional list or a single object.
    """
    for i in listify(a):
        if i not in listify(b):
            return False
    return True
    

def find_indices_where(in_list, value, condition=operator.eq):
    """Return list of indices in in_list that match the condition value
    
       Condition operators from import operator are e.g. 
         operator.eq : ==
         operator.ne : !=
         operator.lt : <
         operator.le : <=
         operator.gt : >
         operator.ge : >=
    """
    return [i for i,x in enumerate(in_list) if condition(x, value)]
        
def find_indices_where_eq(in_list, value): return find_indices_where(in_list, value, operator.eq)
def find_indices_where_ne(in_list, value): return find_indices_where(in_list, value, operator.ne)
def find_indices_where_lt(in_list, value): return find_indices_where(in_list, value, operator.lt)
def find_indices_where_le(in_list, value): return find_indices_where(in_list, value, operator.le)
def find_indices_where_gt(in_list, value): return find_indices_where(in_list, value, operator.gt)
def find_indices_where_ge(in_list, value): return find_indices_where(in_list, value, operator.ge)


def unique(in_list):
    """
    Extract unique list elements (without changing the order like set() does)
    """
    seen = {}
    result = []
    for item in in_list:
       if item in seen: continue
       seen[item] = 1
       result.append(item)
    return result
    
def reverse_list(in_list):
    """Return list in reversed index order"""
    return list(reversed(in_list))
    
def sort_list_indices(in_list, lowToHigh = True):
    """Return list of original indices of in_list for the sorted(in_list)"""
    result = sorted(list(range(len(in_list))), key = lambda ix : in_list[ix])
    if lowToHigh==True:
        return result
    else:
        return reverse_list(result)
    
def list_duplicates(in_list):
    """
    find duplicate list elements
    """
    # http://stackoverflow.com/questions/9835762/find-and-list-duplicates-in-python-list
    seen = set()
    seen_add = seen.add
    # adds all elements it doesn't know yet to seen and all other to seen_twice
    seen_twice = set( x for x in in_list if x in seen or seen_add(x) )
    # turn the set into a list (as requested)
    return list( seen_twice )

def all_the_same(lst):
    """
    Returns True if all the list elements are identical.
    """
    return lst[1:] == lst[:-1]

def all_equal_to(lst, value):
    """
    Returns True if all the list elements equal 'value'.
    """
    if all_the_same(lst)==True and lst[0]==value:
        return True
    else:
        return False
      
def rotate_list(in_list, n):
    """
    Rotates the list. Positive numbers rotate left. Negative numbers rotate right.
    """
    return in_list[n:] + in_list[:n]  
      
def to_uword(arg):
    """
    Represent 32 bit value as unsigned word. Note that:
    
      common.to_signed(common.to_uword(-1), 32) = -1
      
    """
    vRet = []
    vList = listify(arg)
    for value in vList:
        v = int(value) & c_word_mask     # mask the 32 bits, also accept float value by converting to int
        vRet.append(v)
    return unlistify(vRet)
    
def to_unsigned(arg, width):
    """
    Interpret value[width-1:0] as unsigned
    """
    c_mask = 2**width-1
    vRet = []
    vList = listify(arg)
    for value in vList:
        v = int(value) & c_mask     # mask the lower [width-1:0] bits, also accept float value by converting to int
        vRet.append(v)
    return unlistify(vRet)

def to_signed(arg, width):
    """
    Interpret arg value[width-1:0] or list of arg values as signed (two's complement)
    """
    c_wrap = 2**width
    c_mask = 2**width-1
    c_sign = 2**(width-1)
    vRet = []
    vList = listify(arg)
    for value in vList:
        v = int(value) & c_mask   # mask the lower [width-1:0] bits, also accept float value by converting to int
        if v & c_sign:
            v -= c_wrap           # keep negative values and wrap too large positive values
        vRet.append(v)
    return unlistify(vRet)
  
def max_abs(data):
    return max(max(data), -min(data))
      
def insert(orig, new, pos):
    """
    Inserts new (string, element) inside original string or list at pos. 
    """
    return orig[:pos] + new + orig[pos:]

def deinterleave(input_stream, nof_out, block_size=1):
    """
    Deinterleave a stream (=flat list) into nof_out output streams based on block_size.
    >> deinterleave( [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16], 4, 2 )
    >> [ [1,2,9,10], [3,4,11,12], [5,6,13,14], [7,8,15,16] ]
    Note: len(input_stream)/nof_out/block_size should yield an integer.
    Note: This method behaves exactly like common_deinterleave.vhd.
    """
    # Check passed arguments:
    if ( float(len(input_stream))/nof_out/block_size%1==0):
        # Split the list into block_sized sublists:
        if block_size>1:
            block_list = split_list(input_stream, block_size)
        else:
            block_list = input_stream
   
        # Split block_list into 2 sublists so we can transpose them
        sublist_size = nof_out
        block_2arr = split_list(block_list, sublist_size)
        transposed = transpose(block_2arr)

        # Flatten the list so we can re-split it:
        flat_out_list = flatten(transposed)
    
        # Divide this new stream across nof_out:
        sublist_size = len(input_stream)//nof_out
    
        result = split_list(flat_out_list, sublist_size)
        return result
    else:
        print('deinterleave: Error: len(input_stream)/nof_out/block_size should yield an integer!')

def interleave(input_streams, block_size=1):
    """
    Interleave a list of multiple lists into one based on block size. 
    Note: This method behaves exactly like common_interleave.vhd.
    """
    # flatten the list
    flat_list = flatten(input_streams)

    # Use deinterleave function to pull the stream apart block-wise and restore the correct order
    nof_lists = len(input_streams[0]) // block_size
    deint_block_list = deinterleave(flat_list, nof_lists, block_size)

    # Flatten the list
    result = flatten(deint_block_list)
    return result

def reinterleave(input_streams, nof_out, block_size_in=1, block_size_out=1):
    """
    Re-interleave X input streams across nof_out output streams. The input streams are first
    deinterleaved with block_size_in, then nof_out interleaved streams are made with block_size_out. 
    Note: This method behaves exactly like common_reinterleave.vhd.
    """
    nof_in = len(input_streams)

    # Array of deinterleavers:
    # ------------------------
    # deint_arr: [nof_in][deinterleaved streams]:
    deint_arr = []
    for in_no in range(nof_in):
        deint_arr.append(deinterleave(input_streams[in_no], nof_out, block_size_in))

    # Deinterleavers -> interleavers interconnect:
    inter_in_arr = []
    for i in range(nof_out):
        inter_in = []
        for j in range(nof_in):
            inter_in.append(deint_arr[j][i])
        inter_in_arr.append(inter_in)

    # Array of interleavers:
    # ----------------------
    # inter_arr: [nof_out][interleaved streams]:
    inter_out_arr = []
    for out_no in range(nof_out):
         inter_out_arr.append(interleave(inter_in_arr[out_no], block_size_out))
    return inter_out_arr

def reverse_cols_lr(matrix):
    """ Flip order of the columns in the matrix[row][col]
    
    Using numpy only fits matrix lists with numbers:

        np_matrix = np.array(matrix)
        return np_matrix.fliplr().tolist()
    
    To suit any list element type use general fliplr.
    """
    result = []
    for row in matrix:
        result.append(list(reversed(row)))
    return result
        
def reverse_rows_ud(matrix):
    """ Flip order of the rows in the matrix[row][col]
    
    Using numpy only fits matrix lists with numbers:

        np_matrix = np.array(matrix)
        return np_matrix.flipud().tolist()
    
    To suit any list element type use general flipud.
    
    This reverse_rows_ud() is equivalent to reverse_list(), because it affects the row index, that is the first index.
    """
    return list(reversed(matrix))

def transpose(matrix):
    """ PD transpose using numpy """
    np_matrix = np.array(matrix)
    return np_matrix.transpose().tolist()
    
    """
    Transpose by using zip()
    """
    result = []
    transposed = list(zip(*matrix))
    # Python's zip() returns a list of tuples. We do not want that as tuples
    # should only be used to bind items together; methods like flatten()
    # preserve tuples (as tuples should not be broken - that's why they're 
    # tuples in the first place) wich would mean the output of a transpose 
    # could not be flattened. So, convert the list of tuples to a list of lists:
    for i in transposed:
        result.append(list(i))
    return result

def straighten(matrix, padding=' '):
    """
    Straighten a crooked matrix by padding the shorter lists with the padding
    up to the same length as the longest list.
    """
    padded_matrix = []
    max_len = len(max(matrix))
    for row in matrix:
        padded_matrix.append(pad(row, max_len, padding))
    return padded_matrix
 
def pad(lst, length, padding=' '):
    """
    Pad a list up to length with padding
    """
    return lst+[padding]*(length-len(lst))

def depth(x):
    """
    Returns the depth of x. Returns 0 if x is not iterable (not a list or tuple).
    """
    if isinstance(x, list) or isinstance(x, tuple):
        for level in itertools.count():
            if not x:
                return level
            x = list(itertools.chain.from_iterable(s for s in x if isinstance(s, list) or isinstance(s, tuple)))
    else:
        return 0

def listify(x):
    """
    Can be used to force method input to a list.
    """
    # The isinstance() built-in function is recommended over the type() built-in function for testing the type of an object
    if isinstance(x, list):
        return x
    else:
        return [x]

def unlistify(x):
    """
    Converts 1-element list to x.
    """
    # The isinstance() built-in function is recommended over the type() built-in function for testing the type of an object
    if isinstance(x, list):
        if len(x)==1:
            return x[0]
        else:
            return x
    else:
        return x

def tuplefy(x):
    """
    Similar to listify().
    This method enables user to iterate through tuples of inconsistent depth by
    always returning a non-flat tuple.
    Pushes a flat tuple (depth=1) e.g. (0,1,2) one level deeper: ( (0,1,2), ).
    Non-flat tuples are returned untouched.
    A non-tuple (depth=0) is also pushed into a tuple 2 levels deep.
    """
    if depth(x)==1:
        return (x,)
    elif depth(x)==0:
       return ( (x,), )
    else:
        return x

def method_name(caller_depth=0):
    """
    Returns the name of the caller method.
    """
    # Note: inspect.stack()[0][3] would return the name of this method.
    return inspect.stack()[caller_depth+1][3]

def method_arg_names(method):
    """
    Returns the names of the arguments of passed method.
    """
    return inspect.getargspec(method)[0]
    
def concat_complex(list_complex, width_in_bits, imreOrder=True):
    """
    Concatenates the real and imaginary part into one integer. 
    The specifed width counts for both the real and imaginary part. 
    Real part is mapped on the LSB. Imaginary part is shifted to the MSB. 
    """
    # PD
    if imreOrder:
        return [((int(i.imag) & (2**width_in_bits-1)) << width_in_bits) + (int(i.real) & (2**width_in_bits-1)) for i in list_complex]
    else:
        return [((int(i.real) & (2**width_in_bits-1)) << width_in_bits) + (int(i.imag) & (2**width_in_bits-1)) for i in list_complex]
    
    # EK    
    result = []    
    for i in range(len(list_complex)):
        real = int(list_complex[i].real) & (2**width_in_bits-1)
        imag = int(list_complex[i].imag) & (2**width_in_bits-1)
        if imreOrder:
            result.append((imag << width_in_bits) + real)
        else:
            result.append((real << width_in_bits) + imag)
    return result                                       

def unconcat_complex(list_concat, width_in_bits, imreOrder=True):
    """
    Unconcatenates the real and imaginary part from an integer list into
    a complex list with separate real and imaginary part. The integers
    in list_concat are 2*width_in_bits wide.
    Real part is extracted from the LSB. Imaginary part is extracted the MSB. 
    Example:
      >>> unconcat_complex(concat_complex([complex(1,2), complex(3,4)], 16), 16)
      [(1+2j), (3+4j)]
    """
    result = []    
    for i in range(len(list_concat)):
        lo = to_signed( list_concat[i]                   & (2**width_in_bits-1), width_in_bits)
        hi = to_signed((list_concat[i] >> width_in_bits) & (2**width_in_bits-1), width_in_bits) 
        if imreOrder:
            result.append(complex(lo, hi))
        else:
            result.append(complex(hi, lo))
    return result                                       

def split_complex(list_complex):
    """
    Returns the real and imaginary part in two separate lists. 
    [list_re, list_im] = split_complex(list_complex)
    """ 
    list_real = []
    list_imag = []
    for i in range(len(list_complex)):
        list_real.append(list_complex[i].real)
        list_imag.append(list_complex[i].imag)
    return (list_real, list_imag)

def unsplit_complex(list_real, list_imag):
    """Returns complex list by combining the real and imaginary parts from two separate lists. 
    """ 
    return [complex(x,y) for x,y in zip(list_real, list_imag)]

def mac_str(n):
    """
    Converts MAC address integer to the hexadecimal string representation,
    separated by ':'.
    """
    hexstr = "%012x" % n
    return ':'.join([hexstr[i:i+2] for i in range(0, len(hexstr), 2)])

def ip_str(n):
    """
    Converts IP address integer to the decimal string representation,
    separated by '.'.
    """
    ip_bytes = CommonBytes(n, 4)
    return str(ip_bytes[3])+'.'+str(ip_bytes[2])+'.'+str(ip_bytes[1])+'.'+str(ip_bytes[0])
    
def mkdir(path):
    """Recursively create leave directory and intermediate directories if they do not already exist."""
    expandPath = os.path.expandvars(path)        # support using environment variables in the file path
    expandPath = os.path.expanduser(expandPath)  # support using ~ in the file path
    if not os.path.exists(expandPath):
        os.makedirs(expandPath)
        
def expand_file_path_name(fpn, dir_path=''):
    """ Expand environment variables in fpn to get filePathName.
    - if it is an absolute path return filePathName else
    - if it still has a local file path prepend dir_path to the filePathName and return dir_path + filePathName.
    """
    filePathName = os.path.expandvars(fpn)           # support using environment variables in the file path
    filePathName = os.path.expanduser(filePathName)  # support using ~ in the file path
    if os.path.isabs(filePathName):
        return filePathName                          # use absolute path to file
    else:
        return os.path.join(os.path.expandvars(dir_path), filePathName)  # derive path to file from the directory path and a directory path to the file
    
def find_string_in_file(fpn, find_str):
    """Return index >= 0 if find_str is found in file fpn, returns -1 if find_str is not found in file fpn.
    
       Can also find '\n'.
    """
    return open(fpn, 'r').read().find(find_str)
    
def remove_from_list_string(list_str, item_str, sep=' '):
    """Treat the string list_str as a list of items that are separated by sep and then
       remove the specified item_str string from the list and return the list as a
       string of items separated by sep. Also remove any duplicate items.
    """
    ls = list_str.split(sep)
    ls = unique(ls)
    ls.remove(item_str)
    ls = sep.join(ls)
    return ls
    
def find_all_file_paths(rootDir, fileName):
    """
    Recursively search the rootDir tree to find the paths to all fileName files.
    """
    paths = []
    for root, _, files in os.walk(rootDir):
        if fileName in files:
             paths.append(root)
    return paths


def reverse_bits(num, nofBits):
    """Reverse the order of the number of bits in the number value, e.g. to perform a index bit flip for an FFT"""
    result = 0
    for i in range(nofBits):
        result = (result << 1) + (num & 1)   # flip order of bits
        num >>= 1
    return result
    

def invert_msbit(num, nofBits):
    """Invert the most significant bit of num, e.g. to perform an index fftshift()"""
    return (num & (2**nofBits-1)) ^ (2**(nofBits-1))  # first mask bits of num and then invert MSbit
    

################################################################################
# Classes

class CommonBits:
    """
    The purpose of this class is to allow the user to:
    1) create a CommonBits object with some data, e.g:
       >> my_bits = CommonBits(0xDEADBEEF)
    2) Use the bracket notation [] to extract bit ranges from that data:
       >> print(hex(my_bits[31:0]))
       0xdeadbeef
       >> print(hex(my_bits[31:4]))
       0xdeadbee
       >> print(hex(my_bits[31:16]))
       0xdead
       >> print(hex(my_bits[31]))
       0x1
       >> print(hex(my_bits[0]))
       0x1
    3) If a (optional) data width is passed, leading zeroes are added.
       >> my_bits = CommonBits(0xDEADBEEF, 16)
       >> print(hex(my_bits))
       0xbeef
       >> my_bits = CommonBits(0xDEADBEEF, 64)
       >> print(hex(my_bits[63:32]))
       0x0
    4) Besides getting bit slices, setting bitslices is also possible:
       >> my_bits = CommonBits(0xdeadbeef)
       >> print(my_bits)
       0xdeadbeef      
       >> my_bits[15:0] = 0xbabe
       >> print(my_bits)
       0xdeadbabe
    5) Use -1 to set a range of bits to all ones.
    6) Use VHDL-style & operator to concatenate CommonBits types.
       >> MyBitsHi = 0xDEAD
       >> MyBitsLo = 0xBEEF
       >> print(MyBitsHi & MyBitsLo & CommonBits(0xCAFEBABE))
       0xdeadbeefcafebabe
    """
    def __init__(self, data, bits=0):

        if data>=0:
            self.data = data
        else:
            print(("CommonBits: Error: Input data = %d. Only unsigned integers are supported, use to_unsigned(data, bits)." %data))

        if bits>0:
            # Set data width to passed 'bits'
            self.data_bin_len = bits

            # Check if data fits in passed nof bits
            if self.get_bin_len(data) > self.data_bin_len:
                print(("CommonBits: Error: input data %d does not fit in passed number of bits (%d)" %(data, bits)))

        else:
            # Use the minimum required data width            
            self.data_bin_len = self.get_bin_len(self.data)

    def __getitem__(self, bitslice):
        if self.check_slice(bitslice)==0:
            if type(bitslice)==type(slice(1,2,3)):
                # Get a bitmask for the bit range passed via the bitslice
                bitmask = self.bitmask(bitslice.start - bitslice.stop +1)
                return int((self.data >> bitslice.stop) & bitmask)
            if type(bitslice)==type(0):
                # We only want one bit
                bitmask = self.bitmask(1)
                return int((self.data >> bitslice) & bitmask)
            print(bitmask)
        else:
            print('CommonBits: Error: invalid slice range')

    def __setitem__(self, bitslice, value):
        if self.check_slice(bitslice)==0:
            if type(bitslice)==type(slice(1,2,3)):
                # Get a bitmask for the bit range passed via the bitslice
                bitmask = self.bitmask(bitslice.start - bitslice.stop +1)

                if value==-1:
                    # Allow -1 to set range to all ones. Simply use the bitmask as data.
                    data=bitmask
                elif value>=0:
                    data = value
                else:
                    print(("CommonBits: Error: Input data = %d. Only unsigned integers are supported, use to_unsigned(data, bits)." %value))
              
                # Make sure bit length of passed data does not exceed bitmask length
                if self.get_bin_len(data) <= self.get_bin_len(bitmask):
                    self.data = (self.data & ~(bitmask << bitslice.stop)) | (data << bitslice.stop)
                else:
                    print(('CommonBits: Error: passed value (%d) does not fit in bits [%d..%d].' %(value, bitslice.start, bitslice.stop)))

            if type(bitslice)==type(0):
                # We only want to set one bit
                bitmask = self.bitmask(1)
                data=value
                # Make sure bit length of passed data does not exceed bitmask length
                if self.get_bin_len(data) <= self.get_bin_len(bitmask):
                    self.data = (self.data & ~(bitmask << bitslice)) | (data << bitslice)   
                else:
                    print(('CommonBits: Error: passed value (%d) does not fit in bit [%d].' %(value, bitslice)))

        else:
            print('CommonBits: Error: invalid slice range')

    def __repr__(self):
        if self.data_bin_len>1:
            bitslice = slice(self.data_bin_len-1, 0, None)
        else:
            bitslice = 0
        return str(self.__getitem__(bitslice))

    def __len__(self):
        return self.data_bin_len

    def __str__(self):
        return hex(int(self.__repr__()))

    def __hex__(self):
        return hex(int(self.__repr__()))

    def __trunc__(self):
        return int(self.data).__trunc__()

    def __and__(self, other):
        # To concatenate two CommonBits types, first create a new one with the combined length
        ret = CommonBits(0, self.data_bin_len + other.data_bin_len )

        # Now fill in the values. Self is interpreted as the MS part, other as the LS part.
        ms_hi = ret.data_bin_len-1
        ms_lo = other.data_bin_len
        ls_hi = other.data_bin_len-1
        ls_lo = 0 
        ret[ms_hi:ms_lo] = self.data
        ret[ls_hi:ls_lo] = other.data 
        return ret 

    def hi(self):
        data_bits = CommonBits(self.data)
        result = []
        for bit in range(0, self.data_bin_len):
            if data_bits[bit]==1:
                result.append(bit)
        return result

    def lo(self):
        data_bits = CommonBits(self.data)
        result = []
        for bit in range(0, self.data_bin_len):
            if data_bits[bit]==0:
                result.append(bit)
        return result

    def bitmask(self, nof_bits):
        # return a bitmask of nof_bits, e.g. 7 is a bitmask for 3 bits
        return pow(2, nof_bits)-1

    def check_slice(self, bitslice):
        # Check that the user passed a valid slice e.g. [31:24], or 1 integer e.g. [31]
        result = 0
        if type(bitslice)==type(slice(1,2,3)):
            # Slice type passed. Don't allow user to pass step
            if bitslice.step!=None:
                result+=1
                print('CommonBits: Error: no step size allowed')
            # We want user to pass range in [MS:LS] notation
            if bitslice.stop > bitslice.start:
                result+=1
                print('CommonBits: Error: slice range should be [ms:ls]')
            # Do not exceed MSb index
            if bitslice.start>=self.data_bin_len:
                result+=1
                print('CommonBits: Error: Passed MSbit does not exist in data')
        if type(bitslice)==type(0):
            # One integer passed. Only check if the passed bit exists.
            if bitslice>=self.data_bin_len:
                result+=1
                print('CommonBits: Error: Passed MSbit does not exist in data')
        return result

    def get_bin_len(self, value):
        value_bin_str = bin(value)
        # Cut the '0b' from the binary string:
        value_bin = value_bin_str[2:len(value_bin_str)]
        return len(value_bin)

    def reversed(self):
        format_str = '{:0%db}'%self.data_bin_len
        res = int(format_str.format(self.data)[::-1], 2)
        return res

class CommonSymbols(CommonBits):
    """ 
    CommonBits operating on symbol boundaries.
    """
    def __init__(self, data, symbol_w, datasymbols=1):
        if datasymbols>0:
            CommonBits.__init__(self, data, datasymbols*symbol_w)
        else:
            CommonBits.__init__(self, data)
        
        self.symbol_w = symbol_w
        self.data_symbol_len = ceil_div(self.data_bin_len, symbol_w)

    def __getitem__(self, symbolslice):
        # Convert symbol range to bit range, let CommonBits do the rest
        return CommonBits.__getitem__(self, self.symbolslice_to_bitslice(symbolslice))

    def __setitem__(self, symbolslice, value):
        # Convert symbol range to bit range, let CommonBits do the rest
         return CommonBits.__setitem__(self, self.symbolslice_to_bitslice(symbolslice), value)

    def __repr__(self):
        if self.data_symbol_len>1:
            symbolslice = slice(self.data_symbol_len-1, 0, None)
        else:
            symbolslice = 0
        return self.__getitem__(symbolslice)

    def __len__(self):
        return self.data_symbol_len

    def symbolslice_to_bitslice(self, symbolslice):
        if type(symbolslice)==type(slice(1,2,3)):
            MSS = symbolslice.start
            LSS = symbolslice.stop
            bitslice = slice((1+MSS)*self.symbol_w-1, LSS*self.symbol_w, None)
        if type(symbolslice)==type(0):
            MSb = (1+symbolslice)*self.symbol_w
            LSb = (1+symbolslice)*self.symbol_w-self.symbol_w
            bitslice = slice(MSb-1, LSb, None)
        return bitslice


class CommonBytes(CommonSymbols):
    def __init__(self, data, datasymbols=1):
        CommonSymbols.__init__(self, data, 8, datasymbols)

class CommonShorts(CommonSymbols):
    def __init__(self, data, datasymbols=1):
        CommonSymbols.__init__(self, data, 16, datasymbols)

class CommonWords(CommonSymbols):
    def __init__(self, data, datasymbols=1):
        CommonSymbols.__init__(self, data, 32, datasymbols)

class CommonWords64(CommonSymbols):
    def __init__(self, data, datasymbols=1):
        CommonSymbols.__init__(self, data, 64, datasymbols)


