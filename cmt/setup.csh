# echo "Setting GPLtools v0r15 in /a/surrey01/vol/vol2/g.svac/focke/builds"

if ( $?CMTROOT == 0 ) then
  setenv CMTROOT /afs/slac.stanford.edu/g/glast/applications/CMT/v1r16p20040701
endif
source ${CMTROOT}/mgr/setup.csh

set tempfile=`${CMTROOT}/mgr/cmt build temporary_name -quiet`
if $status != 0 then
  set tempfile=/tmp/cmt.$$
endif
${CMTROOT}/mgr/cmt -quiet setup -csh -pack=GPLtools -version=v0r15 -path=/a/surrey01/vol/vol2/g.svac/focke/builds  $* >${tempfile}; source ${tempfile}
/bin/rm -f ${tempfile}

