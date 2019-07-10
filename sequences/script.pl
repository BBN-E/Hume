$ENV{SVN_PROJECT_ROOT}='/nfs/mercury-04/u22/Active/Projects';

$cmd = "";
for(my $i=0; $i<=$#ARGV; $i++) {
  if($i > 0) {
    $cmd .= " ";
  }
  $cmd .= $ARGV[$i];

  `$cmd`;
}


