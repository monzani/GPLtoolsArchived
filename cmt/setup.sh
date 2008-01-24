# echo "Setting GPLtools v1r1 in /afs/slac.stanford.edu/g/glast/ground/PipelineConfig/GPLtools"

if test "${CMTROOT}" = ""; then
  CMTROOT=/afs/slac.stanford.edu/g/glast/applications/CMT/v1r16p20040701; export CMTROOT
fi
. ${CMTROOT}/mgr/setup.sh

tempfile=`${CMTROOT}/mgr/cmt build temporary_name -quiet`
if test ! $? = 0 ; then tempfile=/tmp/cmt.$$; fi
${CMTROOT}/mgr/cmt -quiet setup -sh -pack=GPLtools -version=v1r1 -path=/afs/slac.stanford.edu/g/glast/ground/PipelineConfig/GPLtools  $* >${tempfile}; . ${tempfile}
/bin/rm -f ${tempfile}

