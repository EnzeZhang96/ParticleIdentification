
ifndef ATMPD_ROOT
	ATMPD_ROOT = ../../
endif

include $(ATMPD_ROOT)/config.gmk


LOCAL_INC	=  -I. -I$(INCDIR) -I$(FORTRAN_INCDIR)

LOCAL_LIBS	= $(APLIB) $(OBJS)

#
#  necessary ATMPD libraries
#

APLIB =  -lapdrlib -lpolfit -laplib -lringlib  -ltp -ltf  -lringlib  \
	 -laplib -lmsfit -lmslib -lseplib -lmsfit -lprtlib -lmuelib \
	 -lffit -lodlib -lstmu -laplowe -lpolfit -lexpq  -laplib -lska -lneutflux \
	 -lThreeProb -lfiTQun

#
#  Objects
#

ROOTLIBS     := $(shell root-config --glibs) -lTreePlayer -lMinuit

OBJS = 

EXEC_FILES = getqtinfo 

#
#  Rules for building library 
#

.PHONY:  

all: exec

getqtinfo: getqtinfo.o $(OBJS)
        LD_RUN_PATH=$(LIBDIR):$(SKOFL_LIBDIR) $(CXX) $(CXXFLAGS) -o $@ $@.o $(OBJS) $(LDLIBS)

lib: ${OBJS}

exec: $(EXEC_FILES)

clean:
	$(RM) -f *.o *.a *~ $(EXEC_FILES)

