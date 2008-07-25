# echo "Setting GPLtools v1r10 in /home/focke/cvs"

if test "${CMTROOT}" = ""; then
  CMTROOT=/afs/slac/g/glast/applications/CMT/v1r18p20061003; export CMTROOT
fi
. ${CMTROOT}/mgr/setup.sh

tempfile=`${CMTROOT}/mgr/cmt -quiet build temporary_name`
if test ! $? = 0 ; then tempfile=/tmp/cmt.$$; fi
${CMTROOT}/mgr/cmt setup -sh -pack=GPLtools -version=v1r10 -path=/home/focke/cvs  -no_cleanup $* >${tempfile}; . ${tempfile}
/bin/rm -f ${tempfile}

