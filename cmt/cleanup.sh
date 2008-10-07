if test "${CMTROOT}" = ""; then
  CMTROOT=/afs/slac/g/glast/applications/CMT/v1r18p20061003; export CMTROOT
fi
. ${CMTROOT}/mgr/setup.sh
tempfile=`${CMTROOT}/mgr/cmt -quiet build temporary_name`
if test ! $? = 0 ; then tempfile=/tmp/cmt.$$; fi
${CMTROOT}/mgr/cmt cleanup -sh -pack=GPLtools -version=v1r13 -path=/a/surrey01/vol/vol2/g.svac/focke/L1 $* >${tempfile}; . ${tempfile}
/bin/rm -f ${tempfile}

