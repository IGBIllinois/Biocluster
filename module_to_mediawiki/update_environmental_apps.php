#!/usr/bin/env php
<?php

require_once 'libs/functions.inc.php';
require_once 'config.inc.php';

$sapi_type = php_sapi_name();
if ($sapi_type != 'cli') {
        echo "Error: This script can only be run from the command line.\n";
	exit;
}

//Command to get module list
$command = "source /etc/profile.d/modules.sh; module -t whatis 2>&1";
$result = exec($command,$output,$sterr);
//Sorts it alphabetically
natcasesort($output);
$previous_app = array();
$previous_app_index = 0;

//Format output into array
$formatted_output = array();
foreach ($output as $row) {
	
		$colon_pos = strpos($row,":");
		$whatis = substr($row,$colon_pos+1);
		$app_version = substr($row,0,$colon_pos);
		$homepage_pos = strpos($whatis,'Homepage: ');
		$homepage = "";
		if ($homepage_pos) {
			$homepage = substr($whatis,$homepage_pos+9);
			$whatis = substr($whatis,0,$homepage_pos);
		}
		
		if (substr_count($app_version,"/") == 1) {
			$second_explode = explode("/",$app_version);
			$app_name = $second_explode[0];
			$version = $second_explode[1];
			$formatted_row = array('app'=>trim(rtrim($app_name)),
					'version'=>trim(rtrim($version)),
					'whatis'=>trim(rtrim($whatis)),
					'homepage'=>trim(rtrim($homepage))
					);
		
			if (!in_array($formatted_row['app'],$ignore_apps)) {
				array_push($formatted_output,$formatted_row);
			}
		}
}
$previous_app_index = 0;
$count = count($formatted_output);
for ($i=0;$i<$count;$i++) {
	if (($i != 0) && ($formatted_output[$i]['app'] == $formatted_output[$previous_app_index]['app'])) {
		$formatted_output[$i]['version'] = $formatted_output[$previous_app_index]['version'] . ", " . $formatted_output[$i]['version'];
		unset($formatted_output[$previous_app_index]);
	}
	$previous_app_index = $i;
}
$formatted_output = array_values($formatted_output);

//Creates table header
$wiki_output = "{| style='width: 900px;  margin: 0 auto' class='wikitable' border='1' cellpadding='1' cellspacing='1'\n";
$wiki_output .= "|-\n";
$wiki_output .= "!Application\n";
$wiki_output .= "!Installed Versions\n";
$wiki_output .= "!Description\n";
//Populates table
foreach ($formatted_output as $row) {
	$wiki_output .= "|-\n";
	if ($row['homepage'] != "") {
		$wiki_output .= "|[" . $row['homepage'] . " " . $row['app'] . "]\n";
	}
	else {
		$wiki_output .= "|" . $row['app'] . "\n";
	}
	$wiki_output .= "|" . $row['version'] . "\n";
	$wiki_output .= "|" . $row['whatis'] . "\n";
}

$wiki_output .= "|}";

$cookie_file = tempnam("/tmp/", "CURLCOOKIE");
//Login to wiki
$token = wiki_login($wiki_api,$wiki_user,$wiki_password,$wiki_domain,$cookie_file);
if ($token) {
	//Send wiki table to page
	wiki_edit_page($wiki_api,$wiki_page,$wiki_output,$cookie_file);

}
?>

