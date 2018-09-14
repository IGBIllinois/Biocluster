<?php
error_reporting(E_ALL);
ini_set('display_errors', '1');

require_once 'libs/functions.inc.php';
require_once 'config.inc.php';

$sapi_type = php_sapi_name();
if ($sapi_type != 'cli') {
        log_alert("Error: This script can only be run from the command line.");
	exit;
}

$module_dirs = explode(" ",__MODULE_DIRS__);
$apps = array();
foreach ($module_dirs as $dir) {
	$result = get_lmod_apps($dir);
	if (is_array($result)) {
		$apps = array_merge($apps,$result);
		log_alert("Parsing directory " . $dir);
	}
	else {
		log_alert("Error: Unable to parse apps in " . $dir);
	}
}
asort($apps);
//Format output into array
$formatted_output = array();
foreach ($apps as $row) {

		//Crazy php array manipulation to get homepage	
		$help_array = explode("\n",$row['versions'][0]['help']);
		$homepage_array = array_values(preg_grep("/Homepage:/",$help_array));
		$homepage = "";
		if (count($homepage_array)) {
			$homepage = trim(rtrim(substr($homepage_array[0],strpos($homepage_array[0],":")+2)));
			if (!filter_var($homepage,FILTER_VALIDATE_URL)) {
				log_alert("Error: Invalid homepage for " . $row['package']);
				$homeage = "";
			}
		}

		//Get Versions
		$versions_array = array();
		foreach ($row['versions'] as $version_row) {
			$format_version = substr($version_row['full'],strpos($version_row['full'],"/")+1);
			array_push($versions_array,$format_version);
		}
		asort($versions_array);
		$versions = implode("<br>",$versions_array);

		$description = "";
		if (isset($row['description'])) {
			$description = str_replace("\n","",$row['description']);
		}
		else {
			log_alert("Error: No Description set for " . $row['package']);
		}
		//formatted array of applications
		$formatted_row = array('app'=>$row['package'],
					'version'=>$versions,
					'whatis'=>$description,
					'homepage'=>$homepage
					);
		array_push($formatted_output,$formatted_row);
}

//Creates table header
$wiki_output = "{| style='margin: 0 auto' class='wikitable' border='1' cellpadding='1' cellspacing='1'\n";
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

$token = wiki_login(__WIKI_API__,__WIKI_USER__,__WIKI_PASSWORD__,__WIKI_DOMAIN__,$cookie_file);
log_alert("Mediawiki Token: " . $token);
if ($token) {
	//Send wiki table to page
	$result = wiki_edit_page(__WIKI_API__,__WIKI_PAGE__,$wiki_output,$cookie_file);
	$full_url = substr(__WIKI_API__,0,strpos(__WIKI_API__,"/api.php")) . "/" . __WIKI_PAGE__;
	if (!$result) {
		log_alert("Error: Failed updating mediaiwki page " . $full_url);
	}
	else {
		log_alert("Success: " . $full_url . " successfully updated");
		log_alert("Total Applications: " . count($apps));
	}

}
else {
	log_alert("ERROR: Failed login to mediawiki");

}

?>

