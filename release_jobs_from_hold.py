#!/usr/bin/env perl
use strict;
use Getopt::Long;


my $usage    = "\t\t --usage $0 job_id=<PBS JOB ID> min=<Start of array> max=<End of array>\n";
my $job_id;
my $min;
my $max;
$\= "\n";



if (! scalar(@ARGV)  ) {
        die $usage;
}

GetOptions ("job_id=i"  => \$job_id,
              "min=i"   => \$min,
              "max=i"   => \$max)   ;

if(! $job_id || ! $min || ! $max){
        die $usage;
}


print "job=$job_id min=$min max=$max\n";


for(my $i = $min; $i <= $max; $i++){
        my $call = 'releasehold -a "' . $job_id .  '\[' . $i . '\]"';
        print $call;
        system($call);
}
