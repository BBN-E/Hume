
use strict;
use warnings;

# Standard libraries:
use Getopt::Long;
use File::Basename;
use Data::Dumper;

# Runjobs libraries:
use lib ("/d4m/ears/releases/Cube2/R2016_02_12/" .
    "install-optimize$ENV{ARCH_SUFFIX}/perl_lib");
use runjobs4;
use File::PathConvert;
use Parameters;
use PerlUtils;
use RunJobsUtils;

# Package declaration:
package main;

our ($exp_root, $exp) = startjobs();
my $expts = "$exp_root/expts";

max_jobs(400,);

my $paramFile = $ARGV[0];
print "Got param file $paramFile\n";
my $params = Parameters::loadAndPrint($paramFile);

defined($params) or die "Could not load params";

my $exptName = $params->get('exptName');
my $dir_prefix = $params->get('dir.prefix');
my $dir_suffix = $params->get('dir.suffix');
my $outdir = $params->get('outdir');
my $script = $params->get('script');
my $cmd_script = $params->get('cmd_script');


for(my $i=0; $i<=399; $i++) {
  my $chunk = "chunk-".$i;
  my $indir = "$dir_prefix/$chunk/$dir_suffix";
  my $outdir = "$outdir/$chunk";

  if(!-e $outdir) {
    my $cmd = "mkdir $outdir";
    `$cmd`;
  }

  my $cmd = "python $script $indir $outdir";

  my $job = runjobs4::runjobs([], "$exptName/$chunk", { BATCH_QUEUE => $params->get("batchQueue") }, ["perl $cmd_script $cmd"]);
}

endjobs();



