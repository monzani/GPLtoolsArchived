if test "${CMTROOT}" = ""; then
  CMTROOT=/afs/slac/g/glast/applications/CMT/v1r18p20061003; export CMTROOT
fi
. ${CMTROOT}/mgr/setup.sh
tempfile=`${CMTROOT}/mgr/cmt -quiet build temporary_name`
if test ! $? = 0 ; then tempfile=/tmp/cmt.$$; fi
${CMTROOT}/mgr/cmt cleanup -sh -pack=fileOps -version= -path=/afs/slac.stanford.edu/g/glast/ground/releases/volume01/L1Proc/test/1.74/GPLtools/b/GPLtools $* >${tempfile}; . ${tempfile}
/bin/rm -f ${tempfile}

