# echo "Setting fileOps  in /a/surrey01/vol/vol2/g.svac/focke/L1/GPLtools/GPLtools"

if test "${CMTROOT}" = ""; then
  CMTROOT=/afs/slac/g/glast/applications/CMT/v1r18p20061003; export CMTROOT
fi
. ${CMTROOT}/mgr/setup.sh

tempfile=`${CMTROOT}/mgr/cmt -quiet build temporary_name`
if test ! $? = 0 ; then tempfile=/tmp/cmt.$$; fi
${CMTROOT}/mgr/cmt setup -sh -pack=fileOps -version= -path=/a/surrey01/vol/vol2/g.svac/focke/L1/GPLtools/GPLtools  -no_cleanup $* >${tempfile}; . ${tempfile}
/bin/rm -f ${tempfile}

