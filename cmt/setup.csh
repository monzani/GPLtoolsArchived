# echo "Setting GPLtools v1r12 in /a/surrey01/vol/vol2/g.svac/focke/L1/gpl"

if ( $?CMTROOT == 0 ) then
  setenv CMTROOT /afs/slac/g/glast/applications/CMT/v1r18p20061003
endif
source ${CMTROOT}/mgr/setup.csh

set tempfile=`${CMTROOT}/mgr/cmt -quiet build temporary_name`
if $status != 0 then
  set tempfile=/tmp/cmt.$$
endif
${CMTROOT}/mgr/cmt setup -csh -pack=GPLtools -version=v1r12 -path=/a/surrey01/vol/vol2/g.svac/focke/L1/gpl  -no_cleanup $* >${tempfile}; source ${tempfile}
/bin/rm -f ${tempfile}

